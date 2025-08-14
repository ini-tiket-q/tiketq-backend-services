from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Literal

BookingStatus = Literal["INCOMPLETE", "PAID", "CANCELLED"]
PaymentStatus = Literal["PENDING", "PAID", "FAILED"]

@dataclass(slots=True)
class Flight:
    id: Optional[str]
    flight_number: str
    from_airport: str
    to_airport: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: str
    gate: Optional[str] = None
    terminal: Optional[str] = None
    status: str = "SCHEDULED"
    notes: Optional[str] = None

@dataclass
class Booking:
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
    flight_number: str
    airline: Optional[str]
    cabin: Optional[str]
    pax_adult: int
    pax_child: int
    pax_infant: int
    fare_amount: int
    fare_currency: str
    offer_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Passenger:
    id: Optional[str]
    booking_id: Optional[str]
    type: Literal["ADULT", "CHILD", "INFANT"]
    full_name: str
    dob: Optional[date] = None
    id_no: Optional[str] = None

@dataclass
class Payment:
    id: Optional[str]
    booking_id: str
    provider: str
    status: PaymentStatus
    amount: int
    currency: str
    snap_token: Optional[str] = None
    redirect_url: Optional[str] = None
    raw_provider_payload: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None    
