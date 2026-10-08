"""Server-side rate limiting for tool calls.

A simple in-process sliding-window limiter, keyed per tool. It protects the
process (and, in live mode, would protect the upstream) from runaway agent
loops. It is deliberately NOT an attempt to bypass any upstream limit.

For multi-replica deployments this interface is where a Redis-backed
implementation would slot in without touching the MCP layer.
"""

import time
from collections import deque


class RateLimitExceeded(Exception):
    """Raised when a key has exceeded its allowed calls in the window."""

    def __init__(self, retry_after_seconds: float) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded. Retry after {retry_after_seconds:.0f} seconds.")


class SlidingWindowRateLimiter:
    """Per-key sliding-window limiter. Thread-hostile by design (asyncio only)."""

    def __init__(self, max_calls: int, window_seconds: float) -> None:
        self._max_calls = max_calls
        self._window = window_seconds
        self._events: dict[str, deque[float]] = {}

    @property
    def enabled(self) -> bool:
        return self._max_calls > 0

    def acquire(self, key: str) -> None:
        """Record one call for ``key`` or raise ``RateLimitExceeded``."""
        if not self.enabled:
            return
        now = time.monotonic()
        events = self._events.setdefault(key, deque())
        while events and events[0] <= now - self._window:
            events.popleft()
        if len(events) >= self._max_calls:
            retry_after = self._window - (now - events[0])
            raise RateLimitExceeded(retry_after)
        events.append(now)
