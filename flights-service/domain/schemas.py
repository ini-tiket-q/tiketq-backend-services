from pydantic import BaseModel, Field, HttpUrl, StringConstraints
from typing import Optional, Literal, Annotated
from datetime import datetime, date

# -------------------------------
# Enum-like Literals
# -------------------------------
BookingStatus = Literal["INCOMPLETE", "PAID", "CANCELLED"]
PaymentStatus = Literal["PENDING", "PAID", "FAILED"]
PassengerType = Literal["ADULT", "CHILD", "INFANT"]
FlightStatus = Literal["SCHEDULED", "DELAYED", "CANCELLED", "DEPARTED", "ARRIVED"]

# -------------------------------
# Constrained Types
# -------------------------------
AirportCode = Annotated[str, StringConstraints(min_length=3, max_length=3)]
AirlineCode = Annotated[str, StringConstraints(min_length=2, max_length=3)]


# -------------------------------
# City Schema
# -------------------------------
class CitySchema(BaseModel):
    code: AirportCode
    city_name: str


# -------------------------------
# Airline Schema
# -------------------------------
class AirlineSchema(BaseModel):
    flight_code: AirlineCode
    flight_name: str
    flight_image: Optional[HttpUrl] = None


# -------------------------------
# Flight Schema
# -------------------------------
class FlightSchema(BaseModel):
    id: Optional[str]
    airline_code: AirlineCode
    flight_from: AirportCode
    flight_to: AirportCode
    flight_route: Optional[str] = None
    flight_date: date
    departure_time: datetime
    arrival_time: datetime
    flight_transit: Optional[str] = None
    transit_info: Optional[str] = None
    flight_class: Optional[str] = None
    flight_seat: Optional[int] = None
    available_seat: Optional[int] = None
    baggage_capacity: Optional[str] = None
    facilities: Optional[str] = None
    adult_count: Optional[int] = None
    child_count: Optional[int] = None
    infant_count: Optional[int] = None
    publish_price: Optional[float] = None
    tax: Optional[float] = None
    total_fare: Optional[float] = None
    show_nta_price: Optional[float] = None
    real_nta_price: Optional[float] = None
    status: FlightStatus = "SCHEDULED"


# -------------------------------
# Booking Schema
# -------------------------------
class BookingSchema(BaseModel):
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


# -------------------------------
# Passenger Schema
# -------------------------------
class PassengerSchema(BaseModel):
    id: Optional[str]
    booking_id: str
    passenger_type: PassengerType
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    id_card_number: Optional[str] = None


# -------------------------------
# Payment Schema
# -------------------------------
class PaymentSchema(BaseModel):
    id: Optional[str]
    booking_id: str
    provider: str
    status: PaymentStatus
    amount: float
    currency: str
    snap_token: Optional[str] = None
    redirect_url: Optional[str] = None
    raw_provider_payload: Optional[str] = None
    transaction_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# -------------------------------
# ETicket Schema
# -------------------------------
class ETicketSchema(BaseModel):
    id: Optional[str]
    booking_id: str
    ticket_number: str
    issued_at: Optional[datetime] = None
    document_url: Optional[HttpUrl] = None
