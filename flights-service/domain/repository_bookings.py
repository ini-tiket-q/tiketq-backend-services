
from adapters.store import BOOKING_STATUS


class BookingRepository:
    def set_status(self, kodebooking: str, status: str) -> None:
        BOOKING_STATUS[kodebooking] = status

    def get_status(self, kodebooking: str) -> str:
        return BOOKING_STATUS.get(kodebooking)

    def has(self, kodebooking: str) -> bool:
        return kodebooking in BOOKING_STATUS
