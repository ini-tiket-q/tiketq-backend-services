from pydantic import BaseModel
from typing import List, Optional

class Passenger(BaseModel):
    name: str
    age: int
    nationality: str
    gender: str

class FerryBookingRequest(BaseModel):
    schedule_id: str
    passengers: List[Passenger]

class FerryBookingResponse(BaseModel):
    booking_id: str
    status: str
    total_price: float
    message: str

class FerryTransaction(BaseModel):
    transaction_id: str
    booking_id: str
    amount: float
    status: str   # pending / paid / cancelled
