"""Unit tests for configuration and the live provider refusal."""

import pytest
from pydantic import ValidationError

from alibaba_mcp.config import ProviderMode, Settings
from alibaba_mcp.providers.alibaba import AlibabaProvider
from alibaba_mcp.providers.base import ProviderNotConfiguredError
from alibaba_mcp.providers.mock import MockProvider


class TestSettings:
    def test_defaults_are_mock_mode(self) -> None:
        settings = Settings(rate_limit_max_calls=0)
        assert settings.provider is ProviderMode.MOCK
        assert settings.auth_enabled is False

    def test_invalid_log_level_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Settings(log_level="LOUD")

    def test_auth_needs_token_and_issuer(self) -> None:
        assert Settings(api_token="t").auth_enabled is False
        assert Settings(auth_issuer_url="https://x").auth_enabled is False
        assert Settings(api_token="t", auth_issuer_url="https://x").auth_enabled is True

    def test_scopes_splitting(self) -> None:
        assert Settings(required_scopes="travel:read, travel:write").scopes_list == [
            "travel:read",
            "travel:write",
        ]


class TestAlibabaProviderRefusal:
    """The live provider must fail loudly and never fall back to mock."""

    @pytest.fixture
    def provider(self) -> AlibabaProvider:
        return AlibabaProvider(base_url="https://example.test", timeout_seconds=5)

    async def test_search_refuses_with_clear_error(self, provider: AlibabaProvider) -> None:
        from datetime import date, timedelta

        with pytest.raises(ProviderNotConfiguredError, match="no official public API"):
            await provider.search_flights("THR", "MHD", date.today() + timedelta(days=1))

    async def test_booking_refuses(self, provider: AlibabaProvider) -> None:
        with pytest.raises(ProviderNotConfiguredError):
            await provider.create_booking("flight", "FLT-1", 1)

    def test_provider_is_not_mock(self, provider: AlibabaProvider) -> None:
        assert provider.is_mock is False
        assert provider.supports_bookings is False

    def test_mock_provider_is_mock(self) -> None:
        assert MockProvider().is_mock is True
