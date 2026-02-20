# ai-content-autopilot

Python SDK for the **Visibly Content Autopilot API**. Provides a Pull API client, HMAC-SHA256 webhook verification, and a Flask Blueprint for receiving webhooks.

## Installation

```bash
pip install ai-content-autopilot
```

## Quick Start

### Option A: Full Flask Blueprint (webhook receiver + auto-fetch)

```python
from ai_content_autopilot import configure_visibly, contentpilot_webhook_bp

def my_handler(article):
    """Called when a webhook delivers an article."""
    print(article['title'], article['content_html'])
    return True

configure_visibly(
    webhook_secret='your-webhook-secret',
    api_key='sk_live_your_api_key',
    on_article_received=my_handler,
)

app.register_blueprint(contentpilot_webhook_bp)
# POST /webhooks/visibly is now active
```

### Option B: Standalone Pull API Client

```python
from ai_content_autopilot import VisiblyClient

client = VisiblyClient(api_key='sk_live_your_api_key')

# List approved articles
articles = client.list_articles(status='approved', project_id=5)

# Fetch single article with full content
article = client.fetch_article(42, include_markdown=True)

# Confirm publication
client.confirm_published(42, 'https://myblog.com/seo-guide')
```

### Option C: HMAC verification only

```python
from ai_content_autopilot import verify_webhook_signature

is_valid = verify_webhook_signature(
    payload_bytes=request.get_data(),
    secret='your-webhook-secret',
    signature_header=request.headers.get('X-Webhook-Signature', ''),
)
```

## API Reference

| Function / Class | Description |
|---|---|
| `configure_visibly(webhook_secret, api_key, base_url, on_article_received)` | Configure the Blueprint with credentials and callback |
| `verify_webhook_signature(payload_bytes, secret, signature_header)` | Verify HMAC-SHA256 signature. Returns True/False |
| `VisiblyClient(api_key, base_url, timeout)` | Pull API client for fetching, listing, and confirming articles |
| `client.fetch_article(article_id, include_markdown)` | Returns article dict or None |
| `client.list_articles(status, project_id, limit, offset)` | Returns list of article dicts |
| `client.confirm_published(article_id, published_url)` | Confirms publication. Returns True/False |
| `contentpilot_webhook_bp` | Flask Blueprint. Register with `app.register_blueprint()` |
| `default_flask_blog_handler(article)` | Default handler: saves article as JSON to `./content_output/` |

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT