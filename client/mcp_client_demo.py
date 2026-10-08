"""Alibaba MCP client demo.

A real MCP client: it speaks the MCP protocol (initialize, tools/list,
tools/call, resources/read, prompts/get) — it never imports server
functions directly.

Usage:
    uv run python client/mcp_client_demo.py                # launch server via stdio
    uv run python client/mcp_client_demo.py --url http://127.0.0.1:8000/mcp
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, timedelta

from mcp import Client, StdioServerParameters


def _print_block(title: str) -> None:
    print(f"\n=== {title} " + "=" * max(0, 60 - len(title)))


async def run_demo(client: Client) -> None:
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    _print_block("initialize")
    print(f"server_info : {client.server_info}")
    print(f"protocol    : {client.protocol_version}")
    print(f"instructions: {(client.instructions or '')[:80]}...")

    _print_block("tools/list")
    tools = (await client.list_tools()).tools
    print(f"{len(tools)} tools discovered:")
    for tool in tools:
        print(f"  - {tool.name}")

    _print_block("tools/call search_cities")
    result = await client.call_tool("search_cities", {"query": "mashhad"})
    print("structured:", result.structured_content)

    _print_block("tools/call search_flights")
    result = await client.call_tool(
        "search_flights",
        {"origin": "THR", "destination": "MHD", "departure_date": tomorrow},
    )
    data = result.structured_content
    assert data is not None
    print(f"{data['count']} flights found (is_mock_data={data['is_mock_data']})")
    for flight in data["flights"][:3]:
        print(
            f"  - {flight['airline_name']} {flight['flight_number']}: "
            f"{flight['price']['amount']:,} IRT, "
            f"{flight['duration_minutes']} min"
        )

    _print_block("tools/call compare_travel_options")
    result = await client.call_tool(
        "compare_travel_options",
        {"origin": "THR", "destination": "MHD", "departure_date": tomorrow},
    )
    data = result.structured_content
    assert data is not None
    print(f"cheapest: {data['cheapest']['title']} ({data['cheapest']['price']['amount']:,} IRT)")
    print(f"fastest : {data['fastest']['title']} ({data['fastest']['duration_minutes']} min)")

    _print_block("resources/read alibaba://travel/provider-status")
    resource_result = await client.read_resource("alibaba://travel/provider-status")
    print(resource_result.contents[0].text)

    _print_block("prompts/get flight_comparison")
    prompt = await client.get_prompt(
        "flight_comparison",
        {"origin": "IKA", "destination": "IST", "departure_date": tomorrow},
    )
    print(f"role={prompt.messages[0].role}: {prompt.messages[0].content.text[:120]}...")

    _print_block("done")


async def main_async(args: argparse.Namespace) -> int:
    if args.url:
        print(f"Connecting over Streamable HTTP to {args.url} ...")
        async with Client(args.url) as client:
            await run_demo(client)
    else:
        print("Launching Alibaba MCP as a stdio subprocess ...")
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "alibaba_mcp"],
        )
        async with Client(server) as client:
            await run_demo(client)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Alibaba MCP client demo")
    parser.add_argument(
        "--url",
        default=None,
        help="Connect to an already-running server over Streamable HTTP "
        "(e.g. http://127.0.0.1:8000/mcp). Default: launch via stdio.",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
