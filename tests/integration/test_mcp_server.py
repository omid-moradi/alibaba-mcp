"""MCP integration tests: the full protocol against the in-memory transport.

These exercise initialize, tools/list, tools/call (success + failure),
resources, prompts, structured output and the sandbox booking lifecycle —
through the MCP protocol, never by importing tool functions.
"""

from __future__ import annotations

from datetime import date, timedelta

from mcp import Client

from alibaba_mcp.server import create_server
from tests.conftest import make_test_settings

_TOMORROW = (date.today() + timedelta(days=1)).isoformat()

EXPECTED_TOOLS = {
    "search_airports",
    "search_flights",
    "get_flight_details",
    "search_hotels",
    "get_hotel_details",
    "search_cities",
    "search_train_stations",
    "search_trains",
    "get_train_details",
    "search_buses",
    "get_bus_details",
    "search_tours",
    "get_tour_details",
    "compare_travel_options",
    "calculate_trip_cost",
    "search_travel_policies",
    "create_sandbox_booking",
    "get_booking_status",
    "cancel_sandbox_booking",
}

EXPECTED_RESOURCES = {
    "alibaba://travel/policies",
    "alibaba://travel/cancellation-policy",
    "alibaba://travel/cities",
    "alibaba://travel/provider-status",
    "alibaba://travel/tool-guide",
}

EXPECTED_PROMPTS = {
    "travel_planner",
    "flight_comparison",
    "hotel_selection",
    "budget_trip_planner",
    "business_trip_planner",
}


async def test_initialization(client: Client) -> None:
    assert client.server_info is not None
    assert client.server_info.name == "Alibaba MCP"
    assert client.instructions is not None


async def test_tool_discovery_matches_surface(client: Client) -> None:
    page = await client.list_tools()
    names = {t.name for t in page.tools}
    assert names == EXPECTED_TOOLS
    # every tool must expose a description for LLM tool selection
    assert all(t.description for t in page.tools)


async def test_resource_and_prompt_discovery(client: Client) -> None:
    resources = {r.uri for r in (await client.list_resources()).resources}
    assert resources >= EXPECTED_RESOURCES
    prompts = {p.name for p in (await client.list_prompts()).prompts}
    assert prompts == EXPECTED_PROMPTS


async def test_search_flights_structured_output(client: Client) -> None:
    result = await client.call_tool(
        "search_flights",
        {
            "origin": "THR",
            "destination": "MHD",
            "departure_date": _TOMORROW,
        },
    )
    assert not result.is_error
    data = result.structured_content
    assert data is not None
    assert data["count"] > 0
    assert data["is_mock_data"] is True
    first = data["flights"][0]
    assert first["price"]["currency"] == "IRT"
    assert first["price"]["amount"] > 0
    assert "id" in first and "airline_name" in first


async def test_search_airports_resolves_city(client: Client) -> None:
    result = await client.call_tool("search_airports", {"query": "tehran"})
    assert not result.is_error
    # list-returning tools wrap structured output as {"result": [...]} (per spec)
    codes = [a["code"] for a in result.structured_content["result"]]
    assert "IKA" in codes and "THR" in codes


async def test_invalid_code_yields_model_readable_error(client: Client) -> None:
    result = await client.call_tool(
        "search_flights",
        {
            "origin": "XXX",
            "destination": "MHD",
            "departure_date": _TOMORROW,
        },
    )
    assert result.is_error
    message = result.content[0].text
    assert "Unknown airport code" in message
    assert "Known airport codes" in message  # actionable guidance for the model


async def test_schema_rejects_wrong_argument_type(client: Client) -> None:
    result = await client.call_tool(
        "search_flights",
        {
            "origin": "THR",
            "destination": "MHD",
            "departure_date": 12345,
        },
    )
    assert result.is_error


async def test_missing_required_argument(client: Client) -> None:
    result = await client.call_tool(
        "search_flights",
        {
            "origin": "THR",
            "departure_date": _TOMORROW,
        },
    )
    assert result.is_error


async def test_oversized_input_does_not_crash(client: Client) -> None:
    big = "a" * 100_000
    result = await client.call_tool("search_cities", {"query": big, "limit": 3})
    assert not result.is_error  # handled gracefully (empty result)
    assert result.structured_content["result"] == []


