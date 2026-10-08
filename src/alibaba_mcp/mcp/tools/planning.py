"""Planning tools: multi-modal comparison, trip cost breakdown, policy search."""

from datetime import date

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from alibaba_mcp.application.policies import search_policies
from alibaba_mcp.domain.models import CostBreakdown, TravelOptionComparison
from alibaba_mcp.mcp.context import AppContext


def register(mcp: MCPServer, ctx: AppContext) -> None:
    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def compare_travel_options(
        origin: str,
        destination: str,
        departure_date: date,
        max_per_mode: int = 5,
    ) -> TravelOptionComparison:
        """Compare flight, train and bus options between two cities on one date.

        Use this when the user asks which option is cheapest, fastest, or
        'compare travel options'. It searches all three modes at once, skips
        modes that do not serve the route, and highlights the overall
        cheapest and fastest option. Read-only. When is_mock_data=true the
        results are simulated demo data.

        Args:
            origin: Origin city/airport code, e.g. 'THR' (use search_cities first).
            destination: Destination city/airport code.
            departure_date: Departure date (ISO format YYYY-MM-DD; not in the past).
            max_per_mode: Maximum options per travel mode (1-10).
        """
        return await ctx.call(
            "compare_travel_options",
            lambda: ctx.service.compare_travel_options(
                origin, destination, departure_date, max_per_mode
            ),
        )

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def calculate_trip_cost(
        passengers: int = 1,
        flight_id: str | None = None,
        train_id: str | None = None,
        bus_id: str | None = None,
        hotel_id: str | None = None,
        nights: int = 0,
        rooms: int = 1,
    ) -> CostBreakdown:
        """Calculate an itemized total trip cost from selected option ids.

        Use this when the user has picked specific options (e.g. 'what would
        this flight plus 3 hotel nights cost for 2 people?'). Provide ids
        exactly as returned by the search tools — at most one transport id
        (flight, train OR bus) plus optionally one hotel id. Prices are in
        Iranian Toman (IRT). Read-only; a simulated 9% service fee is added.
        When is_mock_data=true the calculation uses simulated demo prices.

        Args:
            passengers: Number of travelers (1-9).
            flight_id: Flight id from search_flights, if pricing a flight.
            train_id: Train id from search_trains, if pricing a train trip.
            bus_id: Bus id from search_buses, if pricing a bus trip.
            hotel_id: Hotel id from search_hotels, if pricing accommodation.
            nights: Number of hotel nights (required with hotel_id, 1-30).
            rooms: Number of hotel rooms (1-4).
        """
        return await ctx.call(
            "calculate_trip_cost",
            lambda: ctx.service.calculate_trip_cost(
                passengers, flight_id, train_id, bus_id, hotel_id, nights, rooms
            ),
        )

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_travel_policies(query: str, limit: int = 3) -> list[dict[str, str]]:
        """Search the server's travel policy knowledge base by keyword.

        Use this for policy questions such as cancellation rules, refund
        timing, baggage allowance, check-in guidance or child fares. Returns
        the most relevant policy documents (topic, title, text). NOTE: these
        are generic educational policy texts written for this demo project —
        they are NOT official Alibaba.ir policies. Read-only.

        Args:
            query: Keywords or a question, e.g. 'cancellation rules' or
                'how much baggage is included'.
            limit: Maximum policy documents to return (1-5).
        """
        ctx.check_rate_limit("search_travel_policies")
        entries = search_policies(query, limit)
        return [{"topic": e.topic, "title": e.title, "text": e.text} for e in entries]
