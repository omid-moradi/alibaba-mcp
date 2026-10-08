# Alibaba.ir live-integration investigation notes

**Date of investigation:** 2026-10-08
**Conclusion: LIVE INTEGRATION NOT VERIFIED — MOCK MODE AVAILABLE.**

This document records exactly what was investigated and why the live
Alibaba.ir provider in this project is an honest placeholder rather than a
working integration.

## What was investigated

| Step | Method | Result |
|------|--------|--------|
| Official developer API / docs | Searched alibaba.ir for any public developer portal, API docs or OpenAPI spec | **None found.** The only partner-facing product is "پنل آژانسی" (agency panel), which requires a registered travel-agency account and is not a public API |
| Public site robots.txt | `https://www.alibaba.ir/robots.txt` | Permissive (`Sitemap:` only). No API-discovery help |
| Sitemap | `https://www.alibaba.ir/sitemap.xml` | **SEO landing pages only** (`/flight/...`, `/train/...`, `/bus/...`, `/tour/...`, `/accommodation/...`). No public data endpoints |
| Server-rendered flight data | Fetched public SEO pages looking for embedded JSON (`__NEXT_DATA__`-style hydration payloads with offers/prices) | Search results are **not** exposed in public HTML; inventory is fetched client-side by the web app |
| Internal API host | Probed the web app's historically referenced API host (`ws.alibaba.ir`) read-only, root path | Root returns **404**; endpoints are undocumented and not exposed for third-party use |

## Why no live integration was implemented

1. **No official public API exists.** There is no documented, publicly
   accessible Alibaba.ir API that third parties are permitted to use.
2. **Undocumented internal endpoints are protected.** The endpoints used by
   Alibaba.ir's own clients require sessions/anti-bot protections
   (historically including CAPTCHA on search flows). Using them would mean
   scraping, bypassing access controls, or violating the site's terms — all
   explicitly out of scope for this project.
3. **The project's own rules forbid it.** This project never scrapes,
   never bypasses CAPTCHA/authentication/rate limits, and never fabricates
   data. With no legitimate live path available, the honest outcome is a
   **documented limitation**, not a reverse-engineered integration.

## What the code does instead

- `src/alibaba_mcp/providers/alibaba/` keeps the full adapter seam:
  - `endpoints.py` — centralized endpoint map (all placeholder values,
    clearly marked unverified)
  - `client.py` — hardened HTTP transport (timeouts, bounded concurrency,
    conservative retries, honest user agent, rate-limit respect) that is
    dormant until a legitimate API exists
  - `AlibabaProvider` implements the whole `TravelProvider` protocol and
    **fails every call with `ProviderNotConfiguredError`** explaining why,
    with a pointer to this document
- The provider factory (`providers/__init__.py`) never silently substitutes
  mock data in live mode (asserted by `tests/live/test_live_smoke.py`).
- `MockProvider` is deterministic and every result is labeled
  `is_mock_data: true`.

## How a legitimate live integration would be added

If Alibaba.ir ever publishes an official public API (or grants API access):

1. Put real endpoints in `providers/alibaba/endpoints.py`.
2. Add response schemas + parsers mapping raw responses to the domain
   models in `src/alibaba_mcp/domain/models.py` (the normalized model
   contract does not change).
3. Wire the HTTP transport (`client.py`) into `AlibabaProvider`'s methods.
4. Replace the refusal tests in `tests/live/test_live_smoke.py` with real
   read-only smoke tests (airport lookup, flight search for a valid future
   date), run with `uv run pytest -m live`.
5. Update `docs/live-integration-notes.md` and the README with verified
   endpoint behavior.

No MCP-layer changes would be required — that is the point of the provider
seam.
