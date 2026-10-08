"""Travel use-cases: orchestration above the provider seam.

MCP tools call this layer, never the provider directly. That keeps business
rules (comparisons, cost aggregation, sandbox booking policy) in one place
and lets providers stay pure data adapters.
"""

import asyncio
import math
from datetime import date

from alibaba_mcp.domain.enums import BookingItemKind, Currency, TravelMode
from alibaba_mcp.domain.models import (
    Airport,
    Booking,
    Bus,
    BusSearchResult,
    City,
    CostBreakdown,
    CostComponent,
    Flight,
    FlightSearchResult,
    Hotel,
    HotelSearchResult,
    Price,
    Tour,
    TourSearchResult,
    Train,
    TrainSearchResult,
    TrainStation,
    TravelOption,
    TravelOptionComparison,
)
from alibaba_mcp.domain.enums import CabinClass
from alibaba_mcp.providers.base import InvalidInputError, NotFoundError, TravelProvider

# A simulated platform service fee applied on top of inventory prices.
_SERVICE_FEE_RATE = 0.09


class TravelService:
    """Use-cases exposed to MCP tools."""

    def __init__(self, provider: TravelProvider) -> None:
        self._provider = provider

    @property
    def provider(self) -> TravelProvider:
        return self._provider

    # -- pass-through searches (kept explicit for clarity and typing) -----------
    async def search_airports(self, query: str, limit: int) -> list[Airport]:
        return await self._provider.search_airports(query, limit)

    async def search_cities(self, query: str, limit: int) -> list[City]:
        return await self._provider.search_cities(query, limit)

    async def search_train_stations(self, query: str, limit: int) -> list[TrainStation]:
        return await self._provider.search_train_stations(query, limit)

    async def search_flights(
        self, origin: str, destination: str, departure_date: date,
        adults: int, cabin_class: CabinClass, max_results: int,
    ) -> FlightSearchResult:
        return await self._provider.search_flights(
            origin, destination, departure_date, adults, cabin_class, max_results
        )

    async def get_flight_details(self, flight_id: str) -> Flight:
        return await self._provider.get_flight_details(flight_id)

    async def search_hotels(
        self, city_id: str, check_in: date, check_out: date,
        guests: int, min_stars: int, max_results: int,
    ) -> HotelSearchResult:
        return await self._provider.search_hotels(
            city_id, check_in, check_out, guests, min_stars, max_results
        )

    async def get_hotel_details(self, hotel_id: str) -> Hotel:
        return await self._provider.get_hotel_details(hotel_id)

    async def search_trains(
        self, origin: str, destination: str, departure_date: date, max_results: int
    ) -> TrainSearchResult:
        return await self._provider.search_trains(origin, destination, departure_date, max_results)

    async def get_train_details(self, train_id: str) -> Train:
        return await self._provider.get_train_details(train_id)

    async def search_buses(
        self, origin: str, destination: str, departure_date: date, max_results: int
    ) -> BusSearchResult:
        return await self._provider.search_buses(origin, destination, departure_date, max_results)

    async def get_bus_details(self, bus_id: str) -> Bus:
        return await self._provider.get_bus_details(bus_id)

    async def search_tours(self, destination: str | None, max_results: int) -> TourSearchResult:
        return await self._provider.search_tours(destination, max_results)

    async def get_tour_details(self, tour_id: str) -> Tour:
        return await self._provider.get_tour_details(tour_id)

    # -- composed use-cases ---------------------------------------------------
    async def compare_travel_options(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        max_per_mode: int = 5,
    ) -> TravelOptionComparison:
        """Find the cheapest and fastest option across flights, trains and buses.

        Modes that do not serve the requested pair (e.g. no rail service on a
        route) are skipped gracefully — a comparison is still returned for
        the remaining modes.
        """
        flight_opts, train_opts, bus_opts = await asyncio.gather(
            self._safe_flights(origin, destination, departure_date, max_per_mode),
            self._safe_trains(origin, destination, departure_date, max_per_mode),
            self._safe_buses(origin, destination, departure_date, max_per_mode),
        )
        options = [*flight_opts, *train_opts, *bus_opts]

        if not options:
            raise InvalidInputError(
                f"No travel options found between '{origin}' and '{destination}' on "
                f"{departure_date.isoformat()}. Use search_cities to check which "
                "modes serve these cities."
            )
        cheapest = min(options, key=lambda o: o.price.amount)
        fastest = min(options, key=lambda o: o.duration_minutes)
        return TravelOptionComparison(
            origin_code=origin.upper(),
            destination_code=destination.upper(),
            departure_date=departure_date,
            cheapest=cheapest,
            fastest=fastest,
            options=options,
            is_mock_data=self._provider.is_mock,
        )

    async def _safe_flights(
        self, origin: str, destination: str, departure_date: date, limit: int
    ) -> list[TravelOption]:
        try:
            result = await self._provider.search_flights(
                origin, destination, departure_date, max_results=limit
            )
        except (InvalidInputError, NotFoundError):
            return []
        return [
            TravelOption(
                mode=TravelMode.FLIGHT,
                option_id=f.id,
                title=f"{f.airline_name} {f.flight_number} ({f.cabin_class.value})",
                departure_time=f.departure_time,
                duration_minutes=f.duration_minutes,
                price=f.price,
                operator=f.airline_name,
            )
            for f in result.flights
        ]

    async def _safe_trains(
        self, origin: str, destination: str, departure_date: date, limit: int
    ) -> list[TravelOption]:
        try:
            result = await self._provider.search_trains(
                origin, destination, departure_date, max_results=limit
            )
        except (InvalidInputError, NotFoundError):
            return []
        return [
            TravelOption(
                mode=TravelMode.TRAIN,
                option_id=t.id,
                title=f"{t.operator} {t.train_number} ({t.seat_class.value})",
                departure_time=t.departure_time,
                duration_minutes=t.duration_minutes,
                price=t.price,
                operator=t.operator,
            )
            for t in result.trains
        ]

    async def _safe_buses(
        self, origin: str, destination: str, departure_date: date, limit: int
    ) -> list[TravelOption]:
        try:
            result = await self._provider.search_buses(
                origin, destination, departure_date, max_results=limit
            )
        except (InvalidInputError, NotFoundError):
            return []
        return [
            TravelOption(
                mode=TravelMode.BUS,
                option_id=b.id,
                title=f"{b.operator} {b.bus_type.value}",
                departure_time=b.departure_time,
                duration_minutes=b.duration_minutes,
                price=b.price,
                operator=b.operator,
            )
            for b in result.buses
        ]

    async def calculate_trip_cost(
        self,
        passengers: int,
        flight_id: str | None = None,
        train_id: str | None = None,
        bus_id: str | None = None,
        hotel_id: str | None = None,
        nights: int = 0,
        rooms: int = 1,
    ) -> CostBreakdown:
        """Itemize a trip total from selected inventory ids.

        At least one component (transport or hotel) must be provided.
        A simulated 9% platform service fee is added on top of the subtotal.
        """
        if not any([flight_id, train_id, bus_id, hotel_id]):
            raise InvalidInputError(
                "Provide at least one of flight_id, train_id, bus_id or hotel_id "
                "to calculate a trip cost."
            )
        transport_ids = [i for i in (flight_id, train_id, bus_id) if i]
        if len(transport_ids) > 1:
            raise InvalidInputError(
                "Provide at most one transport id: flight_id, train_id or bus_id."
            )
        components: list[CostComponent] = []
        subtotal = 0

        if flight_id:
            flight = await self._provider.get_flight_details(flight_id)
            amount = flight.price.amount * passengers
            components.append(CostComponent(
                label="Flight",
                price=Price(amount=amount, currency=Currency.IRT),
                detail=f"{flight.airline_name} {flight.flight_number} x {passengers} passenger(s)",
            ))
            subtotal += amount
        if train_id:
            train = await self._provider.get_train_details(train_id)
            amount = train.price.amount * passengers
            components.append(CostComponent(
                label="Train",
                price=Price(amount=amount, currency=Currency.IRT),
                detail=f"{train.operator} {train.train_number} x {passengers} passenger(s)",
            ))
            subtotal += amount
        if bus_id:
            bus = await self._provider.get_bus_details(bus_id)
            amount = bus.price.amount * passengers
            components.append(CostComponent(
                label="Bus",
                price=Price(amount=amount, currency=Currency.IRT),
                detail=f"{bus.operator} x {passengers} passenger(s)",
            ))
            subtotal += amount
        if hotel_id:
            if nights < 1:
                raise InvalidInputError("nights must be at least 1 when a hotel_id is given.")
            hotel = await self._provider.get_hotel_details(hotel_id)
            amount = hotel.price_per_night.amount * nights * rooms
            components.append(CostComponent(
                label="Hotel",
                price=Price(amount=amount, currency=Currency.IRT),
                detail=f"{hotel.name} ({hotel.room_type}) x {nights} night(s) x {rooms} room(s)",
            ))
            subtotal += amount

        fee = math.ceil(subtotal * _SERVICE_FEE_RATE / 10_000) * 10_000
        components.append(CostComponent(
            label="Platform service fee (simulated)",
            price=Price(amount=fee, currency=Currency.IRT),
            detail="9% of the subtotal; simulated for this demo server.",
        ))
        return CostBreakdown(
            components=components,
            total=Price(amount=subtotal + fee, currency=Currency.IRT),
            is_mock_data=self._provider.is_mock,
        )

    # -- sandbox bookings -------------------------------------------------------
    async def create_sandbox_booking(
        self, kind: BookingItemKind, item_id: str, passengers: int
    ) -> Booking:
        if not self._provider.supports_bookings:
            raise InvalidInputError(
                "The active provider does not support bookings (live-provider "
                "bookings are disabled by design — see SECURITY.md)."
            )
        return await self._provider.create_booking(kind, item_id, passengers)

    async def get_booking(self, booking_id: str) -> Booking:
        return await self._provider.get_booking(booking_id)

    async def cancel_booking(self, booking_id: str) -> Booking:
        return await self._provider.cancel_booking(booking_id)


__all__ = ["TravelService"]


