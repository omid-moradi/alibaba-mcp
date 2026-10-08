"""Alibaba.ir live provider — adapter boundary.

STATUS (as of the investigation recorded in ``docs/live-integration-notes.md``):
Alibaba.ir publishes **no official public API** for third-party developers.
The endpoints used by its own web/mobile apps are undocumented, session- and
CAPTCHA-protected, and not intended for third-party consumption. This project
will not scrape them or bypass any protection.

``AlibabaProvider`` therefore keeps the adapter seam complete and honest:

* it implements the full ``TravelProvider`` protocol surface,
* every data call fails with a single, clear ``ProviderNotConfiguredError``
  explaining exactly why live mode is unavailable and where to read more,
* it NEVER silently falls back to mock data — a failed live request is an
  error, not a disguised mock answer.

To activate a real live integration some day, implement the transport in
``client.py`` against an officially provided API, add parsing/mapping modules,
and wire them into the provider methods.
"""

from datetime import date

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
from alibaba_mcp.providers.base import ProviderNotConfiguredError

_NOT_CONFIGURED_MESSAGE = (
    "Live Alibaba.ir integration is not available in this project: "
    "Alibaba.ir exposes no official public API, and its internal web/mobile "
    "endpoints are undocumented and protected (see docs/live-integration-notes.md). "
    "The server refused to fabricate or scrape data. "
    "Set ALIBABA_PROVIDER=mock to use the deterministic mock provider."
)


class AlibabaProvider:
    """Live provider seam.

    Fails loudly and honestly until a legitimate official API can be wired in.
    """

    def __init__(self, base_url: str = "", timeout_seconds: float = 10.0) -> None:
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    # -- identity ------------------------------------------------------------
    @property
    def name(self) -> str:
        return "alibaba-live"

    @property
    def is_mock(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return (
            "Live Alibaba.ir provider (placeholder). No official public API "
            "exists today, so this provider reports a clear configuration error "
            "instead of fabricating or scraping data."
        )

    @property
    def supports_bookings(self) -> bool:
        return False  # side effects against a live system are out of scope by design

    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            mode="live",
            is_mock=False,
            description=self.description,
            supported_products=[],
        )

    # -- capability refusal ------------------------------------------------------
    def _refuse(self) -> ProviderNotConfiguredError:
        return ProviderNotConfiguredError(_NOT_CONFIGURED_MESSAGE)

    # -- reference data -----------------------------------------------------------
    async def search_airports(self, query: str, limit: int = 10) -> list[Airport]:
        raise self._refuse()

    async def search_cities(self, query: str, limit: int = 10) -> list[City]:
        raise self._refuse()

    async def search_train_stations(self, query: str, limit: int = 10) -> list[TrainStation]:
        raise self._refuse()

    # -- flights --------------------------------------------------------------------
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        adults: int = 1,
        cabin_class: CabinClass = CabinClass.ECONOMY,
        max_results: int = 10,
    ) -> FlightSearchResult:
        raise self._refuse()

    async def get_flight_details(self, flight_id: str) -> Flight:
        raise self._refuse()

    # -- hotels ---------------------------------------------------------------------
    async def search_hotels(
        self,
        city_id: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        min_stars: int = 1,
        max_results: int = 10,
    ) -> HotelSearchResult:
        raise self._refuse()

    async def get_hotel_details(self, hotel_id: str) -> Hotel:
        raise self._refuse()

    # -- trains ------------------------------------------------------------------------
    async def search_trains(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        max_results: int = 10,
    ) -> TrainSearchResult:
        raise self._refuse()

    async def get_train_details(self, train_id: str) -> Train:
        raise self._refuse()

    # -- buses ---------------------------------------------------------------------------
    async def search_buses(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        max_results: int = 10,
    ) -> BusSearchResult:
        raise self._refuse()

    async def get_bus_details(self, bus_id: str) -> Bus:
        raise self._refuse()

    # -- tours -----------------------------------------------------------------------------
    async def search_tours(
        self, destination: str | None = None, max_results: int = 10
    ) -> TourSearchResult:
        raise self._refuse()

    async def get_tour_details(self, tour_id: str) -> Tour:
        raise self._refuse()

    # -- bookings (never supported against a live system without an official API) -----------
    async def create_booking(
        self, kind: BookingItemKind, item_id: str, passengers: int
    ) -> Booking:
        raise self._refuse()

    async def get_booking(self, booking_id: str) -> Booking:
        raise self._refuse()

    async def cancel_booking(self, booking_id: str) -> Booking:
        raise self._refuse()


