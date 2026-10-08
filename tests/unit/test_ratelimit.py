"""Unit tests for the sliding-window rate limiter."""

import pytest

from alibaba_mcp.infrastructure.ratelimit import (
    RateLimitExceeded,
    SlidingWindowRateLimiter,
)


def test_disabled_limiter_never_blocks() -> None:
    limiter = SlidingWindowRateLimiter(max_calls=0, window_seconds=60)
    assert limiter.enabled is False
    for _ in range(100):
        limiter.acquire("any-key")


def test_blocks_after_max_calls() -> None:
    limiter = SlidingWindowRateLimiter(max_calls=3, window_seconds=60)
    for _ in range(3):
        limiter.acquire("t")
    with pytest.raises(RateLimitExceeded) as excinfo:
        limiter.acquire("t")
    assert excinfo.value.retry_after_seconds > 0


def test_keys_are_independent() -> None:
    limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=60)
    limiter.acquire("tool-a")
    limiter.acquire("tool-b")  # different key: unaffected
    with pytest.raises(RateLimitExceeded):
        limiter.acquire("tool-a")


def test_window_slides() -> None:
    limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=0.05)
    limiter.acquire("k")
    with pytest.raises(RateLimitExceeded):
        limiter.acquire("k")
    import time

    time.sleep(0.06)
    limiter.acquire("k")  # old event slid out of the window
