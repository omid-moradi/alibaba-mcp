"""MCP resources: static/contextual data the application (not the model) reads.

Why Resources and not Tools: resources describe *state* the client can
attach to a conversation (policy text, reference data, server status).
They have no parameters that a model needs to guess and no side effects.
Searches, by contrast, are model-driven actions and therefore Tools.
"""

from mcp.server import MCPServer

from alibaba_mcp.application.policies import POLICY_DOCUMENTS, get_policy
from alibaba_mcp.domain.models import City
from alibaba_mcp.mcp.context import AppContext

_DISCLAIMER = (
    "# Note\n\nThis is an unofficial educational/portfolio project. It is not "
    "affiliated with Alibaba.ir. Policy texts are generic educational content, "
    "not official Alibaba.ir policies.\n"
)


def register(mcp: MCPServer, ctx: AppContext) -> None:
    provider = ctx.provider

    @mcp.resource("alibaba://travel/policies", mime_type="text/markdown")
    async def all_policies() -> str:
        """All travel policy documents in this server's knowledge base."""
        parts = ["# Travel policies\n"]
        for entry in POLICY_DOCUMENTS:
            parts.append(f"## {entry.title}\n\n{entry.text}\n")
        return _DISCLAIMER + "\n".join(parts)

    @mcp.resource("alibaba://travel/cancellation-policy", mime_type="text/markdown")
    async def cancellation_policy() -> str:
        """Cancellation and refund rules served by this server."""
        entry = get_policy("cancellation")
        refund = get_policy("refund")
        text = "# Cancellation policy\n\n"
        text += f"## {entry.title}\n\n{entry.text}\n\n" if entry else ""
        text += f"## {refund.title}\n\n{refund.text}\n" if refund else ""
        return _DISCLAIMER + text

    @mcp.resource("alibaba://travel/cities", mime_type="application/json")
    async def cities() -> list[City]:
        """All cities supported by this server, with their travel modes."""
        return await ctx.service.search_cities("", limit=20)

    @mcp.resource("alibaba://travel/provider-status", mime_type="application/json")
    async def provider_status() -> dict[str, object]:
        """Which data provider is active, and what that means for data authenticity."""
        info = provider.provider_info()
        return {
            "name": info.name,
            "mode": info.mode,
            "is_mock": info.is_mock,
            "description": info.description,
            "supported_products": info.supported_products,
            "bookings_supported": provider.supports_bookings,
            "bookings_are_simulated": True,
            "note": (
                "Mock mode serves deterministic synthetic data. Live mode is a "
                "placeholder that refuses to fabricate data until a legitimate "
                "official Alibaba.ir API exists (see docs/live-integration-notes.md)."
            ),
        }

    @mcp.resource("alibaba://travel/tool-guide", mime_type="text/markdown")
    async def tool_guide() -> str:
        """How an agent should use this server's tools, step by step."""
        return _DISCLAIMER + (
            "# Tool guide\n\n"
            "1. Resolve places first: `search_airports` (flights) or "
            "`search_cities` (trains/buses/hotels).\n"
            "2. Search options: `search_flights`, `search_trains`, `search_buses`, "
            "`search_hotels`, `search_tours` — or `compare_travel_options` when the "
            "user wants the cheapest/fastest overall.\n"
            "3. Deep-dive a single option: `get_flight_details`, `get_train_details`, "
            "`get_bus_details`, `get_hotel_details`, `get_tour_details`.\n"
            "4. Budget questions: `calculate_trip_cost` with ids from step 2-3.\n"
            "5. Policy questions: `search_travel_policies`.\n"
            "6. Bookings are SIMULATED: only call `create_sandbox_booking` after "
            "explicit user confirmation; explain that nothing real is reserved.\n\n"
            "All prices are per person per segment in Iranian Toman (IRT), sorted "
            "cheapest first. If `is_mock_data` is true, results are simulated demo "
            "data and must be presented as such.\n"
        )
