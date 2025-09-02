from pydantic import BaseModel, Field, HttpUrl, StringConstraints, EmailStr
from typing import Optional, Literal, Annotated, Any, Dict
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

# === Shared ===
class KodeBookingRequest(BaseModel):
    kodebooking: str

class MMBCErrorResponse(BaseModel):
    result: str = "no"
    reason: str

# ===  Get Price ===
class GetPriceRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    flight: str = Field(..., example="JT-792")
    from_: str = Field(..., alias="from", example="CGK")
    to: str = Field(..., example="DPS")
    date: str = Field(..., example="2025-09-01")
    adult: int = Field(..., example=1)
    child: int = Field(..., example=0)
    infant: int = Field(..., example=0)


class GetPriceResponse(BaseModel):
    result: str
    flight_id: str
    flight: str
    flight_code: str
    flight_image: str
    flight_availableseat: str
    flight_from: str
    flight_to: str
    flight_date: str
    flight_transit: str
    flight_infotransit: str
    flight_time: str
    flight_duration: Optional[str]
    adult: int
    child: int
    infant: int
    publish: int
    tax: int
    totalfare: int

    # These were causing 500 errors – make them optional
    flight_shownta: Optional[int] = None
    flight_realnta: Optional[int] = None



# ===  Post Booking ===
class PostBookingRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    flight: str = Field(..., example="JT-792")
    from_: str = Field(..., alias="from", example="CGK")
    to: str = Field(..., example="DPS")
    date: str = Field(..., example="2025-09-01")
    adult: int = Field(..., example=1)
    child: int = Field(..., example=0)
    infant: int = Field(..., example=0)
    email: EmailStr = Field(..., example="johndoe@example.com")
    phone: str = Field(..., example="+628123456789")
    passengername: str = Field(..., example="John Doe")
    dateofbirth: str = Field(..., example="1990-01-01")
    baggagevolume: Optional[str] = Field(None, example="20kg")


class PostBookingResponse(BaseModel):
    result: str
    tid: str
    tanggal: str
    flight: str
    flight_code: str
    kodebooking: str
    flight_route: str
    flight_departure: str
    flight_time: str
    flight_transit: str
    flight_infotransit: str
    flight_class: str
    flight_totalpassenger: str
    flight_datapassengers_json: str
    flight_contactdetails_json: str
    flight_currency: str
    flight_publishfare: str
    flight_tax: str
    flight_totalfare: str
    flight_realnta: str
    flight_shownta: str
    flight_bonus_agen: str
    flight_timelimit: str
    flight_bookingby: str
    flight_bookingby_kodeagen: str
    flight_issued_date: str
    flight_issued_ticketnumber: str
    flight_issuedby: str
    flight_issuedby_kodeagen: str
    flight_statusbooking: str
    reason: Optional[str] = ""



# ===  Get Issued ===
class GetIssuedResponseSuccess(BaseModel):
    result: str
    tid: Optional[str]
    tanggal: Optional[str]
    flight: Optional[str]
    flight_code: Optional[str]
    kodebooking: Optional[str]
    flight_route: Optional[str]
    flight_departure: Optional[str]
    flight_time: Optional[str]
    flight_transit: Optional[str]
    flight_infotransit: Optional[str]
    flight_class: Optional[str]
    flight_totalpassenger: Optional[str]
    flight_datapassengers_json: Optional[Any]
    flight_contactdetails_json: Optional[Any]
    flight_currency: Optional[str]
    flight_publishfare: Optional[str]
    flight_tax: Optional[str]
    flight_totalfare: Optional[str]
    flight_realnta: Optional[str]
    flight_shownta: Optional[str]
    flight_bonus_agen: Optional[str]
    flight_timelimit: Optional[str]
    flight_bookingby: Optional[str]
    flight_bookingby_kodeagen: Optional[str]
    flight_issued_date: Optional[str]
    flight_issued_ticketnumber: Optional[str]
    flight_issuedby: Optional[str]
    flight_issuedby_kodeagen: Optional[str]
    flight_statusbooking: Optional[str]


class GetStatusBookingResponse(GetIssuedResponseSuccess):
    pass  # Same structure


class GetIssuedResponseError(BaseModel):
    result: str = "no"
    reason: str


# ===  Get Status Booking ===
class GetStatusBookingResponse(BaseModel):
    result: str
    flight_statusbooking: Literal["issued", "waiting"]
    reason: Optional[str]


# ===  Reset Password ===
class ResetPasswordRequest(BaseModel):
    username: str = Field(..., example="johnuser123")
    email: EmailStr = Field(..., example="john@example.com")
    phone: str = Field(..., example="081234567890")
    agencode: str = Field(..., example="AGT001")
    newpassword: str = Field(..., example="NewSecureP@ss1")


class ResetPasswordResponse(BaseModel):
    result: str
    message: Optional[str]

# Request body to MMBC for getting e-ticket
class GetETicketRequest(BaseModel):
    kodebooking: str

# Direct response from MMBC API
class GetETicketResponse(BaseModel):
    result: str
    reason: str  # This contains either the error message or the PDF URL
