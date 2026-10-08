"""End-to-end test: MCP client over stdio to a real server subprocess."""

from __future__ import annotations

import sys
from datetime import date, timedelta

from mcp import Client, StdioServerParameters


async def test_stdio_subprocess_end_to_end() -> None:
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    server = StdioServerParameters(command=sys.executable, args=["-m", "alibaba_mcp"])
    async with Client(server) as client:
        assert client.server_info is not None
        assert client.server_info.name == "Alibaba MCP"

        tools = {t.name for t in (await client.list_tools()).tools}
        assert "search_flights" in tools

        result = await client.call_tool(
            "search_flights",
            {"origin": "THR", "destination": "MHD", "departure_date": tomorrow},
        )
        assert not result.is_error
        data = result.structured_content
        assert data is not None and data["count"] > 0
        assert data["is_mock_data"] is True
