"""Ground transport tools: cities, train stations, trains and buses."""

from datetime import date

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from alibaba_mcp.domain.models import (
    Bus,
    BusSearchResult,
    City,
    Train,
    TrainSearchResult,
    TrainStation,
)
from alibaba_mcp.mcp.context import AppContext


def register(mcp: MCPServer, ctx: AppContext) -> None:
    # -- discovery -------------------------------------------------------------
    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_cities(query: str, limit: int = 10) -> list[City]:
        """Find supported cities by code, English name, or Persian name.

        Use this FIRST when a place name is ambiguous or when you need to know
        which travel modes (airport / train / bus) serve a city. An empty
        query lists all supported cities. Read-only.

        Args:
            query: Free text matched against city code, English or Persian name.
            limit: Maximum number of cities to return (1-20).
        """
        return await ctx.call("search_cities", lambda: ctx.service.search_cities(query, limit))

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_train_stations(query: str, limit: int = 10) -> list[TrainStation]:
        """Find railway stations by code or name.

        Use this to resolve a city to its station code before searching
        trains. An empty query lists all supported stations. Read-only.

        Args:
            query: Free text matched against station code or name.
            limit: Maximum number of stations to return (1-20).
        """
        return await ctx.call(
            "search_train_stations",
            lambda: ctx.service.search_train_stations(query, limit),
        )

    # -- trains -------------------------------------------------------------------
    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_trains(
        origin: str,
        destination: str,
        departure_date: date,
        max_results: int = 5,
    ) -> TrainSearchResult:
        """Search intercity trains between two cities on a departure date.

        Use this for rail travel requests (often cheaper than flights).
        Prices are per passenger in Iranian Toman (IRT), cheapest first.
        Read-only: nothing is reserved. When is_mock_data=true the results
        are simulated demo data.

        Args:
            origin: Origin city code, e.g. 'THR' (use search_cities first).
            destination: Destination city code.
            departure_date: Departure date (ISO format YYYY-MM-DD; not in the past).
            max_results: Maximum options to return (1-20).
        """
        return await ctx.call(
            "search_trains",
            lambda: ctx.service.search_trains(origin, destination, departure_date, max_results),
        )

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def get_train_details(train_id: str) -> Train:
        """Get full details for one train by its id.

        The id must come from search_trains — do not invent one. Read-only.

        Args:
            train_id: Train id exactly as returned by search_trains.
        """
        return await ctx.call("get_train_details", lambda: ctx.service.get_train_details(train_id))

    # -- buses -----------------------------------------------------------------------
    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search_buses(
        origin: str,
        destination: str,
        departure_date: date,
        max_results: int = 5,
    ) -> BusSearchResult:
        """Search intercity buses between two cities on a departure date.

        Use this for low-budget road travel. Prices are per passenger in
        Iranian Toman (IRT), cheapest first. Read-only. When is_mock_data=true
        the results are simulated demo data.

        Args:
            origin: Origin city code, e.g. 'THR' (use search_cities first).
            destination: Destination city code.
            departure_date: Departure date (ISO format YYYY-MM-DD; not in the past).
            max_results: Maximum options to return (1-20).
        """
        return await ctx.call(
            "search_buses",
            lambda: ctx.service.search_buses(origin, destination, departure_date, max_results),
        )

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def get_bus_details(bus_id: str) -> Bus:
        """Get full details for one bus trip by its id.

        The id must come from search_buses — do not invent one. Read-only.

        Args:
            bus_id: Bus id exactly as returned by search_buses.
        """
        return await ctx.call("get_bus_details", lambda: ctx.service.get_bus_details(bus_id))