async def test_hotels_trains_buses_tours_round_trip(client: Client) -> None:
    hotels = await client.call_tool(
        "search_hotels",
        {
            "city_id": "MHD",
            "check_in": _TOMORROW,
            "check_out": (date.today() + timedelta(days=4)).isoformat(),
        },
    )
    assert hotels.structured_content["count"] > 0

    trains = await client.call_tool(
        "search_trains",
        {
            "origin": "THR",
            "destination": "MHD",
            "departure_date": _TOMORROW,
        },
    )
    assert trains.structured_content["count"] > 0

    buses = await client.call_tool(
        "search_buses",
        {
            "origin": "THR",
            "destination": "MHD",
            "departure_date": _TOMORROW,
        },
    )
    assert buses.structured_content["count"] > 0

    tours = await client.call_tool("search_tours", {"destination": "kish"})
    assert tours.structured_content["count"] > 0


async def test_compare_travel_options(client: Client) -> None:
    result = await client.call_tool(
        "compare_travel_options",
        {
            "origin": "THR",
            "destination": "MHD",
            "departure_date": _TOMORROW,
        },
    )
    data = result.structured_content
    assert not result.is_error
    assert data["cheapest"]["price"]["amount"] <= data["options"][0]["price"]["amount"]
    assert data["fastest"]["duration_minutes"] <= min(
        o["duration_minutes"] for o in data["options"]
    )


async def test_calculate_trip_cost(client: Client) -> None:
    flights = await client.call_tool(
        "search_flights",
        {
            "origin": "THR",
            "destination": "MHD",
            "departure_date": _TOMORROW,
        },
    )
    flight_id = flights.structured_content["flights"][0]["id"]
    result = await client.call_tool(
        "calculate_trip_cost",
        {
            "flight_id": flight_id,
            "passengers": 2,
        },
    )
    data = result.structured_content
    assert data["total"]["amount"] > 0
    assert data["is_mock_data"] is True


async def test_policy_search_and_resources(client: Client) -> None:
    result = await client.call_tool(
        "search_travel_policies",
        {
            "query": "baggage allowance",
        },
    )
    assert result.structured_content["result"][0]["topic"] == "baggage"

    status = await client.read_resource("alibaba://travel/provider-status")
    assert '"is_mock": true' in status.contents[0].text

    policies = await client.read_resource("alibaba://travel/cancellation-policy")
    assert "Cancellation policy" in policies.contents[0].text


async def test_prompt_rendering(client: Client) -> None:
    prompt = await client.get_prompt(
        "flight_comparison",
        {
            "origin": "IKA",
            "destination": "IST",
            "departure_date": _TOMORROW,
        },
    )
    assert prompt.messages[0].content.text.startswith("Find and compare flights")


async def test_sandbox_booking_lifecycle(client: Client) -> None:
    flights = await client.call_tool(
        "search_flights",
        {
            "origin": "THR",
            "destination": "MHD",
            "departure_date": _TOMORROW,
        },
    )
    flight_id = flights.structured_content["flights"][0]["id"]

    created = await client.call_tool(
        "create_sandbox_booking",
        {
            "item_kind": "flight",
            "item_id": flight_id,
            "passengers": 2,
        },
    )
    booking = created.structured_content
    assert booking["simulated"] is True
    assert booking["passengers"] == 2

    status = await client.call_tool("get_booking_status", {"booking_id": booking["id"]})
    assert status.structured_content["status"] == "confirmed"

    cancelled = await client.call_tool(
        "cancel_sandbox_booking",
        {
            "booking_id": booking["id"],
        },
    )
    assert cancelled.structured_content["status"] == "cancelled"

    repeat = await client.call_tool(
        "cancel_sandbox_booking",
        {
            "booking_id": booking["id"],
        },
    )
    assert repeat.is_error
    assert "already cancelled" in repeat.content[0].text


async def test_unknown_booking_id(client: Client) -> None:
    result = await client.call_tool("get_booking_status", {"booking_id": "BKG-NOPE"})
    assert result.is_error
    assert "BKG-NOPE" in result.content[0].text


async def test_rate_limit_enforced_over_protocol() -> None:
    server = create_server(make_test_settings(rate_limit_max_calls=3, rate_limit_window_seconds=60))
    async with Client(server, raise_exceptions=True) as c:
        for _ in range(3):
            result = await c.call_tool("search_cities", {"query": "tehran"})
            assert not result.is_error
        blocked = await c.call_tool("search_cities", {"query": "tehran"})
        assert blocked.is_error
        assert "Rate limit exceeded" in blocked.content[0].text
        # other tools remain unaffected (per-tool limits)
        ok = await c.call_tool("search_airports", {"query": ""})
        assert not ok.is_error
