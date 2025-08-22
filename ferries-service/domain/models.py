from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date

class Passenger(BaseModel):
    type: str                   # "Adult" atau "Child"
    title: str                  # "Mr", "Mrs", "Ms"
    name: str                   # Nama sesuai passport
    passport_no: str
    nationality: str
    issuing_country: str
    dob: date                   # Date of Birth
    passport_expiry: date
    passport_issue: date

class BookingRequirements(BaseModel):
    email: EmailStr
    confirm_email: EmailStr
    mobile_phone: str
    whatsapp_no: Optional[str]

class FerryBookingRequest(BaseModel):
    schedule_id: str
    passengers: List[Passenger]
    requirements: BookingRequirements

class FerryBookingResponse(BaseModel):
    booking_id: str
    status: str
    total_price: float
    message: str
