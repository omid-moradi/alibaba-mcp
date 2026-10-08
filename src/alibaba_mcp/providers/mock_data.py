"""Deterministic fixture catalogs for the MockProvider.

These are clearly-labeled synthetic data used for tests, CI, offline demos
and the MCP Inspector. They are NOT real Alibaba.ir inventory.
"""

from alibaba_mcp.domain.enums import BusType, SeatClass
from alibaba_mcp.domain.models import Airport, City, TrainStation

# ---------------------------------------------------------------------------
# Cities
# ---------------------------------------------------------------------------
CITIES: list[City] = [
    City(
        id="THR",
        name="Tehran",
        name_fa="تهران",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="MHD",
        name="Mashhad",
        name_fa="مشهد",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="IFN",
        name="Isfahan",
        name_fa="اصفهان",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="SYZ",
        name="Shiraz",
        name_fa="شیراز",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="TBZ",
        name="Tabriz",
        name_fa="تبریز",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="KIH",
        name="Kish",
        name_fa="کیش",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=False,
        has_bus=False,
    ),
    City(
        id="AWZ",
        name="Ahvaz",
        name_fa="اهواز",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="RAS",
        name="Rasht",
        name_fa="رشت",
        country="Iran",
        country_code="IR",
        has_airport=False,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="YZD",
        name="Yazd",
        name_fa="یزد",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="KER",
        name="Kerman",
        name_fa="کرمان",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="BND",
        name="Bandar Abbas",
        name_fa="بندرعباس",
        country="Iran",
        country_code="IR",
        has_airport=True,
        has_train=True,
        has_bus=True,
    ),
    City(
        id="IST",
        name="Istanbul",
        name_fa="استانبول",
        country="Türkiye",
        country_code="TR",
        has_airport=True,
        has_train=False,
        has_bus=False,
    ),
    City(
        id="DXB",
        name="Dubai",
        name_fa="دبی",
        country="United Arab Emirates",
        country_code="AE",
        has_airport=True,
        has_train=False,
        has_bus=False,
    ),
]

CITY_BY_ID = {c.id: c for c in CITIES}

# ---------------------------------------------------------------------------
# Airports
# ---------------------------------------------------------------------------
AIRPORTS: list[Airport] = [
    Airport(
        code="IKA", name="Tehran Imam Khomeini International", city_id="THR", country_code="IR"
    ),
    Airport(code="THR", name="Tehran Mehrabad Domestic", city_id="THR", country_code="IR"),
    Airport(code="MHD", name="Mashhad International", city_id="MHD", country_code="IR"),
    Airport(code="IFN", name="Isfahan International", city_id="IFN", country_code="IR"),
    Airport(code="SYZ", name="Shiraz International", city_id="SYZ", country_code="IR"),
    Airport(code="TBZ", name="Tabriz International", city_id="TBZ", country_code="IR"),
    Airport(code="KIH", name="Kish International", city_id="KIH", country_code="IR"),
    Airport(code="AWZ", name="Ahvaz International", city_id="AWZ", country_code="IR"),
    Airport(code="YZD", name="Yazd Shahid Sadooghi", city_id="YZD", country_code="IR"),
    Airport(code="KER", name="Kerman International", city_id="KER", country_code="IR"),
    Airport(code="BND", name="Bandar Abbas International", city_id="BND", country_code="IR"),
    Airport(code="IST", name="Istanbul Airport", city_id="IST", country_code="TR"),
    Airport(code="DXB", name="Dubai International", city_id="DXB", country_code="AE"),
]

AIRPORT_BY_CODE = {a.code: a for a in AIRPORTS}

# Airline catalog: (IATA code, display name)
AIRLINES: list[tuple[str, str]] = [
    ("IR", "IranAir"),
    ("W5", "Mahan Air"),
    ("EP", "Aseman Airlines"),
    ("CPN", "Caspian Airlines"),
    ("QB", "Qeshm Air"),
    ("TBZ", "ATA Airlines"),
    ("VRH", "Varesh Airlines"),
    ("SPL", "Sepehran Airlines"),
]

