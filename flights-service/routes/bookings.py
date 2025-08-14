from datetime import datetime, date
from dataclasses import asdict
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr

from domain.models import Booking, Passenger
from adapters.repository_sqlachemy import get_session, SqlAlchemyBookingRepo
from domain.services import (
    create_booking, list_bookings as list_bk, get_booking as get_bk,
    create_payment_snap_stub, handle_midtrans_webhook_stub
)

router = APIRouter(prefix="/api/v1/flight-service", tags=["bookings"])

class PassengerIn(BaseModel):
    type: Literal["ADULT","CHILD","INFANT"]
    full_name: str
    dob: Optional[date] = None
    id_no: Optional[str] = None

class ContactIn(BaseModel):
    full_name: str
    phone: str
    email: EmailStr

class CreateBookingIn(BaseModel):
    offer_id: str
    contact: ContactIn
    passengers: list[PassengerIn]
    user_id: Optional[str] = None
    # minimal itinerary echo from search result (needed to persist)
    route_from: str
    route_to: str
    departure_time: datetime
    arrival_time: datetime
    flight_number: str
    airline: Optional[str] = None
    cabin: Optional[str] = None
    fare_amount: int
    fare_currency: str

def repo_dep(session = Depends(get_session)):
    return SqlAlchemyBookingRepo(session)

@router.post("/bookings", status_code=201)
def create_booking_endpoint(body: CreateBookingIn, repo: SqlAlchemyBookingRepo = Depends(repo_dep)):
    pax_adult = sum(1 for p in body.passengers if p.type == "ADULT")
    pax_child = sum(1 for p in body.passengers if p.type == "CHILD")
    pax_infant= sum(1 for p in body.passengers if p.type == "INFANT")

    bk = Booking(
        id=None,
        user_id=body.user_id,
        contact_name=body.contact.full_name, contact_phone=body.contact.phone, contact_email=body.contact.email,
        status="INCOMPLETE",
        route_from=body.route_from, route_to=body.route_to,
        departure_time=body.departure_time, arrival_time=body.arrival_time,
        flight_number=body.flight_number, airline=body.airline, cabin=body.cabin,
        pax_adult=pax_adult, pax_child=pax_child, pax_infant=pax_infant,
        fare_amount=body.fare_amount, fare_currency=body.fare_currency,
        offer_id=body.offer_id
    )
    pax = [Passenger(id=None, booking_id=None, **p.model_dump()) for p in body.passengers]
    created = create_booking(repo, bk, pax)
    return {"data": {"booking_id": created.id, "status": created.status, "amount": created.fare_amount, "currency": created.fare_currency}, "error": None, "meta": {}}

@router.get("/bookings")
def list_bookings_endpoint(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    repo: SqlAlchemyBookingRepo = Depends(repo_dep)
):
    items, total = list_bk(repo, user_id=user_id, email=email, phone=phone, page=page, per_page=per_page)
    from math import ceil
    payload = jsonable_encoder([asdict(i) for i in items])
    return {"data": payload, "error": None, "meta": {"page": page, "per_page": per_page, "total": total, "total_pages": ceil(total/per_page) if per_page else 1}}

@router.get("/bookings/{booking_id}")
def get_booking_endpoint(booking_id: str, repo: SqlAlchemyBookingRepo = Depends(repo_dep)):
    try:
        bk = get_bk(repo, booking_id)
        return {"data": jsonable_encoder(asdict(bk)), "error": None, "meta": {}}
    except KeyError:
        raise HTTPException(status_code=404, detail="Booking not found")

# Payments (stub Snap)
@router.post("/payments/{booking_id}/snap")
def create_snap_endpoint(booking_id: str, repo: SqlAlchemyBookingRepo = Depends(repo_dep)):
    # lookup booking to get amount/currency
    bk = get_bk(repo, booking_id)
    pay = create_payment_snap_stub(repo, booking_id, bk.fare_amount, bk.fare_currency)
    return {"data": jsonable_encoder(asdict(pay)), "error": None, "meta": {}}

# Midtrans webhook (stub)
class MidtransWebhookIn(BaseModel):
    payment_id: str
    raw: dict = Field(default_factory=dict)

@router.post("/payments/midtrans/webhook")
def midtrans_webhook_endpoint(body: MidtransWebhookIn, repo: SqlAlchemyBookingRepo = Depends(repo_dep)):
    pay = handle_midtrans_webhook_stub(repo, body.payment_id, jsonable_encoder(body.raw))
    return {"data": jsonable_encoder(asdict(pay)), "error": None, "meta": {}}
