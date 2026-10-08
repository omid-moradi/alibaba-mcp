# syntax=docker/dockerfile:1
# Alibaba MCP — production-oriented image.
#
# Build:  docker build -t alibaba-mcp .
# Run:    docker run -p 8000:8000 alibaba-mcp
#
# Design:
# - uv-based deterministic install (uv.lock committed)
# - non-root runtime user
# - no secrets baked in (all config via environment)
# - container healthcheck performs a real MCP initialize

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app
ENV UV_LINK_MODE=copy

# Install dependencies first for better layer caching.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

# Install the project itself.
COPY src ./src
COPY README.md ./
RUN uv sync --locked --no-dev


FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="Alibaba MCP" \
      org.opencontainers.image.description="Unofficial MCP server for Alibaba.ir-style travel discovery (portfolio project)" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/theomid80/alibaba-mcp"

# tzdata is required for Asia/Tehran timezone lookups.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /usr/sbin/nologin mcp

WORKDIR /app
COPY --from=builder --chown=mcp:mcp /app/.venv /app/.venv
COPY --chown=mcp:mcp src ./src
COPY --chown=mcp:mcp scripts/healthcheck.py ./healthcheck.py

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    ALIBABA_MCP_HOST=0.0.0.0 \
    ALIBABA_MCP_PORT=8000

USER mcp
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "/app/healthcheck.py"]

# Streamable HTTP transport for containerized/remote deployment.
CMD ["python", "-m", "alibaba_mcp", "--transport", "streamable-http"]
