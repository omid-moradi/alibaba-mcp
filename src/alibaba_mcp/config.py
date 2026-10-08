"""Environment-based configuration.

All runtime configuration comes from environment variables (optionally an
`.env` file). Secrets are never hard-coded and never logged.
"""

from enum import StrEnum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderMode(StrEnum):
    """Which data source the server should use."""

    MOCK = "mock"
    LIVE = "live"


class Settings(BaseSettings):
    """Server settings resolved from the environment (see `.env.example`)."""

    model_config = SettingsConfigDict(
        env_prefix="ALIBABA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- provider ----------------------------------------------------------
    provider: ProviderMode = ProviderMode.MOCK
    api_base_url: str = ""
    api_timeout_seconds: float = Field(default=10.0, gt=0, le=60.0)

    # -- server (Streamable HTTP) -------------------------------------------
    mcp_host: str = "127.0.0.1"
    mcp_port: int = Field(default=8000, ge=1, le=65535)
    mcp_path: str = "/mcp"

    # -- logging --------------------------------------------------------------
    log_level: str = "INFO"

    # -- rate limiting ----------------------------------------------------------
    rate_limit_max_calls: int = Field(default=60, ge=0)
    rate_limit_window_seconds: float = Field(default=60.0, gt=0)

    # -- optional bearer-token authorization (Streamable HTTP only) -------------
    api_token: str = ""
    auth_issuer_url: str = ""
    required_scopes: str = "travel:read"

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return upper

    @property
    def auth_enabled(self) -> bool:
        """Bearer-token authorization is on only when token AND issuer are set."""
        return bool(self.api_token and self.auth_issuer_url)

    @property
    def scopes_list(self) -> list[str]:
        return [s.strip() for s in self.required_scopes.split(",") if s.strip()]
