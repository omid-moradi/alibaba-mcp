"""Scratch check: MCP -> LangChain bridge discovers tools and forwards calls."""

import asyncio
import sys

from mcp import Client, StdioServerParameters


async def main() -> int:
    sys.path.insert(0, "client")
    from mcp_langchain_bridge import as_langchain_tools

    server = StdioServerParameters(command=sys.executable, args=["-m", "alibaba_mcp"])
    async with Client(server) as client:
        tools = await as_langchain_tools(client)
        names = [t.name for t in tools]
        print(f"bridged {len(tools)} tools")
        assert "search_flights" in names and "create_sandbox_booking" in names

        from datetime import date, timedelta

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = await tools[names.index("search_flights")].ainvoke(
            {"origin": "THR", "destination": "MHD", "departure_date": tomorrow}
        )
        print("search_flights via LangChain tool OK:", result[:100], "...")

        err = await tools[names.index("search_flights")].ainvoke(
            {"origin": "XXX", "destination": "MHD", "departure_date": tomorrow}
        )
        assert err.startswith("TOOL ERROR"), err[:80]
        print("error propagation via bridge OK")
    print("BRIDGE CHECKS PASSED")
    return 0


asyncio.run(main())