# Flight durations in minutes for common routes (both directions).
FLIGHT_DURATION_MINUTES: dict[tuple[str, str], int] = {
    ("THR", "MHD"): 90,
    ("MHD", "THR"): 90,
    ("THR", "IFN"): 65,
    ("IFN", "THR"): 65,
    ("THR", "SYZ"): 85,
    ("SYZ", "THR"): 85,
    ("THR", "TBZ"): 75,
    ("TBZ", "THR"): 75,
    ("THR", "KIH"): 100,
    ("KIH", "THR"): 100,
    ("THR", "AWZ"): 85,
    ("AWZ", "THR"): 85,
    ("THR", "YZD"): 65,
    ("YZD", "THR"): 65,
    ("THR", "KER"): 85,
    ("KER", "THR"): 85,
    ("THR", "BND"): 105,
    ("BND", "THR"): 105,
    ("MHD", "IFN"): 70,
    ("IFN", "MHD"): 70,
    ("MHD", "KIH"): 95,
    ("KIH", "MHD"): 95,
    ("IKA", "IST"): 195,
    ("IST", "IKA"): 230,
    ("IKA", "DXB"): 135,
    ("DXB", "IKA"): 155,
    ("MHD", "IST"): 230,
    ("IST", "MHD"): 255,
}

# Economy base fares in Toman for common routes (per adult).
FLIGHT_BASE_FARE_TOMAN: dict[tuple[str, str], int] = {
    ("THR", "MHD"): 1_500_000,
    ("THR", "IFN"): 1_200_000,
    ("THR", "SYZ"): 1_400_000,
    ("THR", "TBZ"): 1_300_000,
    ("THR", "KIH"): 2_100_000,
    ("THR", "AWZ"): 1_400_000,
    ("THR", "YZD"): 1_300_000,
    ("THR", "KER"): 1_500_000,
    ("THR", "BND"): 1_700_000,
    ("MHD", "IFN"): 1_200_000,
    ("MHD", "KIH"): 1_900_000,
    ("IKA", "IST"): 9_500_000,
    ("IKA", "DXB"): 7_000_000,
    ("MHD", "IST"): 10_500_000,
}

# ---------------------------------------------------------------------------
# Rail
# ---------------------------------------------------------------------------
TRAIN_STATIONS: list[TrainStation] = [
    TrainStation(code="THR", name="Tehran Railway Station", city_id="THR"),
    TrainStation(code="MHD", name="Mashhad Railway Station", city_id="MHD"),
    TrainStation(code="IFN", name="Isfahan Railway Station", city_id="IFN"),
    TrainStation(code="SYZ", name="Shiraz Railway Station", city_id="SYZ"),
    TrainStation(code="TBZ", name="Tabriz Railway Station", city_id="TBZ"),
    TrainStation(code="AWZ", name="Ahvaz Railway Station", city_id="AWZ"),
    TrainStation(code="RAS", name="Rasht Railway Station", city_id="RAS"),
    TrainStation(code="YZD", name="Yazd Railway Station", city_id="YZD"),
    TrainStation(code="KER", name="Kerman Railway Station", city_id="KER"),
    TrainStation(code="BND", name="Bandar Abbas Railway Station", city_id="BND"),
]

STATION_BY_CODE = {s.code: s for s in TRAIN_STATIONS}

TRAIN_OPERATORS = ["Raja", "Fadak", "BonRail"]

TRAIN_SEAT_CLASSES: list[SeatClass] = [
    SeatClass.FOUR_BERTH,
    SeatClass.SIX_BERTH,
    SeatClass.RECLINING,
]

