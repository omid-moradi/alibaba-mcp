"""Scratch smoke check for the MockProvider (not part of the test suite)."""

import asyncio
from datetime import date, timedelta

from alibaba_mcp.domain.enums import BookingItemKind
from alibaba_mcp.providers.mock import MockProvider


async def main() -> None:
    p = MockProvider()
    tomorrow = date.today() + timedelta(days=1)

    r1 = await p.search_flights("THR", "MHD", tomorrow)
    r2 = await p.search_flights("THR", "MHD", tomorrow)
    assert [f.id for f in r1.flights] == [f.id for f in r2.flights], "not deterministic"
    print("flights:", r1.count, "cheapest:", r1.flights[0].price.amount, r1.flights[0].id)

    d = await p.get_flight_details(r1.flights[0].id)
    assert d == r1.flights[0], "details mismatch"

    h = await p.search_hotels("MHD", tomorrow, tomorrow + timedelta(days=3))
    print("hotels:", h.count, h.hotels[0].name)

    t = await p.search_trains("THR", "MHD", tomorrow)
    b = await p.search_buses("THR", "MHD", tomorrow)
    tours = await p.search_tours("ist")
    print("trains:", t.count, "buses:", b.count, "tours:", tours.count)

    bk = await p.create_booking(BookingItemKind.FLIGHT, r1.flights[0].id, 2)
    print("booking:", bk.id, bk.status.value, bk.total_price.amount)
    cb = await p.cancel_booking(bk.id)
    print("cancelled:", cb.status.value)

    print("ALL MOCK PROVIDER CHECKS PASSED")


asyncio.run(main())
