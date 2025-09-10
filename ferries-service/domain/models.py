# PYDANTIC MODELS FOR FERRY SERVICE
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Any, Dict, List, Literal, Optional
from datetime import date, datetime

# Type Aliases for Ferry Service
PassengerType = Literal["ADULT", "CHILD", "INFANT"]
BookingStatus = Literal["PENDING", "CONFIRMED", "CANCELLED"]
PaymentStatus = Literal["PENDING", "PAID", "FAILED", "REFUNDED"]


class GenericResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    
class Passenger(BaseModel):
    type: PassengerType                                         # "Adult" atau "Child"
    title: Literal["MR", "MRS", "MS", "MISS"]                   # "Mr", "Mrs", "Ms"
    name: str                                                   # Nama sesuai passport
    passport_no: str
    nationality: str
    issuing_country: str
    date_of_birth: date                   
    passport_expiry: date
    passport_issue: date

#contact info
class BookingRequirements(BaseModel):
    email: EmailStr
    confirm_email: EmailStr
    mobile_phone: str
    whatsapp_no: Optional[str] = None
    
    @field_validator('confirm_email')
    @classmethod
    def emails_match(cls, v, values):
        if 'email' in values and v != values['email']:
            raise ValueError('Emails do not match')
        return v

class TripSearchRequest(BaseModel):
    is_round_trip: bool = False
    nationality: str
    origin: str                                          # port code (e.g., "BTC")
    destination: str
    depart_date: date
    return_date: Optional[date] = None
    pax: int = Field(1, ge=1, le=10)
    ferry_class: Literal["economy", "business", "first"] = "economy"
    
class TripSearchResponse(BaseModel):
    is_round_trip: bool = False
    nationality: str
    origin: str                                          # port code (e.g., "BTC")
    destination: str
    depart_date: date
    return_date: Optional[date] = None
    pax: int = Field(1, ge=1, le=10)
    ferry_class: Literal["economy", "business", "first"] = "economy"
    departure_trips: List[Dict[str, Any]] = Field(default_factory=list)  # For internal use
    return_trips: Optional[List[Dict[str, Any]]] = None  # For internal use
    
    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v, info):
        if info.data.get('is_round_trip') and not v:
            raise ValueError('Return date is required for round trip')
        if v and v <= info.data.get('date'):
            raise ValueError('Return date must be after departure date')
        return v
    
#create booking
class FerryBookingRequest(BaseModel):
    is_round_trip: bool
    # is_return_trip_open: bool
    departure_trip: dict  # Will contain the trip details from Sindo API
    return_trip: Optional[dict] = None
    ferry_class: str = "economy"
    schedule_id: str
    passengers: List[Passenger] = Field(..., min_items=1, max_items=10)
    requirements: BookingRequirements

class FerryBookingResponse(BaseModel):
    booking_id: str #internal booking ID
    sindo_booking_id: str
    status: BookingStatus
    subtotal: float
    tax: float = 0.0
    discount: float = 0.0
    total: float = Field(..., ge=0)
    items: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    currency: str = Field("IDR", pattern="^[A-Z]{3}$")
    payment_url: Optional[str] = None  # For Midtrans integration
    expires_at: datetime
