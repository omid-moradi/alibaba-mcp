"""Scratch smoke check for the assembled MCP server (not part of the test suite)."""

import asyncio
from datetime import date, timedelta

from mcp import Client


async def main() -> None:
    from alibaba_mcp.server import mcp

    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    async with Client(mcp, raise_exceptions=True) as client:
        print("server_info:", client.server_info)
        tools = (await client.list_tools()).tools
        resources = (await client.list_resources()).resources
        prompts = (await client.list_prompts()).prompts
        print(f"tools: {len(tools)} -> {[t.name for t in tools]}")
        print(f"resources: {len(resources)}")
        print(f"prompts: {len(prompts)}")

        r = await client.call_tool(
            "search_flights",
            {"origin": "THR", "destination": "MHD", "departure_date": tomorrow},
        )
        assert not r.is_error, r.content
        data = r.structured_content
        print("search_flights:", data["count"], "flights; mock:", data["is_mock_data"])

        bad = await client.call_tool(
            "search_flights",
            {"origin": "XXX", "destination": "MHD", "departure_date": tomorrow},
        )
        assert bad.is_error, "expected error for unknown airport"
        print("error handling OK:", bad.content[0].text[:80], "...")

        res = await client.read_resource("alibaba://travel/provider-status")
        print("provider-status resource OK")

        p = await client.get_prompt("flight_comparison", {
            "origin": "IKA", "destination": "IST", "departure_date": tomorrow,
        })
        print("prompt OK:", p.messages[0].content.text[:60], "...")

    print("ALL MCP SMOKE CHECKS PASSED")


asyncio.run(main())
