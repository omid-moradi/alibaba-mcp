"""Async HTTP transport for the Alibaba.ir live provider.

Encapsulates the operational hardening a live provider would need:
connection reuse, timeouts, bounded concurrency, and a conservative retry
policy (only for idempotent requests that failed at the transport level).
It deliberately contains NO browser fingerprinting, NO cookie replay and
NO anti-bot bypass logic — if the upstream refuses anonymous access, that
is a legitimate limitation and must be reported, not circumvented.

This module is currently dormant: it exists so that wiring a future
official API is a small change confined to the provider package.
"""

import asyncio

import httpx

from alibaba_mcp.providers.base import (
    ExternalAPIError,
    ParsingError,
    RateLimitedError,
    TimeoutError,
)

_MAX_CONCURRENCY = 4
_RETRY_ATTEMPTS = 2
_RETRY_BACKOFF_SECONDS = 0.5


class AlibabaHttpClient:
    """Hardened async HTTP client factory for live provider calls."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 10.0,
        max_concurrency: int = _MAX_CONCURRENCY,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required for the live HTTP client")
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_seconds),
            # A plain, honest user agent. No browser spoofing.
            headers={"User-Agent": "alibaba-mcp/0.1 (unofficial portfolio project)"},
        )
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _sleep_backoff(self, attempt: int) -> None:
        await asyncio.sleep(_RETRY_BACKOFF_SECONDS * (2**attempt))

    async def get_json(self, path: str, params: dict[str, str] | None = None) -> object:
        """GET a JSON document with timeouts, bounded concurrency and retries.

        Retries happen only on transport-level failures (connection errors,
        timeouts). HTTP 4xx/5xx responses are surfaced as provider errors —
        never retried blindly, never bypassed.
        """
        for attempt in range(_RETRY_ATTEMPTS + 1):
            try:
                async with self._semaphore:
                    response = await self._client.get(path, params=params)
            except httpx.TimeoutException as exc:
                if attempt < _RETRY_ATTEMPTS:
                    await self._sleep_backoff(attempt)
                    continue
                raise TimeoutError(
                    f"Upstream request to '{path}' timed out after retries. "
                    f"Transport detail: {exc.__class__.__name__}."
                ) from exc
            except httpx.HTTPError as exc:
                if attempt < _RETRY_ATTEMPTS:
                    await self._sleep_backoff(attempt)
                    continue
                raise ExternalAPIError(
                    f"Transport failure talking to upstream '{path}': {exc.__class__.__name__}"
                ) from exc

            if response.status_code == 429:
                raise RateLimitedError(
                    "Upstream applied a rate limit (HTTP 429). Back off and retry later; "
                    "this project never bypasses rate limits."
                )
            if response.status_code >= 500:
                raise ExternalAPIError(
                    f"Upstream server error (HTTP {response.status_code}) for '{path}'."
                )
            if response.status_code >= 400:
                raise ExternalAPIError(
                    f"Upstream rejected the request (HTTP {response.status_code}) for '{path}'. "
                    "Live access may require credentials or terms this project does not have."
                )
            try:
                return response.json()
            except ValueError as exc:
                raise ParsingError(f"Upstream returned a non-JSON body for '{path}'.") from exc

        raise ExternalAPIError(f"Request to '{path}' failed after retries.")
