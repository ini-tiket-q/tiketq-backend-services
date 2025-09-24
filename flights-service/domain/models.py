from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Literal

# -------------------------------
# Type Aliases for Enum-like values
# -------------------------------
BookingStatus = Literal["INCOMPLETE", "PAID", "CANCELLED"]
PaymentStatus = Literal["PENDING", "PAID", "FAILED"]
PassengerType = Literal["ADULT", "CHILD", "INFANT"]
FlightStatus = Literal["SCHEDULED", "DELAYED", "CANCELLED", "DEPARTED", "ARRIVED"]



# -------------------------------
# Data Classes for Domain Models
# -------------------------------


@dataclass(slots=True)
class City:
    code: str  # e.g., "CGK"
    city_name: str  # e.g., "JakartaSoekarno–Hatta International Airport"


@dataclass(slots=True)
class Airline:
    flight_code: str  # e.g., "GA"
    flight_name: str  # e.g., "Garuda Indonesia"
    flight_image: Optional[str] = None  # e.g., "https://example.com/flight_image.png"


@dataclass(slots=True)
class Flight:
    id: Optional[str]
    airline_code: str
    flight_from: str  # FK to City.code
    flight_to: str  # FK to City.code
    flight_route: Optional[str]
    flight_date: date
    departure_time: datetime
    arrival_time: datetime
    flight_transit: Optional[str] = None  # e.g., "Langsung, 1 transit, 2 transit, etc."
    transit_info: Optional[str] = None
    flight_class: Optional[str] = None
    flight_seat: Optional[int] = None
    available_seat: Optional[int] = None  # e.g., 100
    baggage_capacity: Optional[str] = None  # e.g., "20kg, 30kg, etc."
    facilities: Optional[str] = None  # e.g., "In-flight meals, Wi-Fi, etc."
    adult_count: Optional[int] = None
    child_count: Optional[int] = None
    infant_count: Optional[int] = None
    publish_price: Optional[float] = None  # Price before any discounts or taxes
    tax: Optional[float] = None
    total_fare: Optional[float] = None  # Total fare including tax
    show_nta_price: Optional[float] = None
    real_nta_price: Optional[float] = None
    status: FlightStatus = "SCHEDULED"


@dataclass
class Booking:
    id: Optional[str]
    flight_id: str
    user_id: Optional[str]
    contact_name: str
    contact_phone: str
    contact_email: str
    status: BookingStatus
    passenger_details: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Passenger:
    id: Optional[str]
    booking_id: str
    passenger_type: PassengerType
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None  # Date of Birth
    id_card_number: Optional[str] = None  # e.g., National ID or Passport Number


@dataclass
class Payment:
    id: Optional[str]
    booking_id: str
    provider: str  # e.g., "Credit Card", "Bank Transfer"
    status: PaymentStatus
    amount: float
    currency: str
    snap_token: Optional[str] = None  # e.g., Token from payment gateway
    redirect_url: Optional[str] = None  # e.g., URL to redirect after payment
    raw_provider_payload: Optional[str] = None
    transaction_id: Optional[str] = None  # e.g., Transaction ID from payment gateway
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ETicket:
    id: Optional[str]
    booking_id: str
    ticket_number: str  # e.g., "1234567890"
    issued_at: Optional[datetime] = None  # Date and time when the ticket was issued
    document_url: Optional[str] = None  # URL to download the e-ticket document
