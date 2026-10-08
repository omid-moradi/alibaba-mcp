"""Domain enums for the normalized travel model."""

from enum import StrEnum


class TravelMode(StrEnum):
    """Supported modes of intercity travel."""

    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"


class CabinClass(StrEnum):
    """Flight cabin classes."""

    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"


class BookingStatus(StrEnum):
    """Lifecycle states of a (simulated) booking."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingItemKind(StrEnum):
    """What a booking refers to."""

    FLIGHT = "flight"
    HOTEL = "hotel"
    TRAIN = "train"
    BUS = "bus"
    TOUR = "tour"


class Currency(StrEnum):
    """Currencies used by the domain model.

    IRT is an unofficial but widely used code for the Iranian Toman
    (1 Toman = 10 Rials). Alibaba.ir displays consumer prices in Toman.
    """

    IRT = "IRT"


class TicketType(StrEnum):
    """Flight ticket types as sold on Iranian OTA platforms."""

    SYSTEM = "system"  # "systematic" published-fare tickets
    CHARTER = "charter"  # charter-block tickets


class SeatClass(StrEnum):
    """Train seat/coach classes available on Iranian railways."""

    FOUR_BERTH = "4-berth compartment"
    SIX_BERTH = "6-berth compartment"
    RECLINING = "reclining seat"


class BusType(StrEnum):
    """Intercity bus service types."""

    VIP = "vip"  # 2+1 layout
    STANDARD = "standard"  # 2+2 layout
