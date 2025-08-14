# domain/services.py
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from .models import Flight, Booking, Passenger, Payment
from .repository import FlightRepository, BookingRepository
from adapters.external_api import MmbcClient

def list_flights(repo: FlightRepository, *, frm: Optional[str]=None, to: Optional[str]=None, day: Optional[date]=None):
    return repo.list(frm=frm, to=to, day=day)

def get_flight(repo: FlightRepository, flight_id: str) -> Flight:
    return repo.get(flight_id)

def create_flight(repo: FlightRepository, flight: Flight) -> Flight:
    return repo.create(flight)

def list_flights_paginated(
    repo: FlightRepository, *,
    frm: Optional[str]=None,
    to: Optional[str]=None,
    day: Optional[date]=None,
    page: int = 1,
    per_page: int = 10,
    sort: Optional[str] = None,
):
    if hasattr(repo, "list_paginated"):
        return repo.list_paginated(frm=frm, to=to, day=day, page=page, per_page=per_page, sort=sort)
    items = list_flights(repo, frm=frm, to=to, day=day)
    total = len(items)
    items = sorted(items, key=lambda f: f.departure_time)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total

def search_flights_external(frm: str, to: str, date_iso: str, pax: int = 1, cabin: str | None = None) -> List[Dict[str, Any]]:
    """
    Orchestrates external search. Returns a list of dicts already ready for JSON.
    (No DB writes here.)
    """
    client = MmbcClient()
    results = client.search_schedules(frm, to, date_iso, pax, cabin)
    # If you need to normalize keys, do it here.
    return results

def create_booking(repo: BookingRepository, booking: Booking, passengers: list[Passenger]) -> Booking:
    return repo.create_booking(booking, passengers)

def list_bookings(repo: BookingRepository, **kwargs):
    return repo.list_bookings(**kwargs)

def get_booking(repo: BookingRepository, booking_id: str):
    return repo.get_booking(booking_id)

def create_payment_snap_stub(repo: BookingRepository, booking_id: str, amount: int, currency: str):
    pay = repo.create_payment_for_booking(booking_id, amount, currency)
    # stub Snap
    pay.snap_token = f"SNAP-{pay.id}"
    pay.redirect_url = f"https://example-snap.local/{pay.snap_token}"
    return pay

def handle_midtrans_webhook_stub(repo, payment_id, raw):
    # 1) mark payment paid (your existing method)
    payment = repo.mark_payment_paid(payment_id, raw_payload=raw)

    # 2) only confirm the booking for “paid” statuses
    status = (raw or {}).get("transaction_status") or (raw or {}).get("status")
    if status and status.lower() in {"capture", "settlement", "success", "paid"}:
        repo.confirm_booking(payment.booking_id)

    return payment

