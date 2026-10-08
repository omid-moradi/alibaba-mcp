"""Live smoke tests against the (currently unavailable) live provider.

Run explicitly with:

    uv run pytest -m live

These tests document the honest status of live Alibaba.ir integration.
Until Alibaba publishes an official public API (see
docs/live-integration-notes.md), the live provider must REFUSE to serve
data rather than fabricate it — and that refusal is exactly what these
tests assert.

If a legitimate live integration is ever wired in, replace the refusal
assertions here with real read-only smoke tests (search airport, search
flight for a valid future date, verify HTTP status / parse / normalize).
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from alibaba_mcp.config import ProviderMode, Settings
from alibaba_mcp.providers import get_provider
from alibaba_mcp.providers.alibaba import AlibabaProvider
from alibaba_mcp.providers.base import ProviderNotConfiguredError, TravelProvider

pytestmark = pytest.mark.live


async def test_live_provider_refuses_instead_of_fabricating() -> None:
    """CRITICAL: live mode must never return mock or made-up data."""
    provider: TravelProvider = AlibabaProvider(base_url="https://placeholder.test")
    with pytest.raises(ProviderNotConfiguredError, match="no official public API"):
        await provider.search_flights("THR", "MHD", date.today() + timedelta(days=1))


async def test_server_in_live_mode_reports_clear_error() -> None:
    """A live-mode server surfaces an honest tool error, not mock data."""
    from mcp import Client

    from alibaba_mcp.server import create_server

    settings = Settings(
        provider=ProviderMode.LIVE,
        api_base_url="https://placeholder.test",
        rate_limit_max_calls=0,
    )
    server = create_server(settings)
    async with Client(server, raise_exceptions=True) as client:
        result = await client.call_tool(
            "search_flights",
            {
                "origin": "THR",
                "destination": "MHD",
                "departure_date": (date.today() + timedelta(days=1)).isoformat(),
            },
        )
        assert result.is_error
        assert "no official public API" in result.content[0].text
        # and crucially: no mock data was silently substituted
        assert result.structured_content is None


async def test_factory_never_silently_falls_back_to_mock() -> None:
    settings = Settings(provider=ProviderMode.LIVE, api_base_url="https://placeholder.test")
    provider = get_provider(settings)
    assert provider.is_mock is False
