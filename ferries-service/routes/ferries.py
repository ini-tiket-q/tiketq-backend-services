# routes/ferries.py
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import Optional, List
from domain.models import FerryRoute, FerrySchedule, BookingCreate, Booking
from domain.repository import InMemoryBookingRepository
from domain.services import FerryService
from adapters.external_api import ExternalFerryAPIClient

router = APIRouter(prefix="/ferries", tags=["Ferries"])

def get_service() -> FerryService:
    repo = InMemoryBookingRepository()
    ext = ExternalFerryAPIClient()
    return FerryService(repo, ext)

@router.get("/routes", response_model=List[FerryRoute])
def list_routes(
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    svc: FerryService = Depends(get_service)
):
    return svc.search_routes(origin, destination)

@router.get("/schedules", response_model=List[FerrySchedule])
def list_schedules(
    route_id: str,
    date_str: Optional[str] = None,
    svc: FerryService = Depends(get_service)
):
    when = datetime.utcnow()
    if date_str:
        try:
            when = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    return svc.get_schedules(route_id, when)

@router.post("/bookings", response_model=Booking, status_code=201)
def create_booking(payload: BookingCreate, svc: FerryService = Depends(get_service)):
    try:
        return svc.create_booking(payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/bookings/{booking_id}", response_model=Booking)
def get_booking(booking_id: str, svc: FerryService = Depends(get_service)):
    bk = svc.get_booking(booking_id)
    if not bk:
        raise HTTPException(status_code=404, detail="Booking not found")
    return bk

@router.get("/bookings", response_model=List[Booking])
def list_bookings(svc: FerryService = Depends(get_service)):
    return svc.list_bookings()
