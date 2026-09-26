"""
Flask Blueprint for receiving Visibly Content Autopilot webhooks.

Depends on: flask, .client, .security

Design note: a webhook is a signal, not a job with a return value
--------------------------------------------------------------------
Visibly waits 10 seconds for your response and treats a read timeout as
"delivered, outcome unknown". Since that release it does NOT retry on a read
timeout, because the request had already reached you and a second delivery
would make you do the same work twice.

Up to v1.0.2 this blueprint fetched the article and ran your handler inside
the request, so a slow handler produced exactly that timeout. Measured in
production on 2026-09-14: three delivery attempts for one article turned into
three LLM translation runs on the receiving CMS.

The blueprint therefore acknowledges first (HTTP 202) and does the work in a
background thread. Pass ``background=False`` to ``configure_visibly()`` if you
need the old, synchronous behaviour (tests, or a handler you know is fast).
"""

import json
import logging
import os
import threading
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from flask import Blueprint, current_app, jsonify, request

from .client import DEFAULT_BASE_URL, VisiblyClient
from .security import verify_webhook_signature

logger = logging.getLogger(__name__)

# =====================================================================
# Configuration (set via configure_visibly())
# =====================================================================

_config = {
    'webhook_secret': None,
    'api_key': None,
    'base_url': DEFAULT_BASE_URL,
    'on_article_received': None,
    'background': True,
}

# Articles currently being processed, so a repeated delivery does not run the
# same work twice. Process-local: with multiple web workers you need a claim
# column in your own database. It covers the realistic cases (a user clicking
# twice, a sender retrying) at no cost.
_in_flight: set = set()
_in_flight_lock = threading.Lock()


def configure_visibly(
    webhook_secret: str,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    on_article_received: Optional[Callable[[Dict[str, Any]], bool]] = None,
    background: bool = True,
) -> None:
    """
    Configure the Visibly integration.

    Args:
        webhook_secret: HMAC-SHA256 secret for verifying webhook signatures
        api_key: API key for Pull API authentication (Bearer token)
        base_url: Visibly base URL. Defaults to the production host.
        on_article_received: Callback function called when webhook delivers an article.
            Receives a dict with article data, returns True on success.
        background: Acknowledge with HTTP 202 and run the fetch + handler in a
            background thread (default). Set to False only if your handler
            finishes well inside Visibly's 10 second delivery timeout.
    """
    _config['webhook_secret'] = webhook_secret
    _config['api_key'] = api_key
    _config['base_url'] = base_url.rstrip('/')
    _config['on_article_received'] = on_article_received
    _config['background'] = background


# =====================================================================
# Processing
# =====================================================================

def _claim(article_id: Any) -> bool:
    """True if this run may process the article (nobody else is on it)."""
    with _in_flight_lock:
        if article_id in _in_flight:
            return False
        _in_flight.add(article_id)
        return True


def _release(article_id: Any) -> None:
    with _in_flight_lock:
        _in_flight.discard(article_id)


def _fetch_and_dispatch(event: str, article_id: Any, payload: Dict[str, Any]) -> str:
    """Pull the article and hand it to the configured handler.

    Returns ``'ok'``, ``'fetch_failed'`` or ``'rejected'``. The three are kept
    apart because they mean different things to a sender: a failed fetch is
    usually transient and worth retrying, a rejected article is not.
    """
    client = VisiblyClient(api_key=_config['api_key'], base_url=_config['base_url'])
    article = client.fetch_article(article_id, include_markdown=True)
    if not article:
        logger.warning(f"Could not fetch article {article_id} via Pull API")
        return 'fetch_failed'

    # Inject webhook metadata into article dict
    article['_webhook_event'] = event
    article['_webhook_timestamp'] = payload.get('timestamp')
    article['_scheduled_date'] = payload.get('scheduled_date')
    article['_published_url'] = payload.get('published_url')
    article['_revision'] = payload.get('revision')

    handler = _config.get('on_article_received') or default_flask_blog_handler
    if handler(article):
        logger.info(f"Article {article_id} processed successfully")
        return 'ok'
    logger.warning(f"Handler returned False for article {article_id}")
    return 'rejected'


def _process_in_background(app, event: str, article_id: Any, payload: Dict[str, Any]) -> None:
    with app.app_context():
        try:
            _fetch_and_dispatch(event, article_id, payload)
        except Exception as e:
            logger.error(f"Handler error for article {article_id}: {e}", exc_info=True)
        finally:
            _release(article_id)


# =====================================================================
# Webhook Receiver Blueprint
# =====================================================================

