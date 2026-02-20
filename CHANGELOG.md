# Changelog

## 1.0.2 (2026-02-20)

- Added webhook payload reference, article response fields, error handling, and rate limits to README
- Added CHANGELOG.md

## 1.0.1 (2026-02-20)

- Expanded README with Visibly overview, integration flow, and developer links
- Fixed `pyproject.toml` license format for twine compatibility

## 1.0.0 (2026-02-20)

- Initial release
- `VisiblyClient` — Pull API client (fetch, list, confirm articles)
- `verify_webhook_signature` — HMAC-SHA256 signature verification
- `contentpilot_webhook_bp` — Flask Blueprint for webhook reception
- `configure_visibly` — one-call configuration for the Blueprint
- `default_flask_blog_handler` — saves articles as JSON to `./content_output/`
- 43 tests covering security, client, and webhook functionality
