"""Tests for VisiblyClient Pull API client."""

import pytest
from unittest.mock import patch, MagicMock

from ai_content_autopilot.client import VisiblyClient


@pytest.fixture
def client():
    """Create a VisiblyClient instance for testing."""
    return VisiblyClient(
        api_key='sk_live_test123',
        base_url='https://example.com/content-autopilot',
        timeout=10,
    )


class TestVisiblyClientInit:
    """Test client initialization."""

    def test_default_base_url(self):
        c = VisiblyClient(api_key='key')
        assert c.base_url == 'https://www.antonioblago.com/content-autopilot'

    def test_trailing_slash_stripped(self):
        c = VisiblyClient(api_key='key', base_url='https://example.com/')
        assert c.base_url == 'https://example.com'

    def test_default_timeout(self):
        c = VisiblyClient(api_key='key')
        assert c.timeout == 30

    def test_headers_contain_bearer(self, client):
        headers = client._headers()
        assert headers['Authorization'] == 'Bearer sk_live_test123'
        assert 'User-Agent' in headers


class TestFetchArticle:
    """Test fetch_article method."""

    @patch('ai_content_autopilot.client.requests.get')
    def test_fetch_success(self, mock_get, client):
        """Successful fetch returns article dict."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'article': {
                'id': 42,
                'title': 'Test Article',
                'content_html': '<p>Content</p>',
            }
        }
        mock_get.return_value = mock_resp

        result = client.fetch_article(42)
        assert result is not None
        assert result['id'] == 42
        assert result['title'] == 'Test Article'

    @patch('ai_content_autopilot.client.requests.get')
    def test_fetch_includes_markdown_param(self, mock_get, client):
        """include_markdown=True should pass query param."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'article': {'id': 1}}
        mock_get.return_value = mock_resp

        client.fetch_article(1, include_markdown=True)
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs['params']['include_markdown'] == 'true'

    @patch('ai_content_autopilot.client.requests.get')
    def test_fetch_without_markdown(self, mock_get, client):
        """include_markdown=False should not pass query param."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'article': {'id': 1}}
        mock_get.return_value = mock_resp

        client.fetch_article(1, include_markdown=False)
        call_kwargs = mock_get.call_args
        assert 'include_markdown' not in call_kwargs.kwargs['params']

    @patch('ai_content_autopilot.client.requests.get')
    def test_fetch_404_returns_none(self, mock_get, client):
        """404 response returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        assert client.fetch_article(999) is None

    @patch('ai_content_autopilot.client.requests.get')
    def test_fetch_network_error_returns_none(self, mock_get, client):
        """Network error returns None."""
        mock_get.side_effect = ConnectionError("Network down")
        assert client.fetch_article(1) is None

    @patch('ai_content_autopilot.client.requests.get')
    def test_fetch_timeout_returns_none(self, mock_get, client):
        """Timeout returns None."""
        mock_get.side_effect = TimeoutError("Timed out")
        assert client.fetch_article(1) is None


class TestListArticles:
    """Test list_articles method."""

    @patch('ai_content_autopilot.client.requests.get')
    def test_list_success(self, mock_get, client):
        """Successful list returns article list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'articles': [
                {'id': 1, 'title': 'First'},
                {'id': 2, 'title': 'Second'},
            ]
        }
        mock_get.return_value = mock_resp

        result = client.list_articles()
        assert len(result) == 2
        assert result[0]['id'] == 1

    @patch('ai_content_autopilot.client.requests.get')
    def test_list_with_filters(self, mock_get, client):
        """Filters should be passed as query params."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'articles': []}
        mock_get.return_value = mock_resp

        client.list_articles(status='published', project_id=5, limit=10, offset=20)
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs['params']
        assert params['status'] == 'published'
        assert params['project_id'] == 5
        assert params['limit'] == 10
        assert params['offset'] == 20

    @patch('ai_content_autopilot.client.requests.get')
    def test_list_server_error_returns_empty(self, mock_get, client):
        """500 response returns empty list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        assert client.list_articles() == []

    @patch('ai_content_autopilot.client.requests.get')
    def test_list_network_error_returns_empty(self, mock_get, client):
        """Network error returns empty list."""
        mock_get.side_effect = ConnectionError("Network down")
        assert client.list_articles() == []


class TestConfirmPublished:
    """Test confirm_published method."""

    @patch('ai_content_autopilot.client.requests.post')
    def test_confirm_success(self, mock_post, client):
        """Successful confirm returns True."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'success': True}
        mock_post.return_value = mock_resp

        result = client.confirm_published(42, 'https://myblog.com/article')
        assert result is True

    @patch('ai_content_autopilot.client.requests.post')
    def test_confirm_sends_correct_body(self, mock_post, client):
        """Confirm should POST with published_url in body."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'success': True}
        mock_post.return_value = mock_resp

        client.confirm_published(42, 'https://myblog.com/test')
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs['json'] == {'published_url': 'https://myblog.com/test'}

    @patch('ai_content_autopilot.client.requests.post')
    def test_confirm_404_returns_false(self, mock_post, client):
        """404 response returns False."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_post.return_value = mock_resp

        assert client.confirm_published(999, 'https://myblog.com/x') is False

    @patch('ai_content_autopilot.client.requests.post')
    def test_confirm_network_error_returns_false(self, mock_post, client):
        """Network error returns False."""
        mock_post.side_effect = ConnectionError("Network down")
        assert client.confirm_published(1, 'https://myblog.com/x') is False

    @patch('ai_content_autopilot.client.requests.post')
    def test_confirm_success_false(self, mock_post, client):
        """Server returning success=false should return False."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'success': False}
        mock_post.return_value = mock_resp

        assert client.confirm_published(42, 'https://myblog.com/x') is False
