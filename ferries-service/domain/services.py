# domain/services.py
from typing import List, Optional
from datetime import datetime
import uuid
from .models import FerryRoute, FerrySchedule, BookingCreate, Booking
from .repository import BookingRepository
from adapters.external_api import ExternalFerryAPIClient

class FerryService:
    def __init__(self, repo: BookingRepository, ext: ExternalFerryAPIClient):
        self.repo = repo
        self.ext = ext

    # --- Query use-cases ---
    def search_routes(self, origin: Optional[str], destination: Optional[str]) -> List[FerryRoute]:
        return self.ext.search_routes(origin, destination)

    def get_schedules(self, route_id: str, when: datetime) -> List[FerrySchedule]:
        return self.ext.get_schedules(route_id, when)

    # --- Command use-cases ---
    def create_booking(self, payload: BookingCreate) -> Booking:
        # Ambil schedule
        all_schedules = []
        for route in self.ext.search_routes(None, None):
            all_schedules.extend(self.ext.get_schedules(route.id, datetime.utcnow()))

        schedule = next((s for s in all_schedules if s.id == payload.schedule_id), None)
        if not schedule:
            raise ValueError("Schedule not found")

        total_price = schedule.price * len(payload.passengers)
        booking = Booking(
            id=str(uuid.uuid4()),
            schedule_id=schedule.id,
            passengers=payload.passengers,
            contact_email=payload.contact_email,
            total_price=total_price,
            created_at=datetime.utcnow(),
        )
        return self.repo.save(booking)

    def get_booking(self, booking_id: str) -> Optional[Booking]:
        return self.repo.get(booking_id)

    def list_bookings(self) -> List[Booking]:
        return self.repo.list()
