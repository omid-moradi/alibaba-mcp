"""Flight tools: airport discovery, flight search, flight details."""

from datetime import date

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from alibaba_mcp.domain.enums import CabinClass
from alibaba_mcp.domain.models import Airport, Flight, FlightSearchResult
from alibaba_mcp.mcp.context import AppContext


def register(mcp: MCPServer, ctx: AppContext) -> None:
    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_airports(query: str, limit: int = 10) -> list[Airport]:
        """Find airports by IATA code, airport name, or city name.

        Use this FIRST when you only know a city/place name (e.g. 'Tehran',
        'Mashhad', 'Istanbul') and need the IATA code required by flight tools.
        An empty query lists all supported airports. Read-only.

        Args:
            query: Free text matched against code, airport name or city name.
            limit: Maximum number of airports to return (1-20).
        """
        return await ctx.call(
            "search_airports", lambda: ctx.service.search_airports(query, limit)
        )

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_flights(
        origin: str,
        destination: str,
        departure_date: date,
        adults: int = 1,
        cabin_class: CabinClass = CabinClass.ECONOMY,
        max_results: int = 5,
    ) -> FlightSearchResult:
        """Search available flights between two airports on a departure date.

        Use this when the user wants flight options, prices, schedules or the
        cheapest flight for a route. Prices are per adult in Iranian Toman
        (IRT); results are sorted cheapest first. This operation is
        read-only: it never books or holds seats. When results carry
        is_mock_data=true, they are simulated demo data, NOT real inventory.

        Args:
            origin: IATA code of the origin airport (find it with search_airports).
            destination: IATA code of the destination airport.
            departure_date: Departure date (ISO format YYYY-MM-DD; not in the past).
            adults: Number of adult passengers (1-9).
            cabin_class: 'economy', 'business' or 'first'.
            max_results: Maximum options to return (1-20).
        """
        return await ctx.call(
            "search_flights",
            lambda: ctx.service.search_flights(
                origin, destination, departure_date, adults, cabin_class, max_results
            ),
        )

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def get_flight_details(flight_id: str) -> Flight:
        """Get full details for one flight by its id.

        Use this after search_flights when you need complete information about
        a specific option (exact times, baggage allowance, refundability).
        The id must come from search_flights — do not invent one. Read-only.

        Args:
            flight_id: Flight id exactly as returned by search_flights.
        """
        return await ctx.call(
            "get_flight_details", lambda: ctx.service.get_flight_details(flight_id)
        )


