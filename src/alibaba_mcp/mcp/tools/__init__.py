"""MCP tool registration."""

from mcp.server import MCPServer

from alibaba_mcp.mcp.context import AppContext
from alibaba_mcp.mcp.tools import bookings, flights, ground, hotels, planning, tours


def register_all(mcp: MCPServer, ctx: AppContext) -> None:
    """Register every tool module onto the server."""
    flights.register(mcp, ctx)
    hotels.register(mcp, ctx)
    ground.register(mcp, ctx)
    tours.register(mcp, ctx)
    planning.register(mcp, ctx)
    bookings.register(mcp, ctx)
