"""Unit tests for the deterministic MockProvider."""

from datetime import date, timedelta

import pytest

from alibaba_mcp.domain.enums import BookingItemKind
from alibaba_mcp.providers.base import InvalidInputError, NotFoundError
from alibaba_mcp.providers.mock import MockProvider

_TOMORROW = date.today() + timedelta(days=1)


@pytest.fixture
def provider() -> MockProvider:
    return MockProvider()


async def test_flight_search_is_deterministic(provider: MockProvider) -> None:
    r1 = await provider.search_flights("THR", "MHD", _TOMORROW)
    r2 = await provider.search_flights("THR", "MHD", _TOMORROW)
    assert [f.id for f in r1.flights] == [f.id for f in r2.flights]
    assert [f.price.amount for f in r1.flights] == [f.price.amount for f in r2.flights]


async def test_flights_sorted_cheapest_first(provider: MockProvider) -> None:
    result = await provider.search_flights("THR", "MHD", _TOMORROW)
    prices = [f.price.amount for f in result.flights]
    assert prices == sorted(prices)


async def test_flight_details_matches_search(provider: MockProvider) -> None:
    result = await provider.search_flights("THR", "MHD", _TOMORROW)
    for flight in result.flights:
        assert await provider.get_flight_details(flight.id) == flight


async def test_results_labeled_as_mock(provider: MockProvider) -> None:
    result = await provider.search_flights("THR", "MHD", _TOMORROW)
    assert result.is_mock_data is True
    assert provider.is_mock is True


async def test_unknown_airport_rejected(provider: MockProvider) -> None:
    with pytest.raises(InvalidInputError, match="Unknown airport code"):
        await provider.search_flights("XXX", "MHD", _TOMORROW)


async def test_same_origin_destination_rejected(provider: MockProvider) -> None:
    with pytest.raises(InvalidInputError, match="different airports"):
        await provider.search_flights("THR", "THR", _TOMORROW)


async def test_past_date_rejected(provider: MockProvider) -> None:
    with pytest.raises(InvalidInputError, match="in the past"):
        await provider.search_flights("THR", "MHD", date.today() - timedelta(days=1))


async def test_made_up_flight_id_rejected(provider: MockProvider) -> None:
    with pytest.raises(NotFoundError):
        await provider.get_flight_details("FLT-THR-MHD-20260101-999-economy")
    with pytest.raises(NotFoundError):
        await provider.get_flight_details("not-a-flight-id")


async def test_hotel_search_and_details(provider: MockProvider) -> None:
    result = await provider.search_hotels("MHD", _TOMORROW, _TOMORROW + timedelta(days=2))
    assert result.count > 0
    hotel = await provider.get_hotel_details(result.hotels[0].id)
    assert hotel == result.hotels[0]


async def test_hotel_city_without_inventory_rejected(provider: MockProvider) -> None:
    with pytest.raises(InvalidInputError, match="No hotel inventory"):
        await provider.search_hotels("RAS", _TOMORROW, _TOMORROW + timedelta(days=1))


async def test_train_requires_rail_city(provider: MockProvider) -> None:
    with pytest.raises(InvalidInputError, match="No train service"):
        await provider.search_trains("THR", "KIH", _TOMORROW)


async def test_bus_and_tour_search(provider: MockProvider) -> None:
    buses = await provider.search_buses("THR", "MHD", _TOMORROW)
    assert buses.count > 0
    tours = await provider.search_tours("Istanbul")
    assert tours.count > 0 and all(t.destination_city_id == "IST" for t in tours.tours)


async def test_booking_lifecycle(provider: MockProvider) -> None:
    flights = await provider.search_flights("THR", "MHD", _TOMORROW)
    booking = await provider.create_booking(BookingItemKind.FLIGHT, flights.flights[0].id, 2)
    assert booking.simulated is True
    assert booking.total_price.amount == flights.flights[0].price.amount * 2

    fetched = await provider.get_booking(booking.id)
    assert fetched.id == booking.id

    cancelled = await provider.cancel_booking(booking.id)
    assert cancelled.status.value == "cancelled"

    with pytest.raises(InvalidInputError, match="already cancelled"):
        await provider.cancel_booking(booking.id)


async def test_unknown_booking_rejected(provider: MockProvider) -> None:
    with pytest.raises(NotFoundError):
        await provider.get_booking("BKG-DOESNOTEXIST")
