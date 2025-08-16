# models.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Literal
from uuid import UUID

# -----------------------
# Enums / literals
# -----------------------

# Broadened to include provider-style states
BookingStatus = Literal[
    "INCOMPLETE",  # local draft
    "WAITING",     # booked, waiting for issue
    "ISSUED",      # ticket issued
    "PAID",
    "CANCELLED",
    "CONFIRMED"    # local confirm step (optional)
]

PaymentStatus = Literal["PENDING", "PAID", "FAILED"]

# -----------------------
# Reference data (PDF)
# -----------------------

@dataclass(slots=True)
class City:
    # PDF: code char(3), city_name varchar
    code: str
    city_name: str


@dataclass(slots=True)
class Airline:
    # PDF: flight_code char(3), flight_name varchar, flight_image text
    flight_code: str
    flight_name: str
    flight_image: Optional[str] = None


# -----------------------
# Flight & Availability
# -----------------------

@dataclass(slots=True)
class Flight:
    """
    Combines normalized fields you already used (e.g., 'flight_number', 'departure_time')
    with PDF-style parity fields (publishfare, seatavail, baggage, etc.).
    """
    # Normalized (existing usage)
    id: Optional[str] = None          # local ID (string/uuid)
    flight_number: str = ""           # e.g. "QG-724"  (alias of airline_code + numeric)
    from_airport: str = ""            # IATA
    to_airport: str = ""              # IATA
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    status: str = "SCHEDULED"
    notes: Optional[str] = None

    # PDF parity fields
    flight_id: Optional[UUID] = None
    airline_code: Optional[str] = None            # char(3)
    flight_from: Optional[str] = None             # IATA
    flight_to: Optional[str] = None               # IATA
    flight_route: Optional[str] = None            # e.g., "CGK-SUB"
    flight_date: Optional[date] = None
    flight_transit: Optional[str] = None          # e.g., "Nonstop"
    flight_infotransit: Optional[str] = None
    flight_datetime: Optional[str] = None         # provider-composed time text
    flight_price: Optional[float] = None
    flight_publishfare: Optional[float] = None
    flight_seatavail: Optional[int] = None
    flight_baggage: Optional[str] = None
    flight_facilities: Optional[str] = None


@dataclass(slots=True)
class FlightClassAvailability:
    """
    Availability/pricing at class level (PDF table).
    """
    availability_id: Optional[UUID]
    flight_id: UUID
    klass: str                                 # 'class' is a keyword; use 'klass'
    available_seat: int
    baggage_capacity: Optional[str] = None
    facilities: Optional[str] = None
    adult_count: int = 1
    child_count: int = 0
    infant_count: int = 0
    publish_price: Optional[float] = None
    tax: Optional[float] = None
    total_fare: Optional[float] = None
    flight_shownta: Optional[float] = None
    flight_realnta: Optional[float] = None


# -----------------------
# Booking domain
# -----------------------

@dataclass
class Booking:
    """
    Normalized fields (what your code uses) + PDF-friendly fields to mirror provider responses.
    """
    # Normalized (existing)
    id: Optional[str]
    user_id: Optional[str]
    contact_name: str
    contact_phone: str
    contact_email: str
    status: BookingStatus
    route_from: str
    route_to: str
    departure_time: datetime
    arrival_time: datetime
    flight_number: str                 # e.g. "QG-724"
    airline: Optional[str]
    cabin: Optional[str]
    pax_adult: int
    pax_child: int
    pax_infant: int
    fare_amount: int
    fare_currency: str
    offer_id: str                      # local/remote offer/PNR linkage
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # PDF parity
    flight_id: Optional[UUID] = None
    provider_kodebooking: Optional[str] = None      # provider 'kodebooking' (PNR)
    passenger_details_json: Optional[str] = None    # PDF returns *_json blocks as strings
    booking_status: Optional[str] = None            # raw provider status, if you want to store it


@dataclass
class Passenger:
    """
    Expanded to support PDF booking payload requirements (titles, baggage, passport).
    """
    id: Optional[str]
    booking_id: Optional[str]
    type: Literal["ADULT", "CHILD", "INFANT"]
    full_name: str
    dob: Optional[date] = None

    # Existing
    id_no: Optional[str] = None

    # For PDF mapping (optional in local store)
    title: Optional[str] = None                    # Mr/Mrs/Ms, Mstr/Miss
    baggage: Optional[str] = None                  # e.g., "20 Kg"
    passport_number: Optional[str] = None
    passport_expired: Optional[date] = None


# -----------------------
# Payments & Tickets
# -----------------------

@dataclass
class Payment:
    id: Optional[str]
    booking_id: str
    provider: str                    # e.g., "midtrans"
    status: PaymentStatus
    amount: int
    currency: str
    snap_token: Optional[str] = None
    redirect_url: Optional[str] = None
    raw_provider_payload: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # PDF parity
    paid_at: Optional[datetime] = None


@dataclass
class ETicket:
    # PDF: ticket store (optional; you can also derive link on the fly)
    id: Optional[str]
    booking_id: str
    ticket_number: Optional[str] = None
    issued_at: Optional[datetime] = None
    document_url: Optional[str] = None
