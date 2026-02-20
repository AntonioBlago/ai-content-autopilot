"""
Flask Blueprint for receiving Visibly Content Autopilot webhooks.

Depends on: flask, .client, .security
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from flask import Blueprint, jsonify, request

from .client import VisiblyClient
from .security import verify_webhook_signature

logger = logging.getLogger(__name__)

# =====================================================================
# Configuration (set via configure_visibly())
# =====================================================================

_config = {
    'webhook_secret': None,
    'api_key': None,
    'base_url': 'https://www.antonioblago.com/content-autopilot',
    'on_article_received': None,
}


def configure_visibly(
    webhook_secret: str,
    api_key: str,
    base_url: str = 'https://www.antonioblago.com/content-autopilot',
    on_article_received: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> None:
    """
    Configure the Visibly integration.

    Args:
        webhook_secret: HMAC-SHA256 secret for verifying webhook signatures
        api_key: API key for Pull API authentication (Bearer token)
        base_url: Visibly Content Autopilot base URL
        on_article_received: Callback function called when webhook delivers an article.
            Receives a dict with article data, returns True on success.
    """
    _config['webhook_secret'] = webhook_secret
    _config['api_key'] = api_key
    _config['base_url'] = base_url.rstrip('/')
    _config['on_article_received'] = on_article_received


# =====================================================================
# Webhook Receiver Blueprint
# =====================================================================

contentpilot_webhook_bp = Blueprint('contentpilot_webhook', __name__)


@contentpilot_webhook_bp.route('/webhooks/visibly', methods=['POST'])
def receive_visibly_webhook():
    """
    Receive and process Visibly Content Autopilot webhooks.

    1. Verify HMAC-SHA256 signature
    2. Parse payload
    3. Fetch full article via Pull API
    4. Call on_article_received callback
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

    # Fetch full article via Pull API
    api_key = _config.get('api_key')
    if not api_key:
        logger.error("API key not configured. Call configure_visibly() first.")
        return jsonify({'error': 'API key not configured'}), 500

    client = VisiblyClient(api_key=api_key, base_url=_config['base_url'])
    article = client.fetch_article(article_id, include_markdown=True)

    if not article:
        logger.warning(f"Could not fetch article {article_id} via Pull API")
        return jsonify({'error': 'Failed to fetch article'}), 502

    # Inject webhook metadata into article dict
    article['_webhook_event'] = event
    article['_webhook_timestamp'] = payload.get('timestamp')
    article['_scheduled_date'] = payload.get('scheduled_date')

    # Call handler
    handler = _config.get('on_article_received')
    if handler:
        try:
            success = handler(article)
            if success:
                logger.info(f"Article {article_id} processed successfully")
                return jsonify({'success': True, 'article_id': article_id})
            else:
                logger.warning(f"Handler returned False for article {article_id}")
                return jsonify({'success': False, 'error': 'Handler rejected article'}), 422
        except Exception as e:
            logger.error(f"Handler error for article {article_id}: {e}")
            return jsonify({'error': 'Handler error'}), 500
    else:
        # No handler configured - use default
        success = default_flask_blog_handler(article)
        return jsonify({'success': success, 'article_id': article_id})


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

        logger.info(f"Saved article to {filepath}")
        return True

    except Exception as e:
        logger.error(f"default_flask_blog_handler error: {e}")
        return False