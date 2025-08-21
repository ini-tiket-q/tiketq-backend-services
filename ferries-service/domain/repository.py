from __future__ import annotations
from typing import Dict, Optional
from datetime import datetime
from .models import Booking, BookingStatus

class BookingRepository:
    def __init__(self):
        self._store: Dict[str, Booking] = {}

    def save(self, booking: Booking) -> Booking:
        self._store[booking.booking_id] = booking
        return booking

    def get(self, booking_id: str) -> Optional[Booking]:
        return self._store.get(booking_id)

    def update_status(self, booking_id: str, status: BookingStatus, payment_id: Optional[str] = None):
        bk = self._store[booking_id]
        bk.status = status
        if payment_id:
            bk.payment_id = payment_id
        bk.updated_at = datetime.utcnow()
        self._store[booking_id] = bk
        return bk
