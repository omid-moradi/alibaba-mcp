"""MCP prompts: reusable, user-selected conversation starters.

Why Prompts and not Tools: a prompt is a template the *user* picks from a
menu and fills in; it seeds the conversation with good instructions instead
of the model deciding to run something. Each prompt below is written to
steer the agent toward effective tool use of this server.
"""

from mcp.server import MCPServer
from mcp.server.mcpserver.prompts.base import AssistantMessage, Message, UserMessage

from alibaba_mcp.mcp.context import AppContext

_COMMON_RULES = (
    "Rules:\n"
    "- Resolve place names to codes with search_airports / search_cities first.\n"
    "- Present prices in Toman and say whether is_mock_data was true.\n"
    "- Be explicit that bookings, if any, are simulated.\n"
)


def register(mcp: MCPServer, ctx: AppContext) -> None:
    @mcp.prompt()
    def travel_planner(origin: str, destination: str, departure_date: str) -> list[Message]:
        """Plan a complete trip between two cities on a given date."""
        return [
            UserMessage(
                f"Plan a trip from {origin} to {destination} on {departure_date}. "
                "Find the best transport option, suggest accommodation for arrival, "
                "and give an estimated total cost."
            ),
            AssistantMessage(
                "I'll compare travel options first, then look for accommodation and "
                "calculate a total. " + _COMMON_RULES
            ),
        ]

    @mcp.prompt()
    def flight_comparison(origin: str, destination: str, departure_date: str) -> str:
        """Compare flight options between two airports on a given date."""
        return (
            f"Find and compare flights from {origin} to {destination} on "
            f"{departure_date}. Use search_airports to resolve the places, then "
            "search_flights. Summarize the cheapest and the fastest options with "
            "prices in Toman, and note whether the data is simulated. " + _COMMON_RULES
        )

    @mcp.prompt()
    def hotel_selection(city: str, check_in: str, check_out: str, guests: str) -> str:
        """Find and recommend hotels in a city for given dates."""
        return (
            f"Find hotels in {city} from {check_in} to {check_out} for {guests} "
            "guest(s). Use search_cities to resolve the city, then search_hotels. "
            "Recommend one budget and one comfort option and explain the trade-offs. "
            + _COMMON_RULES
        )

    @mcp.prompt()
    def budget_trip_planner(
        origin: str, destination: str, departure_date: str, budget_toman: str
    ) -> str:
        """Plan a trip that stays under a given budget in Toman."""
        return (
            f"Plan the cheapest reasonable trip from {origin} to {destination} on "
            f"{departure_date} with a total budget of {budget_toman} Toman. Use "
            "compare_travel_options, pick a low-cost accommodation, and verify the "
            "total with calculate_trip_cost before recommending it. If the budget is "
            "too small, say by how much. " + _COMMON_RULES
        )

    @mcp.prompt()
    def business_trip_planner(
        origin: str, destination: str, departure_date: str, days: str
    ) -> str:
        """Plan a time-efficient business trip (fastest options first)."""
        return (
            f"Plan a {days}-day business trip from {origin} to {destination} leaving "
            f"on {departure_date}. Optimize for time over price: use "
            "compare_travel_options and favor the fastest option, pick a well-rated "
            "hotel near the city center (4+ stars), and give a cost breakdown with "
            "calculate_trip_cost. " + _COMMON_RULES
        )
