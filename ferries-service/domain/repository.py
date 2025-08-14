# domain/repository.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from .models import Booking
import uuid

class BookingRepository(ABC):
    @abstractmethod
    def save(self, booking: Booking) -> Booking:
        ...

    @abstractmethod
    def get(self, booking_id: str) -> Optional[Booking]:
        ...

    @abstractmethod
    def list(self) -> List[Booking]:
        ...

class InMemoryBookingRepository(BookingRepository):
    def __init__(self):
        self._store: Dict[str, Booking] = {}

    def save(self, booking: Booking) -> Booking:
        self._store[booking.id] = booking
        return booking

    def get(self, booking_id: str) -> Optional[Booking]:
        return self._store.get(booking_id)

    def list(self) -> List[Booking]:
        return list(self._store.values())