TRAIN_DURATION_MINUTES: dict[tuple[str, str], int] = {
    ("THR", "MHD"): 570,
    ("THR", "IFN"): 300,
    ("THR", "SYZ"): 720,
    ("THR", "TBZ"): 600,
    ("THR", "AWZ"): 600,
    ("THR", "RAS"): 270,
    ("THR", "YZD"): 330,
    ("THR", "KER"): 600,
    ("THR", "BND"): 870,
    ("RAS", "MHD"): 540,
    ("IFN", "SYZ"): 360,
}

TRAIN_BASE_FARE_TOMAN: dict[tuple[str, str], int] = {
    ("THR", "MHD"): 450_000,
    ("THR", "IFN"): 280_000,
    ("THR", "SYZ"): 520_000,
    ("THR", "TBZ"): 420_000,
    ("THR", "AWZ"): 400_000,
    ("THR", "RAS"): 250_000,
    ("THR", "YZD"): 300_000,
    ("THR", "KER"): 450_000,
    ("THR", "BND"): 600_000,
    ("RAS", "MHD"): 480_000,
    ("IFN", "SYZ"): 320_000,
}

# ---------------------------------------------------------------------------
# Bus
# ---------------------------------------------------------------------------
BUS_OPERATORS = ["Seir-o-Safar", "Hami Safar", "Royal Safar", "Royan Safar", "Tejarat Safar"]

BUS_TYPES: list[BusType] = [BusType.VIP, BusType.STANDARD]

BUS_DURATION_MINUTES: dict[tuple[str, str], int] = {
    ("THR", "MHD"): 600,
    ("THR", "IFN"): 330,
    ("THR", "SYZ"): 780,
    ("THR", "TBZ"): 570,
    ("THR", "AWZ"): 600,
    ("THR", "RAS"): 270,
    ("THR", "YZD"): 330,
    ("THR", "KER"): 600,
    ("THR", "BND"): 900,
    ("MHD", "IFN"): 540,
    ("IFN", "SYZ"): 330,
}

BUS_BASE_FARE_TOMAN: dict[tuple[str, str], int] = {
    ("THR", "MHD"): 350_000,
    ("THR", "IFN"): 200_000,
    ("THR", "SYZ"): 400_000,
    ("THR", "TBZ"): 320_000,
    ("THR", "AWZ"): 300_000,
    ("THR", "RAS"): 180_000,
    ("THR", "YZD"): 200_000,
    ("THR", "KER"): 320_000,
    ("THR", "BND"): 420_000,
    ("MHD", "IFN"): 300_000,
    ("IFN", "SYZ"): 180_000,
}

