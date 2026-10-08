"""Tour tools: search and details."""

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from alibaba_mcp.domain.models import Tour, TourSearchResult
from alibaba_mcp.mcp.context import AppContext


def register(mcp: MCPServer, ctx: AppContext) -> None:
    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_tours(
        destination: str | None = None, max_results: int = 6
    ) -> TourSearchResult:
        """Search packaged tour products, optionally filtered by destination.

        Use this when the user asks about tour packages or wants a bundled
        trip. Prices are per person in Iranian Toman (IRT), cheapest first.
        Read-only. When is_mock_data=true the results are simulated demo data.

        Args:
            destination: Optional destination filter — city code, city name
                or Persian name (e.g. 'ist', 'Istanbul'). Omit to list all tours.
            max_results: Maximum tours to return (1-20).
        """
        return await ctx.call(
            "search_tours", lambda: ctx.service.search_tours(destination, max_results)
        )

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def get_tour_details(tour_id: str) -> Tour:
        """Get full details for one tour by its id.

        The id must come from search_tours — do not invent one. Read-only.

        Args:
            tour_id: Tour id exactly as returned by search_tours.
        """
        return await ctx.call(
            "get_tour_details", lambda: ctx.service.get_tour_details(tour_id)
        )
