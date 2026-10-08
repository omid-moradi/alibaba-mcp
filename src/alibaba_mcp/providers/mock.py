"""Deterministic MockProvider.

Serves clearly-labeled synthetic travel inventory for offline development,
CI, demos and the MCP Inspector. Results are fully deterministic: the same
query always yields the same results, and item ids encode enough
information for ``get_*_details`` to regenerate the identical object.
This makes the provider stateless and reproducible.
"""

import hashlib
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from alibaba_mcp.domain.enums import (
    BookingItemKind,
    BookingStatus,
    BusType,
    CabinClass,
    Currency,
    SeatClass,
    TicketType,
)
from alibaba_mcp.domain.models import (
    Airport,
    Booking,
    Bus,
    BusSearchResult,
    City,
    Flight,
    FlightSearchResult,
    Hotel,
    HotelSearchResult,
    Price,
    ProviderInfo,
    Tour,
    TourSearchResult,
    Train,
    TrainSearchResult,
    TrainStation,
)
from alibaba_mcp.providers import mock_data as md
from alibaba_mcp.providers.base import InvalidInputError, NotFoundError

_TEHRAN = ZoneInfo("Asia/Tehran")
_MAX_RESULTS_CAP = 20


def _digest(*parts: str) -> int:
    """Stable 64-bit digest of the given key parts."""
    key = "|".join(parts).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(), "big")


def _round_toman(value: float) -> int:
    """Round to a realistic price point (nearest 10,000 Toman)."""
    return max(10_000, int(round(value / 10_000.0)) * 10_000)


def _local_datetime(day: date, hour: int, minute: int) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=_TEHRAN)