# ---------------------------------------------------------------------------
# Hotels: (name, stars, guest_rating, room_type, amenities, base nightly Toman)
# ---------------------------------------------------------------------------
HOTELS: dict[str, list[tuple[str, int, float, str, list[str], int]]] = {
    "MHD": [
        (
            "Darvishi Hotel",
            5,
            4.6,
            "Standard Double",
            ["spa", "restaurant", "free wifi", "parking"],
            4_800_000,
        ),
        (
            "Sinoor Hotel",
            4,
            4.3,
            "Standard Double",
            ["restaurant", "free wifi", "breakfast"],
            3_200_000,
        ),
        ("Madinah Al-Reza Hotel", 3, 4.1, "Twin Room", ["free wifi", "breakfast"], 1_800_000),
        ("Pardisan Hotel", 3, 3.8, "Single Room", ["free wifi"], 1_400_000),
    ],
    "THR": [
        (
            "Espinas Palace Hotel",
            5,
            4.7,
            "Deluxe Double",
            ["spa", "gym", "restaurant", "free wifi"],
            8_500_000,
        ),
        (
            "Esteghlal Hotel",
            5,
            4.4,
            "Standard Double",
            ["pool", "restaurant", "free wifi"],
            6_800_000,
        ),
        (
            "Homa Hotel",
            4,
            4.2,
            "Standard Double",
            ["restaurant", "free wifi", "breakfast"],
            4_200_000,
        ),
        ("Ferdowsi Grand Hotel", 3, 3.9, "Single Room", ["free wifi", "breakfast"], 2_100_000),
    ],
    "IFN": [
        (
            "Abbasi Hotel",
            5,
            4.8,
            "Historic Double",
            ["garden", "restaurant", "free wifi"],
            7_200_000,
        ),
        ("Kowsar Hotel", 4, 4.3, "Standard Double", ["pool", "restaurant", "free wifi"], 3_900_000),
        ("Grand Isfahan Hotel", 3, 3.9, "Twin Room", ["free wifi", "breakfast"], 1_900_000),
    ],
    "SYZ": [
        ("Zandiyeh Hotel", 5, 4.6, "Standard Double", ["spa", "restaurant", "pool"], 5_600_000),
        ("Grand Shiraz Hotel", 4, 4.2, "Standard Double", ["restaurant", "free wifi"], 3_400_000),
        ("Parseh Hotel", 3, 4.0, "Single Room", ["free wifi", "breakfast"], 1_700_000),
    ],
    "KIH": [
        (
            "Dariush Grand Hotel",
            5,
            4.5,
            "Sea-view Double",
            ["beach", "pool", "restaurant"],
            6_900_000,
        ),
        ("Shayan Hotel", 4, 4.2, "Standard Double", ["pool", "free wifi", "breakfast"], 3_800_000),
        ("Sorinet Marjan Hotel", 3, 4.0, "Twin Room", ["free wifi"], 2_200_000),
    ],
    "IST": [
        (
            "CVK Park Bosphorus Hotel",
            5,
            4.7,
            "Bosphorus-view Double",
            ["spa", "gym", "restaurant"],
            21_000_000,
        ),
        (
            "Titanic Port Hotel",
            4,
            4.3,
            "Standard Double",
            ["pool", "free wifi", "breakfast"],
            12_500_000,
        ),
        ("Grand Sairan Hotel", 3, 4.0, "Twin Room", ["free wifi", "breakfast"], 6_400_000),
    ],
    "DXB": [
        (
            "Rixos Premium JBR",
            5,
            4.8,
            "Sea-view Double",
            ["beach", "pool", "spa", "gym"],
            28_000_000,
        ),
        ("Grand Midwest Tower", 4, 4.2, "Standard Double", ["pool", "free wifi"], 14_500_000),
        ("Ibis Al Barsha", 3, 4.0, "Single Room", ["free wifi", "breakfast"], 7_800_000),
    ],
}

# ---------------------------------------------------------------------------
# Tours: (title, dest city id, origin city id, days, base price Toman,
#         inclusions, international)
# ---------------------------------------------------------------------------
TOURS: list[tuple[str, str, str, int, int, list[str], bool]] = [
    (
        "Istanbul Discovery — 5 Days",
        "IST",
        "THR",
        5,
        34_000_000,
        ["round-trip flight", "4-night hotel", "daily breakfast", "city tours", "airport transfer"],
        True,
    ),
    (
        "Antalya Beach Holiday — 7 Days",
        "IST",
        "THR",
        7,
        42_000_000,
        ["round-trip flight", "6-night resort stay", "all-inclusive meals", "beach transfer"],
        True,
    ),
    (
        "Kish Island Escape — 3 Days",
        "KIH",
        "THR",
        3,
        9_500_000,
        ["round-trip flight", "2-night hotel", "daily breakfast", "snorkeling trip"],
        False,
    ),
    (
        "Dubai City Break — 4 Days",
        "DXB",
        "THR",
        4,
        26_000_000,
        ["round-trip flight", "3-night hotel", "city tour", "desert safari"],
        True,
    ),
    (
        "Isfahan Heritage Tour — 2 Days",
        "IFN",
        "THR",
        2,
        4_200_000,
        ["intercity transport", "1-night hotel", "guided tours", "breakfast"],
        False,
    ),
    (
        "Mashhad Pilgrimage Package — 3 Days",
        "MHD",
        "THR",
        3,
        6_800_000,
        ["intercity transport", "2-night hotel", "ziyarat guide", "breakfast"],
        False,
    ),
]
