"""Server assembly: build the fully-wired MCPServer.

Wiring order: settings -> provider -> service -> tool context -> MCPServer
with tools, resources, prompts and (optionally) bearer-token authorization.

Exposes a module-level ``mcp`` instance so that ``mcp run server.py`` and
``uv run mcp dev server.py`` (which look for a module-level server object)
work against the root ``server.py`` shim.
"""

from mcp.server import MCPServer
from pydantic import AnyHttpUrl

from alibaba_mcp.application.services import TravelService
from alibaba_mcp.config import Settings
from alibaba_mcp.infrastructure.logging_setup import configure_logging
from alibaba_mcp.infrastructure.ratelimit import SlidingWindowRateLimiter
from alibaba_mcp.mcp import prompts as prompts_module
from alibaba_mcp.mcp import resources as resources_module
from alibaba_mcp.mcp.context import AppContext
from alibaba_mcp.mcp.tools import register_all
from alibaba_mcp.providers import get_provider

INSTRUCTIONS = """\
Alibaba MCP — unofficial demo server for Alibaba.ir-style travel discovery.

How to work with this server:
1. Resolve places with search_airports (flights) or search_cities
   (trains, buses, hotels) before searching.
2. Prefer compare_travel_options when the user wants cheapest/fastest
   overall; use the mode-specific search tools otherwise.
3. All prices are per person, in Iranian Toman (IRT).
4. Every search result carries is_mock_data: when true, present results as
   simulated demo data — never as real Alibaba.ir inventory.
5. Bookings are ALWAYS simulated (sandbox). Never claim a real reservation.
6. This project is not affiliated with Alibaba.ir.
"""


def _build_auth_kwargs(settings: Settings) -> dict[str, object]:
    """Optional OAuth 2.1 resource-server protection (Streamable HTTP only).

    Follows the official SDK guidance: the MCP server acts as a resource
    server that verifies bearer tokens; it never issues tokens itself.
    Enabled only when both ALIBABA_MCP_API_TOKEN and
    ALIBABA_MCP_AUTH_ISSUER_URL are set.
    """
    if not settings.auth_enabled:
        return {}

    from mcp.server.auth.provider import AccessToken, TokenVerifier
    from mcp.server.auth.settings import AuthSettings

    class StaticTokenVerifier(TokenVerifier):
        """Verifies a single statically-configured bearer token.

        A real deployment would instead verify JWT signatures or call the
        authorization server's introspection endpoint — the verifier is the
        only piece that changes.
        """

        async def verify_token(self, token: str) -> AccessToken | None:
            if token != settings.api_token:
                return None
            return AccessToken(
                token=token,
                client_id="configured-client",
                scopes=settings.scopes_list,
            )

    resource = f"http://{settings.mcp_host}:{settings.mcp_port}{settings.mcp_path}"
    return {
        "token_verifier": StaticTokenVerifier(),
        "auth": AuthSettings(
            issuer_url=AnyHttpUrl(settings.auth_issuer_url),
            resource_server_url=AnyHttpUrl(resource),
            required_scopes=settings.scopes_list,
        ),
    }


def create_server(settings: Settings | None = None) -> MCPServer:
    settings = settings or Settings()
    configure_logging(settings.log_level)

    provider = get_provider(settings)
    service = TravelService(provider)
    limiter = SlidingWindowRateLimiter(
        settings.rate_limit_max_calls, settings.rate_limit_window_seconds
    )
    ctx = AppContext(service=service, settings=settings, limiter=limiter)

    server = MCPServer(
        "Alibaba MCP",
        instructions=INSTRUCTIONS,
        **_build_auth_kwargs(settings),  # type: ignore[arg-type]
    )
    register_all(server, ctx)
    resources_module.register(server, ctx)
    prompts_module.register(server, ctx)
    return server


# Module-level instance used by `mcp run server.py` / `uv run mcp dev server.py`.
mcp = create_server()
