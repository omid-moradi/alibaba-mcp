"""Provider abstraction: the seam between MCP tools and travel data sources.

MCP tools talk to ``TravelProvider`` only. Concrete providers (mock, live
Alibaba, or anything else) implement this interface and translate their own
response shapes into the normalized domain models. The MCP layer therefore
never depends on the internals of any website or API.
"""

from datetime import date
from typing import Protocol

from alibaba_mcp.domain.enums import BookingItemKind, CabinClass
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
    ProviderInfo,
    Tour,
    TourSearchResult,
    Train,
    TrainSearchResult,
    TrainStation,
)


class ProviderError(Exception):
    """Base class for provider failures. Messages are safe to show to users and LLMs."""


class InvalidInputError(ProviderError):
    """The request is semantically invalid (unknown origin, origin==destination, past date...)."""


class NotFoundError(ProviderError):
    """A requested entity (flight id, hotel id, booking id) does not exist."""


class ProviderUnavailableError(ProviderError):
    """The provider cannot serve the request right now (network, upstream outage)."""


class ProviderNotConfiguredError(ProviderUnavailableError):
    """The provider requires configuration (credentials/endpoints) that is missing."""


class RateLimitedError(ProviderError):
    """The upstream service applied a rate limit. Never bypass it: back off and retry later."""


class ExternalAPIError(ProviderError):
    """The upstream service returned an unexpected response."""


class ParsingError(ProviderError):
    """The upstream response could not be parsed into the domain model."""


class TimeoutError(ProviderError):
    """The upstream service did not respond within the configured timeout."""


class TravelProvider(Protocol):
    """The capability contract every provider must satisfy.

    Implementations must be safe to call concurrently and must never expose
    raw upstream payloads: only normalized domain models cross this seam.
    """

    # -- identity ---------------------------------------------------------
    @property
    def name(self) -> str: ...

    @property
    def is_mock(self) -> bool: ...

    @property
    def description(self) -> str: ...

    @property
    def supports_bookings(self) -> bool: ...

    def provider_info(self) -> ProviderInfo: ...

    # -- reference data ----------------------------------------------------
    async def search_airports(self, query: str, limit: int = 10) -> list[Airport]: ...

    async def search_cities(self, query: str, limit: int = 10) -> list[City]: ...

    async def search_train_stations(self, query: str, limit: int = 10) -> list[TrainStation]: ...

    # -- flights -----------------------------------------------------------
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        adults: int = 1,
        cabin_class: CabinClass = CabinClass.ECONOMY,
        max_results: int = 10,
    ) -> FlightSearchResult: ...

    async def get_flight_details(self, flight_id: str) -> Flight: ...

    # -- hotels ------------------------------------------------------------
    async def search_hotels(
        self,
        city_id: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        min_stars: int = 1,
        max_results: int = 10,
    ) -> HotelSearchResult: ...

    async def get_hotel_details(self, hotel_id: str) -> Hotel: ...

    # -- trains ------------------------------------------------------------
    async def search_trains(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        max_results: int = 10,
    ) -> TrainSearchResult: ...

    async def get_train_details(self, train_id: str) -> Train: ...

    # -- buses -------------------------------------------------------------
    async def search_buses(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        max_results: int = 10,
    ) -> BusSearchResult: ...

    async def get_bus_details(self, bus_id: str) -> Bus: ...

    # -- tours -------------------------------------------------------------
    async def search_tours(
        self, destination: str | None = None, max_results: int = 10
    ) -> TourSearchResult: ...

    async def get_tour_details(self, tour_id: str) -> Tour: ...

    # -- sandbox bookings --------------------------------------------------
    async def create_booking(
        self,
        kind: BookingItemKind,
        item_id: str,
        passengers: int,
    ) -> Booking: ...

    async def get_booking(self, booking_id: str) -> Booking: ...

    async def cancel_booking(self, booking_id: str) -> Booking: ...