#: Events that carry an article worth pulling. Everything else is either a
#: connection test or a notification - see docs/CONTRACT.md.
ARTICLE_EVENTS = ('article.approved', 'article.updated', 'article.published')

contentpilot_webhook_bp = Blueprint('contentpilot_webhook', __name__)


@contentpilot_webhook_bp.route('/webhooks/visibly', methods=['POST'])
def receive_visibly_webhook():
    """
    Receive and process Visibly Content Autopilot webhooks.

    1. Verify HMAC-SHA256 signature
    2. Parse payload
    3. Acknowledge with 202 and fetch + dispatch in the background
       (or synchronously when ``background=False``)
    """
    secret = _config.get('webhook_secret')
    if not secret:
        logger.error("Webhook secret not configured. Call configure_visibly() first.")
        return jsonify({'error': 'Webhook not configured'}), 500

    # Get raw body and signature
    payload_bytes = request.get_data()
    signature = request.headers.get('X-Webhook-Signature', '')

    # Verify signature
    if not verify_webhook_signature(payload_bytes, secret, signature):
        logger.warning("Webhook signature verification failed")
        return jsonify({'error': 'Invalid signature'}), 401

    # Parse payload
    try:
        payload = json.loads(payload_bytes)
    except (json.JSONDecodeError, TypeError):
        return jsonify({'error': 'Invalid JSON'}), 400

    event = payload.get('event', '')
    article_id = payload.get('article_id')

    logger.info(f"Received webhook: event={event}, article_id={article_id}")

    # "Test connection" in Visibly. There is no article behind it, so there is
    # nothing to pull. Answering deliberately also keeps the synchronous path
    # from reporting 502 for a connector that is configured correctly.
    if event == 'webhook.test':
        return jsonify({'status': 'ok', 'event': event}), 200

    # article.failed and anything unknown: acknowledge, do not fetch. The
    # contract asks for a log line, and an error would only invite retries
    # that change nothing.
    if not article_id or event not in ARTICLE_EVENTS:
        logger.info(f"Ignoring event {event!r} (article_id={article_id})")
        return jsonify({'status': 'ignored', 'event': event}), 200

    if not _config.get('api_key'):
        logger.error("API key not configured. Call configure_visibly() first.")
        return jsonify({'error': 'API key not configured'}), 500

    if not _config.get('background'):
        # Synchronous path: only safe for handlers that finish inside 10s.
        try:
            status = _fetch_and_dispatch(event, article_id, payload)
        except Exception as e:
            logger.error(f"Handler error for article {article_id}: {e}", exc_info=True)
            return jsonify({'error': 'Handler error'}), 500
        if status == 'fetch_failed':
            return jsonify({'error': 'Failed to fetch article'}), 502
        if status == 'rejected':
            return jsonify({'success': False, 'article_id': article_id}), 422
        return jsonify({'success': True, 'article_id': article_id})

    if not _claim(article_id):
        logger.info(f"Article {article_id} is already being processed, skipping duplicate")
        return jsonify({'status': 'already_processing', 'article_id': article_id}), 202

    app = current_app._get_current_object()
    threading.Thread(
        target=_process_in_background,
        args=(app, event, article_id, payload),
        daemon=True,
        name=f"visibly-webhook-{article_id}",
    ).start()
    return jsonify({'status': 'accepted', 'article_id': article_id}), 202


# =====================================================================
# Default Handler
# =====================================================================

def default_flask_blog_handler(article: Dict[str, Any]) -> bool:
    """
    Default handler: save article as JSON to ./content_output/.

    Creates a JSON file with the article data including scheduled_date
    for later processing by a CMS or static site generator.

    Args:
        article: Article dict from Pull API

    Returns:
        True if saved successfully
    """
    try:
        output_dir = os.path.join(os.getcwd(), 'content_output')
        os.makedirs(output_dir, exist_ok=True)

        slug = article.get('slug') or f"article-{article.get('id', 'unknown')}"
        filename = f"{slug}_visibly.json"
        filepath = os.path.join(output_dir, filename)

        output = {
            'id': article.get('id'),
            'title': article.get('title', ''),
            'slug': slug,
            'meta_description': article.get('meta_description', ''),
            'content_html': article.get('content_html', ''),
            'content_markdown': article.get('content_markdown', ''),
            'keywords': article.get('keywords', []),
            'scheduled_date': article.get('_scheduled_date') or article.get('scheduled_date'),
            'seo_score': article.get('seo_score', 0),
            'word_count': article.get('word_count', 0),
            'received_at': datetime.utcnow().isoformat(),
            'webhook_event': article.get('_webhook_event', ''),
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info(f"Article saved to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save article: {e}")
        return False
