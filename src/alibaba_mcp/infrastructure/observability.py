"""Tool observability: structured logging and timing for every tool call.

Usage (order matters — ``mcp.tool()`` must wrap the instrumented function):

    @mcp.tool()
    @instrumented("search_flights", provider="mock")
    async def search_flights(...): ...
"""

import functools
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from alibaba_mcp.infrastructure.logging_setup import get_logger
from alibaba_mcp.providers.base import ProviderError, RateLimitedError

logger = get_logger("alibaba_mcp.tools")

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def instrumented(tool_name: str, provider_name: str) -> Callable[[F], F]:
    """Wrap an async tool function with structured logs and latency timing."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
            except RateLimitedError as exc:
                logger.warning(
                    "tool rate limited",
                    extra={
                        "tool": tool_name,
                        "provider": provider_name,
                        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                        "status": "rate_limited",
                    },
                )
                raise exc
            except ProviderError as exc:
                logger.warning(
                    "tool failed with provider error",
                    extra={
                        "tool": tool_name,
                        "provider": provider_name,
                        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                        "status": "provider_error",
                        "error_category": type(exc).__name__,
                    },
                )
                raise exc
            except Exception as exc:
                logger.exception(
                    "tool crashed",
                    extra={
                        "tool": tool_name,
                        "provider": provider_name,
                        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                        "status": "crash",
                        "error_category": type(exc).__name__,
                    },
                )
                raise exc
            logger.info(
                "tool completed",
                extra={
                    "tool": tool_name,
                    "provider": provider_name,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                    "status": "ok",
                },
            )
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
