# ai-content-autopilot

Python SDK for the **[Visibly Content Autopilot](https://www.antonioblago.com/content-autopilot)** API.

Visibly Content Autopilot is an AI-powered content generation platform that creates SEO-optimized articles for your projects. It handles keyword research, content planning, and article generation — then delivers finished articles to your CMS via webhooks or a Pull API.

This SDK gives you everything you need to integrate Content Autopilot into any Python/Flask application:

- **Pull API Client** — fetch, list, and confirm articles programmatically
- **Webhook Receiver** — a ready-made Flask Blueprint that verifies HMAC signatures, fetches full article content, and calls your handler
- **HMAC-SHA256 Verification** — standalone signature verification for custom webhook implementations

## How It Works

```
1. Content Autopilot generates & approves an article
                    |
2. Webhook fires to your endpoint (POST /webhooks/visibly)
   with HMAC-SHA256 signature for security
                    |
3. Your app verifies the signature, then calls the Pull API
   to fetch the full article (HTML, Markdown, keywords, SEO score)
                    |
4. Your app saves/publishes the article in your CMS
                    |
5. Your app confirms publication back to Visibly
   (article status changes to "published")
```

## Installation

```bash
pip install ai-content-autopilot
```

**Requirements:** Python 3.8+, Flask 2.3+, Requests 2.25+

## Getting Started

### 1. Get your credentials

- **API Key**: Go to [Account > API Keys](https://www.antonioblago.com/account/api-keys) and create a new key (starts with `sk_live_`)
- **Webhook Secret**: Go to your Project > CMS Settings and configure a webhook endpoint. The secret is generated automatically.

Full API documentation: **[Developer Docs](https://www.antonioblago.com/developers)**

### 2. Choose your integration style

#### Option A: Full Flask Blueprint (recommended)

The easiest way to integrate. Register the blueprint and provide a handler function — the SDK handles signature verification, article fetching, and error responses automatically.

```python
from flask import Flask
from ai_content_autopilot import configure_visibly, contentpilot_webhook_bp

app = Flask(__name__)

def my_handler(article):
    """Called when a webhook delivers an article.

    article dict contains:
      id, title, slug, content_html, content_markdown,
      keywords, meta_description, seo_score, word_count,
      _webhook_event, _webhook_timestamp, _scheduled_date
    """
    # Save to your database, CMS, filesystem, etc.
    db.session.add(Post(
        title=article['title'],
        body=article['content_html'],
        slug=article['slug'],
        publish_at=article.get('_scheduled_date'),
    ))
    db.session.commit()
    return True  # Return False to reject (422 response)

configure_visibly(
    webhook_secret='your-webhook-secret',
    api_key='sk_live_your_api_key',
    on_article_received=my_handler,
)

app.register_blueprint(contentpilot_webhook_bp)
# POST /webhooks/visibly is now active and handles:
#   1. HMAC-SHA256 signature verification
#   2. Full article fetch via Pull API
#   3. Calls my_handler(article)
#   4. Returns {"success": true} or appropriate error
```

#### Option B: Standalone Pull API Client

Use the client directly to poll for articles or integrate into non-Flask applications.

```python
from ai_content_autopilot import VisiblyClient

client = VisiblyClient(api_key='sk_live_your_api_key')

# List approved articles ready for publishing
articles = client.list_articles(status='approved', project_id=5, limit=20)
for a in articles:
    print(a['id'], a['title'], a.get('scheduled_date'))

# Fetch a single article with full content
article = client.fetch_article(42, include_markdown=True)
print(article['content_html'])
print(article['keywords'])       # e.g. ["seo", "keyword research"]
print(article['seo_score'])      # 0-100

# Confirm publication (updates status to "published" in Visibly)
client.confirm_published(42, 'https://myblog.com/seo-guide-2026')
```

#### Option C: HMAC verification only

For custom webhook implementations in any framework.

```python
from ai_content_autopilot import verify_webhook_signature

# In your webhook endpoint:
payload_bytes = request.get_data()       # raw bytes, NOT request.json
signature = request.headers.get('X-Webhook-Signature', '')

if not verify_webhook_signature(payload_bytes, 'your-secret', signature):
    return {'error': 'Invalid signature'}, 401
```

## Article Lifecycle

| Status | Description | Webhook Event |
|--------|-------------|---------------|
| `queued` | Waiting to be generated | - |
| `generating` | AI is writing the article | - |
| `draft` | Draft ready for review | - |
| `approved` | Ready for publishing | `article.approved` |
| `published` | Confirmed published via API | `article.published` |
| `rejected` | Rejected by user | - |
| `failed` | Generation failed | `article.failed` |

## API Reference

| Function / Class | Description |
|---|---|
| `configure_visibly(webhook_secret, api_key, base_url, on_article_received)` | Configure the Blueprint with credentials and callback |
| `verify_webhook_signature(payload_bytes, secret, signature_header)` | Verify HMAC-SHA256 signature. Returns `True`/`False` |
| `VisiblyClient(api_key, base_url, timeout)` | Pull API client for fetching, listing, and confirming articles |
| `client.fetch_article(article_id, include_markdown)` | Returns article dict or `None` on error |
| `client.list_articles(status, project_id, limit, offset)` | Returns list of article dicts |
| `client.confirm_published(article_id, published_url)` | Confirms publication. Returns `True`/`False` |
| `contentpilot_webhook_bp` | Flask Blueprint. Register with `app.register_blueprint()`. Endpoint: `POST /webhooks/visibly` |
| `default_flask_blog_handler(article)` | Default handler: saves article as JSON to `./content_output/` |

## Webhook Security

Every webhook request includes an `X-Webhook-Signature` header with an HMAC-SHA256 signature:

```
X-Webhook-Signature: sha256=<hex_digest>
```

The SDK verifies this automatically when using the Blueprint. The verification uses `hmac.compare_digest` for timing-safe comparison to prevent timing attacks.

## Links

- [Developer Documentation](https://www.antonioblago.com/developers) — full API docs, endpoint reference, code examples in Python, Node.js, and PHP
- [Visibly Content Autopilot](https://www.antonioblago.com/content-autopilot) — the platform
- [API Keys](https://www.antonioblago.com/account/api-keys) — manage your API keys
- [GitHub Repository](https://github.com/AntonioBlago/ai-content-autopilot)
- [PyPI Package](https://pypi.org/project/ai-content-autopilot/)

## Development

```bash
git clone https://github.com/AntonioBlago/ai-content-autopilot.git
cd ai-content-autopilot
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT - see [LICENSE](LICENSE) for details.