class MockProvider:
    """In-memory, deterministic travel provider. All data is simulated."""

    def __init__(self) -> None:
        # Sandbox bookings live only for the lifetime of the process.
        self._bookings: dict[str, Booking] = {}

    # -- identity ------------------------------------------------------------
    @property
    def name(self) -> str:
        return "mock"

    @property
    def is_mock(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return (
            "Deterministic offline provider with synthetic (mock) travel data. "
            "Results are clearly labeled as mock and are NOT real Alibaba.ir data."
        )

    @property
    def supports_bookings(self) -> bool:
        return True  # sandbox only

    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            mode="mock",
            is_mock=True,
            description=self.description,
            supported_products=["flights", "hotels", "trains", "buses", "tours",
                                 "sandbox-bookings"],
        )

    # -- validation helpers ----------------------------------------------------
    @staticmethod
    def _cap(limit: int) -> int:
        return max(1, min(limit, _MAX_RESULTS_CAP))

    @staticmethod
    def _ensure_not_past(day: date) -> None:
        today = datetime.now(_TEHRAN).date()
        if day < today:
            raise InvalidInputError(
                f"Departure date {day.isoformat()} is in the past "
                f"(today is {today.isoformat()} in Asia/Tehran). Use a date from today onwards."
            )

    @staticmethod
    def _require_airport(code: str) -> Airport:
        airport = md.AIRPORT_BY_CODE.get(code.upper())
        if airport is None:
            available = ", ".join(sorted(md.AIRPORT_BY_CODE))
            raise InvalidInputError(
                f"Unknown airport code {code!r}. Known airport codes: {available}."
            )
        return airport

    @staticmethod
    def _require_train_city(code: str) -> City:
        city = md.CITY_BY_ID.get(code.upper())
        if city is None or not city.has_train:
            raise InvalidInputError(
                f"No train service for {code!r}. Known rail cities: "
                + ", ".join(c.id for c in md.CITIES if c.has_train) + "."
            )
        return city

    @staticmethod
    def _require_bus_city(code: str) -> City:
        city = md.CITY_BY_ID.get(code.upper())
        if city is None or not city.has_bus:
            raise InvalidInputError(
                f"No bus service for {code!r}. Known bus cities: "
                + ", ".join(c.id for c in md.CITIES if c.has_bus) + "."
            )
        return city

    @staticmethod
    def _require_hotel_city(city_id: str) -> str:
        city = city_id.upper()
        if city not in md.HOTELS:
            raise InvalidInputError(
                f"No hotel inventory for city {city_id!r}. Cities with hotels: "
                + ", ".join(sorted(md.HOTELS)) + "."
            )
        return city

    # -- reference data -----------------------------------------------------------
    async def search_airports(self, query: str, limit: int = 10) -> list[Airport]:
        needle = query.strip().lower()
        matches = [
            a for a in md.AIRPORTS
            if not needle
            or needle in a.code.lower()
            or needle in a.name.lower()
            or needle in md.CITY_BY_ID[a.city_id].name.lower()
        ]
        return matches[: self._cap(limit)]

    async def search_cities(self, query: str, limit: int = 10) -> list[City]:
        needle = query.strip().lower()
        matches = [
            c for c in md.CITIES
            if not needle
            or needle in c.id.lower()
            or needle in c.name.lower()
            or needle in c.name_fa
        ]
        return matches[: self._cap(limit)]

    async def search_train_stations(self, query: str, limit: int = 10) -> list[TrainStation]:
        needle = query.strip().lower()
        matches = [
            s for s in md.TRAIN_STATIONS
            if not needle
            or needle in s.code.lower()
            or needle in s.name.lower()
        ]
        return matches[: self._cap(limit)]

    # -- flights -------------------------------------------------------------------
    def _build_flight(
        self, origin: str, destination: str, departure: date, seq: int, cabin: CabinClass
    ) -> Flight:
        d = _digest("flight", origin, destination, departure.isoformat(), str(seq), cabin.value)
        airline_code, airline_name = md.AIRLINES[d % len(md.AIRLINES)]
        duration = md.FLIGHT_DURATION_MINUTES.get(
            (origin, destination), 70 + d % 150
        ) + (d % 11)
        base_fare = md.FLIGHT_BASE_FARE_TOMAN.get((origin, destination), 2_000_000)
        cabin_multiplier = {CabinClass.ECONOMY: 1.0, CabinClass.BUSINESS: 2.5,
                            CabinClass.FIRST: 4.0}[cabin]
        price = _round_toman(base_fare * cabin_multiplier + (d % 40) * 50_000)
        hour = 6 + (d // 4096) % 17
        minute = ((d // 64) % 4) * 15
        departure_time = _local_datetime(departure, hour, minute)
        is_charter = d % 5 == 0
        return Flight(
            id=self._flight_id(origin, destination, departure, seq, cabin),
            origin_code=origin,
            destination_code=destination,
            departure_time=departure_time,
            arrival_time=departure_time + timedelta(minutes=duration),
            duration_minutes=duration,
            airline_code=airline_code,
            airline_name=airline_name,
            flight_number=f"{airline_code}{100 + d % 800}",
            cabin_class=cabin,
            ticket_type=TicketType.CHARTER if is_charter else TicketType.SYSTEM,
            seats_available=(d % 40) + 1,
            baggage_allowance_kg=15 if is_charter else 20 + (d % 3) * 5,
            price=Price(amount=price, currency=Currency.IRT),
            refundable=not is_charter and d % 3 != 0,
        )

    @staticmethod
    def _flight_id(
        origin: str, destination: str, departure: date, seq: int, cabin: CabinClass
    ) -> str:
        return f"FLT-{origin}-{destination}-{departure.strftime('%Y%m%d')}-{seq:03d}-{cabin.value}"

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        adults: int = 1,
        cabin_class: CabinClass = CabinClass.ECONOMY,
        max_results: int = 10,
    ) -> FlightSearchResult:
        org = self._require_airport(origin)
        dst = self._require_airport(destination)
        if org.code == dst.code:
            raise InvalidInputError("Origin and destination must be different airports.")
        self._ensure_not_past(departure_date)
        total = 4 + _digest("flight-count", origin, destination,
                            departure_date.isoformat()) % 5
        flights = [
            self._build_flight(org.code, dst.code, departure_date, i, cabin_class)
            for i in range(total)
        ]
        flights.sort(key=lambda f: f.price.amount)
        return FlightSearchResult(
            origin_code=org.code,
            destination_code=dst.code,
            departure_date=departure_date,
            count=len(flights[: self._cap(max_results)]),
            flights=flights[: self._cap(max_results)],
            is_mock_data=True,
        )

    async def get_flight_details(self, flight_id: str) -> Flight:
        parts = flight_id.strip().split("-")
        if len(parts) != 6 or parts[0] != "FLT":
            raise NotFoundError(
                f"'{flight_id}' is not a valid flight id. Use an id returned by search_flights."
            )
        try:
            org = self._require_airport(parts[1])
            dst = self._require_airport(parts[2])
            departure = datetime.strptime(parts[3], "%Y%m%d").date()
            seq = int(parts[4])
            cabin = CabinClass(parts[5])
        except (ValueError, InvalidInputError) as exc:
            raise NotFoundError(
                f"'{flight_id}' does not reference a known flight. "
                "Use an id returned by search_flights."
            ) from exc
        return self._build_flight(org.code, dst.code, departure, seq, cabin)

    # -- hotels -----------------------------------------------------------------------
    def _build_hotel(self, city_id: str, index: int) -> Hotel:
        name, stars, rating, room_type, amenities, base_price = md.HOTELS[city_id][index]
        d = _digest("hotel", city_id, name)
        return Hotel(
            id=f"HTL-{city_id}-{index:02d}",
            name=name,
            city_id=city_id,
            stars=stars,
            guest_rating=rating,
            room_type=room_type,
            amenities=amenities,
            price_per_night=Price(
                amount=_round_toman(base_price + (d % 10) * 50_000),
                currency=Currency.IRT,
            ),
            free_cancellation=stars >= 4 and d % 2 == 0,
        )

    async def search_hotels(
        self,
        city_id: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        min_stars: int = 1,
        max_results: int = 10,
    ) -> HotelSearchResult:
        city = self._require_hotel_city(city_id)
        if check_out <= check_in:
            raise InvalidInputError(
                f"Check-out ({check_out.isoformat()}) must be at least one day "
                f"after check-in ({check_in.isoformat()})."
            )
        self._ensure_not_past(check_in)
        hotels = [self._build_hotel(city, i) for i in range(len(md.HOTELS[city]))]
        hotels = [h for h in hotels if h.stars >= min_stars]
        hotels.sort(key=lambda h: h.price_per_night.amount)
        return HotelSearchResult(
            city_id=city,
            check_in=check_in,
            check_out=check_out,
            count=len(hotels[: self._cap(max_results)]),
            hotels=hotels[: self._cap(max_results)],
            is_mock_data=True,
        )

    async def get_hotel_details(self, hotel_id: str) -> Hotel:
        parts = hotel_id.strip().split("-")
        if len(parts) != 3 or parts[0] != "HTL":
            raise NotFoundError(
                f"'{hotel_id}' is not a valid hotel id. Use an id returned by search_hotels."
            )
        city = parts[1]
        if city not in md.HOTELS:
            raise NotFoundError(
                f"'{hotel_id}' does not reference a known hotel. "
                "Use an id returned by search_hotels."
            )
        try:
            index = int(parts[2])
        except ValueError as exc:
            raise NotFoundError(f"'{hotel_id}' does not reference a known hotel.") from exc
        if index >= len(md.HOTELS[city]):
            raise NotFoundError(
                f"'{hotel_id}' does not reference a known hotel. "
                "Use an id returned by search_hotels."
            )
        return self._build_hotel(city, index)

    # -- trains -------------------------------------------------------------------------
    def _build_train(
        self, origin: str, destination: str, departure: date, seq: int
    ) -> Train:
        d = _digest("train", origin, destination, departure.isoformat(), str(seq))
        operator = md.TRAIN_OPERATORS[d % len(md.TRAIN_OPERATORS)]
        duration = md.TRAIN_DURATION_MINUTES.get(
            (origin, destination), 300 + d % 400
        ) + (d % 7) * 5
        base_fare = md.TRAIN_BASE_FARE_TOMAN.get((origin, destination), 300_000)
        price = _round_toman(base_fare + (d % 30) * 20_000)
        hour = 7 + (d // 2048) % 12
        minute = ((d // 16) % 4) * 15
        departure_time = _local_datetime(departure, hour, minute)
        return Train(
            id=f"TRN-{origin}-{destination}-{departure.strftime('%Y%m%d')}-{seq:03d}",
            origin_code=origin,
            destination_code=destination,
            departure_time=departure_time,
            arrival_time=departure_time + timedelta(minutes=duration),
            duration_minutes=duration,
            operator=operator,
            train_number=f"{100 + d % 500}",
            seat_class=md.TRAIN_SEAT_CLASSES[d % len(md.TRAIN_SEAT_CLASSES)],
            seats_available=(d % 30) + 1,
            price=Price(amount=price, currency=Currency.IRT),
        )

    async def search_trains(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        max_results: int = 10,
    ) -> TrainSearchResult:
        org = self._require_train_city(origin)
        dst = self._require_train_city(destination)
        if org.id == dst.id:
            raise InvalidInputError("Origin and destination must be different cities.")
        self._ensure_not_past(departure_date)
        total = 3 + _digest("train-count", org.id, dst.id,
                            departure_date.isoformat()) % 4
        trains = [self._build_train(org.id, dst.id, departure_date, i) for i in range(total)]
        trains.sort(key=lambda t: t.price.amount)
        return TrainSearchResult(
            origin_code=org.id,
            destination_code=dst.id,
            departure_date=departure_date,
            count=len(trains[: self._cap(max_results)]),
            trains=trains[: self._cap(max_results)],
            is_mock_data=True,
        )

    async def get_train_details(self, train_id: str) -> Train:
        parts = train_id.strip().split("-")
        if len(parts) != 5 or parts[0] != "TRN":
            raise NotFoundError(
                f"'{train_id}' is not a valid train id. Use an id returned by search_trains."
            )
        try:
            org = self._require_train_city(parts[1])
            dst = self._require_train_city(parts[2])
            departure = datetime.strptime(parts[3], "%Y%m%d").date()
            seq = int(parts[4])
        except (ValueError, InvalidInputError) as exc:
            raise NotFoundError(
                f"'{train_id}' does not reference a known train. "
                "Use an id returned by search_trains."
            ) from exc
        return self._build_train(org.id, dst.id, departure, seq)

    # -- buses ----------------------------------------------------------------------------
    def _build_bus(self, origin: str, destination: str, departure: date, seq: int) -> Bus:
        d = _digest("bus", origin, destination, departure.isoformat(), str(seq))
        operator = md.BUS_OPERATORS[d % len(md.BUS_OPERATORS)]
        duration = md.BUS_DURATION_MINUTES.get(
            (origin, destination), 300 + d % 400
        ) + (d % 9) * 10
        base_fare = md.BUS_BASE_FARE_TOMAN.get((origin, destination), 250_000)
        bus_type = md.BUS_TYPES[d % len(md.BUS_TYPES)]
        price = _round_toman(base_fare * (1.4 if bus_type == BusType.VIP else 1.0)
                             + (d % 20) * 10_000)
        hour = 6 + (d // 4096) % 16
        minute = ((d // 32) % 4) * 15
        departure_time = _local_datetime(departure, hour, minute)
        return Bus(
            id=f"BUS-{origin}-{destination}-{departure.strftime('%Y%m%d')}-{seq:03d}",
            origin_code=origin,
            destination_code=destination,
            departure_time=departure_time,
            arrival_time=departure_time + timedelta(minutes=duration),
            duration_minutes=duration,
            operator=operator,
            bus_type=bus_type,
            seats_available=(d % 44) + 1,
            price=Price(amount=price, currency=Currency.IRT),
        )

    async def search_buses(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        max_results: int = 10,
    ) -> BusSearchResult:
        org = self._require_bus_city(origin)
        dst = self._require_bus_city(destination)
        if org.id == dst.id:
            raise InvalidInputError("Origin and destination must be different cities.")
        self._ensure_not_past(departure_date)
        total = 3 + _digest("bus-count", org.id, dst.id,
                            departure_date.isoformat()) % 4
        buses = [self._build_bus(org.id, dst.id, departure_date, i) for i in range(total)]
        buses.sort(key=lambda b: b.price.amount)
        return BusSearchResult(
            origin_code=org.id,
            destination_code=dst.id,
            departure_date=departure_date,
            count=len(buses[: self._cap(max_results)]),
            buses=buses[: self._cap(max_results)],
            is_mock_data=True,
        )

    async def get_bus_details(self, bus_id: str) -> Bus:
        parts = bus_id.strip().split("-")
        if len(parts) != 5 or parts[0] != "BUS":
            raise NotFoundError(
                f"'{bus_id}' is not a valid bus id. Use an id returned by search_buses."
            )
        try:
            org = self._require_bus_city(parts[1])
            dst = self._require_bus_city(parts[2])
            departure = datetime.strptime(parts[3], "%Y%m%d").date()
            seq = int(parts[4])
        except (ValueError, InvalidInputError) as exc:
            raise NotFoundError(
                f"'{bus_id}' does not reference a known bus. "
                "Use an id returned by search_buses."
            ) from exc
        return self._build_bus(org.id, dst.id, departure, seq)

    # -- tours ---------------------------------------------------------------------------
    def _build_tour(self, index: int) -> Tour:
        title, dest, origin, days, price, inclusions, international = md.TOURS[index]
        d = _digest("tour", title)
        return Tour(
            id=f"TR-{index:03d}",
            title=title,
            destination_city_id=dest,
            origin_city_id=origin,
            duration_days=days,
            price_per_person=Price(
                amount=_round_toman(price + (d % 10) * 100_000),
                currency=Currency.IRT,
            ),
            inclusions=inclusions,
            is_international=international,
        )

    async def search_tours(
        self, destination: str | None = None, max_results: int = 10
    ) -> TourSearchResult:
        needle = (destination or "").strip().lower()
        tours = [self._build_tour(i) for i in range(len(md.TOURS))]
        if needle:
            tours = [
                t for t in tours
                if needle in t.destination_city_id.lower()
                or needle in md.CITY_BY_ID[t.destination_city_id].name.lower()
                or needle in md.CITY_BY_ID[t.destination_city_id].name_fa
            ]
        tours.sort(key=lambda t: t.price_per_person.amount)
        return TourSearchResult(
            count=len(tours[: self._cap(max_results)]),
            tours=tours[: self._cap(max_results)],
            is_mock_data=True,
        )

    async def get_tour_details(self, tour_id: str) -> Tour:
        parts = tour_id.strip().split("-")
        if len(parts) != 2 or parts[0] != "TR":
            raise NotFoundError(
                f"'{tour_id}' is not a valid tour id. Use an id returned by search_tours."
            )
        try:
            index = int(parts[1])
        except ValueError as exc:
            raise NotFoundError(
                f"'{tour_id}' does not reference a known tour. "
                "Use an id returned by search_tours."
            ) from exc
        if index >= len(md.TOURS):
            raise NotFoundError(
                f"'{tour_id}' does not reference a known tour. "
                "Use an id returned by search_tours."
            )
        return self._build_tour(index)

    # -- sandbox bookings (always simulated) -----------------------------------------------
    async def _unit_price(self, kind: BookingItemKind, item_id: str) -> int:
        """Price for one passenger/room of the booked item (simulated)."""
        if kind is BookingItemKind.FLIGHT:
            return (await self.get_flight_details(item_id)).price.amount
        if kind is BookingItemKind.HOTEL:
            return (await self.get_hotel_details(item_id)).price_per_night.amount
        if kind is BookingItemKind.TRAIN:
            return (await self.get_train_details(item_id)).price.amount
        if kind is BookingItemKind.BUS:
            return (await self.get_bus_details(item_id)).price.amount
        return (await self.get_tour_details(item_id)).price_per_person.amount

    async def create_booking(
        self, kind: BookingItemKind, item_id: str, passengers: int
    ) -> Booking:
        unit_price = await self._unit_price(kind, item_id)
        booking = Booking(
            id=f"BKG-{uuid.uuid4().hex[:12].upper()}",
            kind=kind,
            item_id=item_id,
            status=BookingStatus.CONFIRMED,
            passengers=passengers,
            total_price=Price(amount=unit_price * passengers, currency=Currency.IRT),
            created_at=datetime.now(timezone.utc),
            simulated=True,
        )
        self._bookings[booking.id] = booking
        return booking

    async def get_booking(self, booking_id: str) -> Booking:
        booking = self._bookings.get(booking_id.strip())
        if booking is None:
            raise NotFoundError(
                f"No booking with reference '{booking_id}'. "
                "Bookings are simulated and live only inside the current server process; "
                "use create_booking first."
            )
        return booking

    async def cancel_booking(self, booking_id: str) -> Booking:
        booking = await self.get_booking(booking_id)
        if booking.status is BookingStatus.CANCELLED:
            raise InvalidInputError(f"Booking '{booking_id}' is already cancelled.")
        cancelled = booking.model_copy(update={"status": BookingStatus.CANCELLED})
        self._bookings[cancelled.id] = cancelled
        return cancelled





