"""Hotel tools: search and details."""

from datetime import date

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from alibaba_mcp.domain.models import Hotel, HotelSearchResult
from alibaba_mcp.mcp.context import AppContext


def register(mcp: MCPServer, ctx: AppContext) -> None:
    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_hotels(
        city_id: str,
        check_in: date,
        check_out: date,
        guests: int = 2,
        min_stars: int = 1,
        max_results: int = 5,
    ) -> HotelSearchResult:
        """Search hotels in a city for a date range.

        Use this when the user asks for accommodation, hotels or places to
        stay. Rates are indicative per-night prices in Iranian Toman (IRT),
        sorted cheapest first. Read-only: nothing is reserved. When
        is_mock_data=true the results are simulated demo data.

        Args:
            city_id: City code (e.g. 'MHD' for Mashhad) — use search_cities first.
            check_in: Check-in date (ISO format YYYY-MM-DD; not in the past).
            check_out: Check-out date; must be after check_in.
            guests: Number of guests (1-8).
            min_stars: Minimum hotel star rating (1-5) to include.
            max_results: Maximum hotels to return (1-20).
        """
        return await ctx.call(
            "search_hotels",
            lambda: ctx.service.search_hotels(
                city_id, check_in, check_out, guests, min_stars, max_results
            ),
        )

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def get_hotel_details(hotel_id: str) -> Hotel:
        """Get full details for one hotel by its id.

        Use this after search_hotels to inspect a specific property (rating,
        amenities, cancellation terms). The id must come from search_hotels.
        Read-only.

        Args:
            hotel_id: Hotel id exactly as returned by search_hotels.
        """
        return await ctx.call("get_hotel_details", lambda: ctx.service.get_hotel_details(hotel_id))
