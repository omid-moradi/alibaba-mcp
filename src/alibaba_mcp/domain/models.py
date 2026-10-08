"""Normalized travel domain models.

Every provider (live or mock) must translate its own response shapes into
these models. MCP tools never expose raw provider payloads — only normalized
domain objects. This keeps the MCP layer stable even if a provider's
underlying implementation changes.

All datetimes are timezone-aware, in the provider's local time
(Asia/Tehran for domestic inventory in this project).
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from alibaba_mcp.domain.enums import (
    BookingItemKind,
    BookingStatus,
    BusType,
    CabinClass,
    Currency,
    SeatClass,
    TicketType,
    TravelMode,
)


class DomainModel(BaseModel):
    """Base for all domain models: strict, no extra fields leaked from providers."""

    model_config = ConfigDict(extra="forbid")


class Price(DomainModel):
    """A monetary amount. Amounts are integer Toman (1 Toman = 10 Rials)."""

    amount: int = Field(ge=0, description="Price in Iranian Toman.")
    currency: Currency = Field(default=Currency.IRT, description="ISO-style currency code.")


class City(DomainModel):
    """A city served by the platform (for bus/train/flight origin & destination)."""

    id: str = Field(min_length=2, max_length=8, description="Stable city code, e.g. 'THR'.")
    name: str = Field(description="English display name.")
    name_fa: str = Field(description="Persian display name.")
    country: str = Field(description="English country name.")
    country_code: str = Field(min_length=2, max_length=2, description="ISO 3166-1 alpha-2 code.")
    has_airport: bool = Field(description="Whether the city has a served airport.")
    has_train: bool = Field(description="Whether intercity trains serve the city.")
    has_bus: bool = Field(description="Whether intercity buses serve the city.")


class Airport(DomainModel):
    """An airport served by the platform."""

    code: str = Field(min_length=3, max_length=3, description="IATA airport code, e.g. 'IKA'.")
    name: str = Field(description="Airport display name.")
    city_id: str = Field(description="City this airport serves.")
    country_code: str = Field(min_length=2, max_length=2)


class TrainStation(DomainModel):
    """A railway station."""

    code: str = Field(description="Stable station code.")
    name: str = Field(description="Station display name.")
    city_id: str = Field(description="City this station serves.")


class Flight(DomainModel):
    """A single bookable flight option."""

    id: str = Field(description="Opaque provider-assigned flight id. Use verbatim in other tools.")
    origin_code: str = Field(description="IATA code of the origin airport, e.g. 'IKA'.")
    destination_code: str = Field(description="IATA code of the destination airport.")
    departure_time: datetime = Field(description="Local departure time (Asia/Tehran).")
    arrival_time: datetime = Field(description="Local arrival time (Asia/Tehran).")
    duration_minutes: int = Field(gt=0, description="Total flight duration in minutes.")
    airline_code: str = Field(description="Airline IATA code, e.g. 'IR'.")
    airline_name: str = Field(description="Airline display name.")
    flight_number: str = Field(description="Flight number, e.g. 'IR452'.")
    cabin_class: CabinClass = Field(description="Cabin class of this fare.")
    ticket_type: TicketType = Field(description="System (published) or charter ticket.")
    seats_available: int = Field(ge=0, description="Seats remaining at this fare.")
    baggage_allowance_kg: int = Field(ge=0, description="Included checked baggage in kg.")
    price: Price = Field(description="Fare per adult passenger, in Toman.")
    refundable: bool = Field(description="Whether this fare is refundable per policy.")


class Hotel(DomainModel):
    """A hotel property with an indicative nightly rate."""

    id: str = Field(description="Opaque provider-assigned hotel id.")
    name: str = Field(description="Hotel display name.")
    city_id: str = Field(description="City the hotel is located in.")
    stars: int = Field(ge=1, le=5, description="Hotel star rating (1-5).")
    guest_rating: float = Field(ge=0, le=5, description="Average guest score (0-5).")
    room_type: str = Field(description="Room type covered by the quoted rate.")
    amenities: list[str] = Field(description="Notable amenities.")
    price_per_night: Price = Field(description="Indicative nightly rate in Toman.")
    free_cancellation: bool = Field(description="Whether free cancellation applies.")


class Train(DomainModel):
    """A single intercity train option."""

    id: str = Field(description="Opaque provider-assigned train id.")
    origin_code: str = Field(description="Origin station code.")
    destination_code: str = Field(description="Destination station code.")
    departure_time: datetime = Field(description="Local departure time (Asia/Tehran).")
    arrival_time: datetime = Field(description="Local arrival time (Asia/Tehran).")
    duration_minutes: int = Field(gt=0)
    operator: str = Field(description="Rail operator, e.g. 'Raja'.")
    train_number: str = Field(description="Service number.")
    seat_class: SeatClass = Field(description="Coach/seat class of this fare.")
    seats_available: int = Field(ge=0)
    price: Price = Field(description="Fare per passenger, in Toman.")


class Bus(DomainModel):
    """A single intercity bus option."""

    id: str = Field(description="Opaque provider-assigned bus trip id.")
    origin_code: str = Field(description="Origin city/terminal code.")
    destination_code: str = Field(description="Destination city/terminal code.")
    departure_time: datetime = Field(description="Local departure time (Asia/Tehran).")
    arrival_time: datetime = Field(description="Local arrival time (Asia/Tehran).")
    duration_minutes: int = Field(gt=0)
    operator: str = Field(description="Bus operator/terminal company.")
    bus_type: BusType = Field(description="Service type (VIP or standard).")
    seats_available: int = Field(ge=0)
    price: Price = Field(description="Fare per passenger, in Toman.")


class Tour(DomainModel):
    """A packaged tour product."""

    id: str = Field(description="Opaque provider-assigned tour id.")
    title: str = Field(description="Tour display title.")
    destination_city_id: str = Field(description="Primary destination city id.")
    origin_city_id: str = Field(description="Departure city id.")
    duration_days: int = Field(gt=0, description="Total trip length in days.")
    price_per_person: Price = Field(description="Tour price per person, in Toman.")
    inclusions: list[str] = Field(description="What the price includes.")
    is_international: bool = Field(description="Whether the tour leaves Iran.")


class TravelOption(DomainModel):
    """A normalized option across travel modes, used for comparisons."""

    mode: TravelMode = Field(description="Mode of travel for this option.")
    option_id: str = Field(description="Provider id of the underlying option.")
    title: str = Field(description="Human-readable summary of the option.")
    departure_time: datetime = Field(description="Local departure time (Asia/Tehran).")
    duration_minutes: int = Field(gt=0)
    price: Price = Field(description="Price per passenger, in Toman.")
    operator: str = Field(description="Airline / rail operator / bus company.")


class TravelOptionComparison(DomainModel):
    """Result of comparing options across travel modes."""

    origin_code: str
    destination_code: str
    departure_date: date
    cheapest: TravelOption | None = Field(description="Lowest-price option across all modes.")
    fastest: TravelOption | None = Field(description="Shortest-duration option across all modes.")
    options: list[TravelOption] = Field(description="All comparable options found.")
    is_mock_data: bool = Field(description="True when results come from the mock provider.")


class CostComponent(DomainModel):
    """A single line item in a trip cost breakdown."""

    label: str = Field(description="Human-readable component name.")
    price: Price
    detail: str = Field(description="How this component was priced.")


class CostBreakdown(DomainModel):
    """Itemized total cost for a trip."""

    components: list[CostComponent] = Field(description="Line items.")
    total: Price = Field(description="Sum of all components, in Toman.")
    is_mock_data: bool


class Booking(DomainModel):
    """A simulated booking created in the sandbox.

    IMPORTANT: bookings in this project are always simulated.
    No real reservation is made on any real system.
    """

    id: str = Field(description="Booking reference, e.g. 'BKG-...' (simulated).")
    kind: BookingItemKind = Field(description="What was booked.")
    item_id: str = Field(description="Provider id of the booked item.")
    status: BookingStatus = Field(description="Current booking status (simulated).")
    passengers: int = Field(ge=1, description="Number of passengers.")
    total_price: Price = Field(description="Total price in Toman (simulated).")
    created_at: datetime = Field(description="Creation time (UTC).")
    simulated: bool = Field(default=True, description="Always True: bookings are sandboxed.")


class FlightSearchResult(DomainModel):
    """Normalized flight search response."""

    origin_code: str
    destination_code: str
    departure_date: date
    count: int = Field(ge=0, description="Number of options returned.")
    flights: list[Flight]
    is_mock_data: bool = Field(description="True when results come from the mock provider.")


class HotelSearchResult(DomainModel):
    """Normalized hotel search response."""

    city_id: str
    check_in: date
    check_out: date
    count: int = Field(ge=0)
    hotels: list[Hotel]
    is_mock_data: bool


class TrainSearchResult(DomainModel):
    """Normalized train search response."""

    origin_code: str
    destination_code: str
    departure_date: date
    count: int = Field(ge=0)
    trains: list[Train]
    is_mock_data: bool


class BusSearchResult(DomainModel):
    """Normalized bus search response."""

    origin_code: str
    destination_code: str
    departure_date: date
    count: int = Field(ge=0)
    buses: list[Bus]
    is_mock_data: bool


class TourSearchResult(DomainModel):
    """Normalized tour search response."""

    count: int = Field(ge=0)
    tours: list[Tour]
    is_mock_data: bool


class ProviderInfo(DomainModel):
    """Describes the active provider and its capabilities."""

    name: str = Field(description="Provider identifier, e.g. 'mock' or 'alibaba-live'.")
    mode: str = Field(description="Provider mode: 'mock' or 'live'.")
    is_mock: bool = Field(description="True when data is simulated.")
    description: str = Field(description="What this provider can and cannot do.")
    supported_products: list[str] = Field(description="Products the provider serves.")
