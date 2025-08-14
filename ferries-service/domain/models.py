# domain/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import List
from datetime import datetime

# ==== Read models ====
class FerryRoute(BaseModel):
    id: str
    origin: str
    destination: str
    operator: str

class FerrySchedule(BaseModel):
    id: str
    route_id: str
    vessel: str
    depart_time: datetime
    arrive_time: datetime
    price: float

# ==== Write models ====
class Passenger(BaseModel):
    full_name: str
    id_number: str

class BookingCreate(BaseModel):
    schedule_id: str
    passengers: List[Passenger]
    contact_email: EmailStr

# ==== Persisted entity ====
class Booking(BaseModel):
    id: str
    schedule_id: str
    passengers: List[Passenger]
    contact_email: EmailStr
    total_price: float
    status: str = Field(default="CONFIRMED")
    created_at: datetime
