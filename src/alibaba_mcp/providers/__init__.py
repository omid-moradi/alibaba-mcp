"""Provider package: factory that resolves the configured provider.

Provider selection is explicit and never falls back silently. If ``live`` is
configured, the server uses ``AlibabaProvider`` (which reports an honest
error until a legitimate official API exists) — it never swaps in mock data
behind the caller's back.
"""

from alibaba_mcp.config import Settings
from alibaba_mcp.providers.alibaba import AlibabaProvider
from alibaba_mcp.providers.base import TravelProvider
from alibaba_mcp.providers.mock import MockProvider


def get_provider(settings: Settings) -> TravelProvider:
    """Build the provider selected by settings.

    Raises ``ValueError`` for unknown modes rather than guessing.
    """
    if settings.provider.value == "mock":
        return MockProvider()
    if settings.provider.value == "live":
        return AlibabaProvider(
            base_url=settings.api_base_url,
            timeout_seconds=settings.api_timeout_seconds,
        )
    raise ValueError(f"Unknown provider mode: {settings.provider!r}")


__all__ = ["get_provider", "MockProvider", "AlibabaProvider", "TravelProvider"]
