from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


### Passenger ###
class PassengerBase(BaseModel):
    full_name: str
    age: int
    id_number: str
    nationality: str
    seat_number: Optional[str] = None

class PassengerCreate(PassengerBase):
    booking_id: UUID


class PassengerRead(PassengerBase):
    id: UUID
    booking_id: UUID

    class Config:
        from_attributes = True


### Booking ###
class BookingBase(BaseModel):
    user_id: str
    trip_id: int
    return_trip_id: Optional[int] = None
    passenger_count: int
    payment_provider: str
    payment_reference: str
    gateway_transaction_id: str
    status: str = "PENDING"
    metadata: Optional[dict] = None


class BookingCreate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: UUID
    refund_id: Optional[UUID] = None
    agent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    passengers: List[PassengerRead] = []

    class Config:
        from_attributes = True