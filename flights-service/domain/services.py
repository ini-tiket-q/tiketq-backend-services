# domain/services.py
from datetime import date
from typing import Optional
from .models import Flight
from .repository import FlightRepository

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
