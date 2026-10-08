# Contributing to Alibaba MCP

Thanks for your interest! This is an **unofficial educational/portfolio
project**, not affiliated with Alibaba.ir. Please keep that framing in all
docs and code.

## Getting started

```bash
git clone https://github.com/theomid80/alibaba-mcp
cd alibaba-mcp
uv sync --group dev            # creates .venv with pinned dev dependencies
uv run pytest                  # 59 tests should pass (3 live tests deselected)
uv run python scripts/mcp_smoke.py    # quick manual smoke check
```

## Development workflow

1. Create a feature branch.
2. Make your change with tests.
3. Ensure all quality gates pass:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run pytest -m live   # offline assertions about live-mode behavior
```

4. Open a PR following the template.

`pre-commit` is configured for local convenience:

```bash
uv run pre-commit install
```

## Project layout

- `src/alibaba_mcp/domain/` — normalized Pydantic models & enums (no I/O)
- `src/alibaba_mcp/providers/` — `TravelProvider` protocol + mock/live providers
- `src/alibaba_mcp/application/` — use-cases (comparisons, cost, policies)
- `src/alibaba_mcp/mcp/` — MCP tools / resources / prompts + context
- `src/alibaba_mcp/infrastructure/` — logging, rate limiting, observability
- `client/` — real MCP client demo + MCP→LangChain bridge
- `examples/` — LangGraph agent
- `tests/` — unit / integration / e2e / live-marker suites

## Hard rules

- **No live Alibaba.ir scraping.** Never add CAPTCHA bypasses,
  authentication bypasses, anti-bot circumvention, session spoofing or
  private-data access. If a capability requires those, it is out of scope.
- **Never silently mix mock and live data.** Mock results must carry
  `is_mock_data: true`; live failures must surface as errors.
- **No secrets in code.** Configuration only via environment variables.
- **Type hints everywhere in `src/`** (`mypy --strict` must pass).
- **Bookings stay sandboxed**: simulated, in-process, clearly labeled.

## Commit style

Conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`), one
logical change per commit.
