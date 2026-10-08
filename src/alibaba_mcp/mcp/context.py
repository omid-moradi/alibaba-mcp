"""Shared context injected into every MCP tool module."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from mcp.server.mcpserver.exceptions import ToolError

from alibaba_mcp.application.services import TravelService
from alibaba_mcp.config import Settings
from alibaba_mcp.infrastructure.ratelimit import RateLimitExceeded, SlidingWindowRateLimiter
from alibaba_mcp.providers.base import (
    InvalidInputError,
    NotFoundError,
    ProviderError,
    TravelProvider,
)

T = TypeVar("T")


@dataclass(frozen=True)
class AppContext:
    """Everything a tool needs besides its own arguments."""

    service: TravelService
    settings: Settings
    limiter: SlidingWindowRateLimiter

    @property
    def provider(self) -> TravelProvider:
        return self.service.provider

    def check_rate_limit(self, tool_name: str) -> None:
        """Apply the per-tool rate limit or raise a model-readable ToolError."""
        try:
            self.limiter.acquire(f"tool:{tool_name}")
        except RateLimitExceeded as exc:
            raise ToolError(
                f"Rate limit exceeded for tool '{tool_name}'. "
                f"Wait {exc.retry_after_seconds:.0f}s before trying again. "
                "This limit protects the server and its upstream; it is never bypassed."
            ) from exc

    async def call(self, tool_name: str, factory: Callable[[], Awaitable[T]]) -> T:
        """Run a tool body with rate limiting and error mapping.

        Provider errors become ``ToolError`` results so the model can read the
        message and correct itself (e.g. fix an airport code). Unexpected
        exceptions are left alone: the SDK turns them into a generic error
        for the caller and logs the traceback server-side.
        """
        self.check_rate_limit(tool_name)
        try:
            return await factory()
        except (InvalidInputError, NotFoundError) as exc:
            # The model could have avoided this with better arguments.
            raise ToolError(str(exc)) from exc
        except ProviderError as exc:
            # Upstream/provider-level limitations (e.g. live mode unavailable).
            raise ToolError(str(exc)) from exc
