"""Unit tests for the normalized domain models."""

import pytest
from pydantic import ValidationError

from alibaba_mcp.domain.enums import Currency, TicketType
from alibaba_mcp.domain.models import Booking, Flight, Hotel, Price


class TestPrice:
    def test_valid_price(self) -> None:
        price = Price(amount=1_500_000)
        assert price.amount == 1_500_000
        assert price.currency is Currency.IRT

    def test_negative_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Price(amount=-1)


class TestHotel:
    def test_stars_bounds_enforced(self) -> None:
        with pytest.raises(ValidationError):
            Hotel(
                id="HTL-THR-00",
                name="X",
                city_id="THR",
                stars=6,
                guest_rating=4.0,
                room_type="Double",
                amenities=[],
                price_per_night=Price(amount=1),
                free_cancellation=False,
            )

    def test_guest_rating_bounds_enforced(self) -> None:
        with pytest.raises(ValidationError):
            Hotel(
                id="HTL-THR-00",
                name="X",
                city_id="THR",
                stars=4,
                guest_rating=5.5,
                room_type="Double",
                amenities=[],
                price_per_night=Price(amount=1),
                free_cancellation=False,
            )


class TestFlight:
    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Flight(
                id="FLT-THR-MHD-20260101-000-economy",
                origin_code="THR",
                destination_code="MHD",
                departure_time="2026-01-01T08:00:00+03:30",
                arrival_time="2026-01-01T09:30:00+03:30",
                duration_minutes=90,
                airline_code="IR",
                airline_name="IranAir",
                flight_number="IR452",
                cabin_class="economy",
                ticket_type="system",
                seats_available=5,
                baggage_allowance_kg=20,
                price=Price(amount=1),
                refundable=True,
                sneaky_field="leaked upstream data",  # must be forbidden
            )


class TestBooking:
    def test_bookings_are_always_simulated(self) -> None:
        booking = Booking(
            id="BKG-TEST",
            kind="flight",
            item_id="FLT-1",
            status="confirmed",
            passengers=1,
            total_price=Price(amount=1),
            created_at="2026-01-01T00:00:00+00:00",
        )
        assert booking.simulated is True


def test_ticket_type_enum_values() -> None:
    assert TicketType.CHARTER.value == "charter"
    assert TicketType.SYSTEM.value == "system"
