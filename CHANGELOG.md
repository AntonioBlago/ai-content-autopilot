# Changelog

## Unreleased — repository naming and documentation (2026-09-27)

- Rename the GitHub project from `ai-content-autopilot` to
  `visibly-ai-cms-connector`, displayed as **Visibly AI CMS Connector**.
- Explain the complete assistant → MCP → Visibly → CMS workflow and the role
  of anyCMS as concrete WordPress/Astro/Next.js/Flask use cases.
- Add a German integration guide and shared agent entry points; distinguish
  webhook acceptance from CMS publication and update stale README examples.
- Update repository metadata and install the project dependencies in CI.
- Keep the PyPI name `ai-content-autopilot`, Python imports, version 1.1.0,
  routes and environment configuration unchanged. No new PyPI release is implied.

## 1.1.0 (2026-09-14)

Two production findings, both from pushing an edited article back to a CMS.

### Fixed: the default base URL pointed at the wrong host

`VisiblyClient` and `configure_visibly` defaulted to
`https://www.antonioblago.com/content-autopilot`, where the autopilot used to
live. That host answers with a redirect today, so `fetch_article` returned
`None` while the webhook handler still reported success and nothing was ever
published. The default is now `https://app.visibly-ai.com`.

**If you set `base_url` explicitly, nothing changes for you.**

### Changed: the webhook Blueprint acknowledges before it works

Up to 1.0.2 the Blueprint fetched the article and ran your handler inside the
request. Visibly waits 10 seconds for a response and used to redeliver on a
timeout, so a slow handler was delivered to repeatedly. Measured in production
on 2026-09-14: three delivery attempts for one article became three LLM
translation runs on the receiving CMS.

The Blueprint now answers `202 {"status": "accepted"}` immediately and runs
the fetch and your handler in a background thread. A repeated delivery of an
article that is still being processed answers
`202 {"status": "already_processing"}` and is skipped.

**Breaking for anyone asserting on the response:** the success code is now
`202` instead of `200`, and a handler failure no longer surfaces as 422 / 500 /
502 — the delivery succeeded, the work did not, and a 5xx would only invite a
retry that reproduces the same error. Failures go to your logs.
Pass `background=False` to `configure_visibly()` to keep the old synchronous
behaviour and its response codes.

### Added

- `article.updated` documented: fires when an already published article is
  edited in Visibly and pushed back. The payload carries `published_url` and
  `revision`, injected into the article dict as `_published_url` / `_revision`.
- Article fields `plan_id`, `url_prefix`, `content_language`, `target_country`,
  `recommended_page_type`, `revision` and `content_format` documented. The two
  language fields are new in the Visibly Pull API and make multilingual routing
  possible.
- README section **Delivery Contract**: what each response code means to
  Visibly, and which failures it retries.
- README section **Multilingual Sites and hreflang**: the two ways to publish
  in several languages, how the hreflang structure comes about, and what
  Visibly does not tell you yet.
- `DEFAULT_BASE_URL` is now exported from `ai_content_autopilot.client`.

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
