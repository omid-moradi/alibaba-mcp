# Security Policy

## Scope

Alibaba MCP is an unofficial, educational/portfolio MCP server. This policy
covers the code in this repository, its default (mock) configuration and
its optional remote (Streamable HTTP) mode.

## Reporting a vulnerability

Please report suspected vulnerabilities privately by opening a GitHub
Security Advisory (GitHub → Security → "Report a vulnerability") instead of
a public issue. Include reproduction steps and affected versions. You will
receive a response as soon as possible.

## Trust boundaries

```
MCP host (Claude/Cursor/VS Code/custom client)
    |  MCP over stdio (local trust) or Streamable HTTP (network trust)
    v
Alibaba MCP server
    |  provider seam
    v
MockProvider (in-process, no network)   |   AlibabaProvider (dormant)
```

- **stdio**: the transport is only as safe as the local host running it.
  Standard MCP host security applies.
- **Streamable HTTP**: the server becomes a network service. It must be
  placed behind TLS and bearer-token authorization (see below).

## Authentication & authorization (Streamable HTTP)

Implemented per the official MCP Python SDK v2 authorization model: the
server is an **OAuth 2.1 resource server** — it verifies bearer tokens and
never issues them.

- Disabled by default (local development).
- Enabled by setting BOTH `ALIBABA_MCP_API_TOKEN` and
  `ALIBABA_MCP_AUTH_ISSUER_URL`. Requests must then carry
  `Authorization: Bearer <token>`; required scopes are configured with
  `ALIBABA_MCP_REQUIRED_SCOPES` (default `travel:read`).
- The SDK publishes RFC 9728 Protected Resource Metadata at
  `/.well-known/oauth-protected-resource/...` and answers unauthenticated
  requests with 401 + `WWW-Authenticate`.
- The shipped `StaticTokenVerifier` is a demonstration verifier. In
  production, replace it with JWT signature verification or authorization-server
  introspection (see `src/alibaba_mcp/server.py`, `_build_auth_kwargs`).

Never enable bearer auth without TLS in production.

## Secrets

- No secrets are hard-coded. All configuration comes from environment
  variables (see `.env.example`).
- `.env` files are git-ignored.
- Structured logging deliberately whitelists the fields it emits; tokens,
  API keys, cookies and personal data are never logged.
- Rate limiting is enforced per tool (sliding window) and surfaces as a
  model-readable tool error; it is never bypassed.

## Live-provider safety rules (non-negotiable)

The live Alibaba provider MUST NOT (and does not):

- scrape protected endpoints,
- bypass CAPTCHA, authentication or anti-bot systems,
- circumvent rate limits,
- access private/customer data,
- perform bookings, payments or any side effect on real systems.

See `docs/live-integration-notes.md` for why live mode is currently
unavailable and how a legitimate integration would be wired in.

## Data exposure

- The mock provider serves only synthetic, deterministic fixture data.
- Every search result carries `is_mock_data: true` in mock mode, so an LLM
  can never mistake demo data for real inventory.
- Bookings are simulated and in-process only.
