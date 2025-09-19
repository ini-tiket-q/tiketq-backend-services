# PYDANTIC MODELS FOR FERRY SERVICE
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator, model_validator
from typing import Any, Dict, List, Literal, Optional
from datetime import date, datetime


class PassengerType(str, Enum):
    ADULT = "ADULT"
    CHILD = "CHILD"
    INFANT = "INFANT"

class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class FerryClass(str, Enum):
    ECONOMY = "Economy Class"
    BUSINESS = "Business Class"
    FIRST = "First Class"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    E_WALLET = "e_wallet"
    QR_CODE = "qr_code"

class PaymentGateway(str, Enum):
    MIDTRANS = "midtrans" 

class Passenger(BaseModel):
    type: PassengerType                                         
    title: Literal["MR", "MRS", "MS", "MISS"]                   
    name: str = Field(..., min_length=1, max_length=100)
    passport_no: str = Field(..., min_length=5, max_length=20)
    nationality: str = Field(..., min_length=2, max_length=3)
    issuing_country: str = Field(..., min_length=2, max_length=3)
    date_of_birth: date                   
    passport_expiry: date
    passport_issue: date
    
    @model_validator(mode='after')
    def validate_passport_dates(self):
        if self.passport_expiry <= date.today():
            raise ValueError('Passport has expired')
        if self.passport_issue >= self.passport_expiry:
            raise ValueError('Passport issue date must be before expiry date')
        if self.passport_issue >= date.today():
            raise ValueError('Passport issue date cannot be in the future')
        return self


class ContactInfo(BaseModel):
    email: EmailStr
    confirm_email: EmailStr
    mobile_phone: str = Field(..., min_length=8, max_length=15)
    whatsapp_no: Optional[str] = Field(None, min_length=8, max_length=15)
 
    @field_validator('confirm_email')
    @classmethod
    def emails_match(cls, v, values):
        if 'email' in values and v != values['email']:
            raise ValueError('Emails do not match')
        return v
    
    @field_validator('mobile_phone', 'whatsapp_no')
    @classmethod
    def validate_phone_format(cls, v):
        if v and not v.replace('+', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits and optional + prefix')
        return v


class TripSearchRequest(BaseModel):
    nationality: str = Field(..., min_length=2, max_length=3)
    origin: str = Field(..., min_length=3, max_length=20)
    destination: str = Field(..., min_length=3, max_length=20)
    depart_date: date
    pax: int = Field(1, ge=1, le=10)
    is_round_trip: bool = False
    return_date: Optional[date] = None
    ferry_class: FerryClass = FerryClass.ECONOMY

    @field_validator('origin', 'destination')
    @classmethod
    def validate_port_codes(cls, v):
        # Add specific validation for port codes if needed
        if len(v) < 3:
            raise ValueError('Port code must be at least 3 characters')
        return v.upper()

    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v, info):
        if info.data.get('is_round_trip') and not v:
            raise ValueError('Return date is required for round trip')
        if v and v <= info.data['depart_date']:
            raise ValueError('Return date must be after departure date')
        return v

    @field_validator("depart_date")
    @classmethod
    def validate_date_format_future(cls, v):
        from datetime import date
        if v < date.today():
            raise ValueError("Departure date cannot be in the past")
        return v
        
class FerryTripDisplay(BaseModel):
    trip_sched_id: str 
    departure_time: str 
    arrival_time: Optional[str] 
    status: Optional[str] = None
    trip_id: str 
    remarks: Optional[str] = None
    used_seat: str
    gate_open: Optional[str] 
    gate_close: Optional[str] 
    nationality: str
    origin: str
    destination: str
    depart_date: str
    return_date: Optional[str] = None
    pax: int
    ferry_class: str
    is_round_trip: bool
    
     # Add a validator to convert numeric fields to strings
    @field_validator('trip_sched_id', 'used_seat', mode='before')
    @classmethod
    def convert_to_string(cls, v):
        if v is not None:
            return str(v)
        return v
    
    @computed_field
    def route(self) -> str:
        return f"{self.origin}-{self.destination}"
    
    @computed_field
    def metadata(self) -> Dict[str, Any]:
        return {
        "trip_sched_id": self.trip_sched_id,
        "route": f"{self.origin}-{self.destination}",
        "departure_time": self.departure_time
        }
        
    class Config:
        from_attributes = True
        populate_by_name = True
      
    # @model_validator(mode='after')
    # def calculate_tax_and_total(self):
    #     self.tax_amount = self.base_price * self.tax_percentage
    #     self.total_price = self.base_price + self.tax_amount
    #     return self

class TripSearchResponse(BaseModel):
    status: str
    departure_trips: List[FerryTripDisplay]
    return_trips: Optional[List[FerryTripDisplay]] = None  
    
       
#create booking
class FerryBookingRequest(BaseModel):
    is_round_trip: bool
    departure_schedule_id: UUID
    return_schedule_id: Optional[UUID] = None
    ferry_class: FerryClass = FerryClass.ECONOMY
    passengers: List[Passenger] = Field(..., min_items=1, max_items=10)
    contact_info: ContactInfo
    payment_method: PaymentMethod
    payment_gateway: PaymentGateway = PaymentGateway.MIDTRANS
    metadata: Dict[str, Any] 
    
    @model_validator(mode='after')
    def validate_round_trip(self):
        if self.is_round_trip and not self.return_schedule_id:
            raise ValueError('Return schedule ID is required for round trips')
        return self

class FerryBookingResponse(BaseModel):
    booking_id: str #internal booking ID
    sindo_booking_id: str
    status: BookingStatus
    total_amount: float 
    currency: str = "IDR"
    transaction_id: Optional[str] = None   # Reference to transaction service
    payment_url: Optional[str] = None  # For Midtrans integration
    expires_at: datetime
    metadata: Dict[str, Any] = {}

class BookingSearchRequest(BaseModel):
    booking_id: Optional[str] = None
    passport_no: Optional[str] = None
    email: Optional[EmailStr] = None
    
class BookingDetails(BaseModel):
    booking_id: str
    sindo_booking_id: UUID
    status: BookingStatus
    total_amount: float
    currency: str
    passengers: List[Passenger]
    contact_info: ContactInfo
    departure_trip: Dict[str, Any]
    return_trip: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    payment_status: PaymentStatus
    transaction_id: Optional[str] = None
    
#for price calculation
class PriceBreakdown(BaseModel):
    base_fare: float
    tax_percentage: float
    tax_amount: float
    discount_amount: float = 0
    total_amount: float
    
    @model_validator(mode='after')
    def calculate_total(self):
        self.total_amount = self.base_fare + self.tax_amount - self.discount_amount
        return self

