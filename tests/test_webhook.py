"""Tests for webhook Blueprint, configure_visibly, and default handler."""

import hashlib
import hmac
import json
import os

import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

from ai_content_autopilot.webhook import (
    _config,
    configure_visibly,
    contentpilot_webhook_bp,
    default_flask_blog_handler,
)


def _make_signature(payload: bytes, secret: str) -> str:
    """Compute a valid sha256=... signature."""
    mac = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


@pytest.fixture
def app():
    """Create a Flask app with the webhook blueprint registered."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(contentpilot_webhook_bp)
    return app


@pytest.fixture
def flask_client(app):
    """Flask test client."""
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_config():
    """Reset _config before each test."""
    original = dict(_config)
    yield
    _config.update(original)


class TestConfigureVisibly:
    """Test configure_visibly function."""

    def test_sets_all_values(self):
        handler = lambda a: True
        configure_visibly(
            webhook_secret='sec',
            api_key='key',
            base_url='https://example.com/',
            on_article_received=handler,
        )
        assert _config['webhook_secret'] == 'sec'
        assert _config['api_key'] == 'key'
        assert _config['base_url'] == 'https://example.com'
        assert _config['on_article_received'] is handler

    def test_strips_trailing_slash(self):
        configure_visibly(webhook_secret='s', api_key='k', base_url='https://x.com///')
        assert _config['base_url'] == 'https://x.com'

    def test_default_base_url(self):
        configure_visibly(webhook_secret='s', api_key='k')
        assert _config['base_url'] == 'https://www.antonioblago.com/content-autopilot'


class TestWebhookEndpoint:
    """Test POST /webhooks/visibly endpoint."""

    def test_no_secret_configured_returns_500(self, flask_client):
        """Unconfigured webhook returns 500."""
        _config['webhook_secret'] = None
        r = flask_client.post('/webhooks/visibly', data=b'{}')
        assert r.status_code == 500

    def test_invalid_signature_returns_401(self, flask_client):
        """Bad HMAC returns 401."""
        _config['webhook_secret'] = 'secret'
        r = flask_client.post(
            '/webhooks/visibly',
            data=b'{}',
            headers={'X-Webhook-Signature': 'sha256=invalid'},
        )
        assert r.status_code == 401

    def test_missing_signature_returns_401(self, flask_client):
        """Missing signature header returns 401."""
        _config['webhook_secret'] = 'secret'
        r = flask_client.post('/webhooks/visibly', data=b'{}')
        assert r.status_code == 401

    def test_invalid_json_returns_400(self, flask_client):
        """Malformed JSON returns 400."""
        _config['webhook_secret'] = 'secret'
        payload = b'not json'
        sig = _make_signature(payload, 'secret')
        r = flask_client.post(
            '/webhooks/visibly',
            data=payload,
            headers={'X-Webhook-Signature': sig},
        )
        assert r.status_code == 400

    def test_no_api_key_returns_500(self, flask_client):
        """No API key configured returns 500."""
        _config['webhook_secret'] = 'secret'
        _config['api_key'] = None
        payload = json.dumps({'event': 'article.approved', 'article_id': 1}).encode()
        sig = _make_signature(payload, 'secret')
        r = flask_client.post(
            '/webhooks/visibly',
            data=payload,
            headers={'X-Webhook-Signature': sig},
        )
        assert r.status_code == 500

    @patch('ai_content_autopilot.webhook.VisiblyClient')
    def test_fetch_failure_returns_502(self, mock_cls, flask_client):
        """Failed article fetch returns 502."""
        _config['webhook_secret'] = 'secret'
        _config['api_key'] = 'key'
        mock_cls.return_value.fetch_article.return_value = None

        payload = json.dumps({'event': 'article.approved', 'article_id': 1}).encode()
        sig = _make_signature(payload, 'secret')
        r = flask_client.post(
            '/webhooks/visibly',
            data=payload,
            headers={'X-Webhook-Signature': sig},
        )
        assert r.status_code == 502

    @patch('ai_content_autopilot.webhook.VisiblyClient')
    def test_handler_called_on_success(self, mock_cls, flask_client):
        """Custom handler is called with article data."""
        handler = MagicMock(return_value=True)
        _config['webhook_secret'] = 'secret'
        _config['api_key'] = 'key'
        _config['on_article_received'] = handler
        mock_cls.return_value.fetch_article.return_value = {
            'id': 42, 'title': 'Test',
        }

        payload = json.dumps({
            'event': 'article.approved',
            'article_id': 42,
            'timestamp': '2026-02-20T10:00:00Z',
            'scheduled_date': '2026-03-01T09:00:00',
        }).encode()
        sig = _make_signature(payload, 'secret')
        r = flask_client.post(
            '/webhooks/visibly',
            data=payload,
            headers={'X-Webhook-Signature': sig},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True

        # Handler should have been called once
        handler.assert_called_once()
        article_arg = handler.call_args[0][0]
        assert article_arg['id'] == 42
        assert article_arg['_webhook_event'] == 'article.approved'
        assert article_arg['_scheduled_date'] == '2026-03-01T09:00:00'

    @patch('ai_content_autopilot.webhook.VisiblyClient')
    def test_handler_returns_false_gives_422(self, mock_cls, flask_client):
        """Handler returning False gives 422."""
        _config['webhook_secret'] = 'secret'
        _config['api_key'] = 'key'
        _config['on_article_received'] = lambda a: False
        mock_cls.return_value.fetch_article.return_value = {'id': 1}

        payload = json.dumps({'event': 'article.approved', 'article_id': 1}).encode()
        sig = _make_signature(payload, 'secret')
        r = flask_client.post(
            '/webhooks/visibly',
            data=payload,
            headers={'X-Webhook-Signature': sig},
        )
        assert r.status_code == 422

    @patch('ai_content_autopilot.webhook.VisiblyClient')
    def test_handler_exception_gives_500(self, mock_cls, flask_client):
        """Handler raising exception gives 500."""
        def bad_handler(a):
            raise RuntimeError("boom")

        _config['webhook_secret'] = 'secret'
        _config['api_key'] = 'key'
        _config['on_article_received'] = bad_handler
        mock_cls.return_value.fetch_article.return_value = {'id': 1}

        payload = json.dumps({'event': 'article.approved', 'article_id': 1}).encode()
        sig = _make_signature(payload, 'secret')
        r = flask_client.post(
            '/webhooks/visibly',
            data=payload,
            headers={'X-Webhook-Signature': sig},
        )
        assert r.status_code == 500


class TestDefaultHandler:
    """Test default_flask_blog_handler."""

    def test_saves_json_file(self, tmp_path):
        """Should create a JSON file with article data."""
        with patch('ai_content_autopilot.webhook.os.getcwd', return_value=str(tmp_path)):
            article = {
                'id': 42,
                'title': 'Test Article',
                'slug': 'test-article',
                'meta_description': 'Desc',
                'content_html': '<p>Hi</p>',
                'content_markdown': '# Hi',
                'keywords': ['seo'],
                'seo_score': 85,
                'word_count': 500,
                '_scheduled_date': '2026-03-01',
                '_webhook_event': 'article.approved',
            }
            result = default_flask_blog_handler(article)

        assert result is True
        output_file = tmp_path / 'content_output' / 'test-article_visibly.json'
        assert output_file.exists()

        data = json.loads(output_file.read_text(encoding='utf-8'))
        assert data['id'] == 42
        assert data['title'] == 'Test Article'
        assert data['scheduled_date'] == '2026-03-01'
        assert data['keywords'] == ['seo']

    def test_fallback_slug(self, tmp_path):
        """Missing slug should use article-{id} fallback."""
        with patch('ai_content_autopilot.webhook.os.getcwd', return_value=str(tmp_path)):
            article = {'id': 99, 'slug': None}
            result = default_flask_blog_handler(article)

        assert result is True
        output_file = tmp_path / 'content_output' / 'article-99_visibly.json'
        assert output_file.exists()
