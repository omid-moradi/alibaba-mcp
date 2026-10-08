"""Shared test fixtures.

Mock provider + disabled rate limiting by default; the rate-limit behavior
itself has dedicated tests with an explicitly configured server.

Async tests run under the anyio pytest plugin (the same pattern the MCP
SDK's own test-suite uses), with all async tests auto-marked.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator

import pytest
from mcp import Client

from alibaba_mcp.config import ProviderMode, Settings
from alibaba_mcp.server import create_server


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply the anyio marker to coroutine tests."""
    for item in items:
        if isinstance(item, pytest.Function) and inspect.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.anyio)


def make_test_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "provider": ProviderMode.MOCK,
        "rate_limit_max_calls": 0,  # disabled for most tests
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.fixture
def server():
    return create_server(make_test_settings())


@pytest.fixture
async def client(server) -> AsyncIterator[Client]:
    async with Client(server, raise_exceptions=True) as c:
        yield c
