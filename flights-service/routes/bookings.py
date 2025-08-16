# routes/bookings.py
import json
from uuid import uuid4
from datetime import datetime, date
from dataclasses import asdict
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from math import ceil
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr

from domain.models import Booking, Passenger
from adapters.external_api import MmbcClient
from adapters.repository_sqlachemy import get_session, SqlAlchemyBookingRepo
from domain.services import (
    create_booking as svc_create_local,
    list_bookings as svc_list,
    get_booking as svc_get,
    create_payment_snap_stub,
    handle_midtrans_webhook_stub,
)


# ---------- core bookings ----------
bookings_router = APIRouter(prefix="/api/v1/flight-service", tags=["bookings"])

# --------- request models (aligned to your current schema) ----------
class PassengerIn(BaseModel):
    type: Literal["ADULT", "CHILD", "INFANT"]
    full_name: str
    dob: Optional[date] = None          # required for CHILD/INFANT (PDF)
    title: Optional[str] = None         # Mr/Mrs/Ms for ADULT; Mstr/Miss for CHILD/INFANT
    baggage: Optional[str] = None       # only relevant for AirAsia/Jetstar per PDF
    passport_number: Optional[str] = None
    passport_expired: Optional[date] = None

class ContactIn(BaseModel):
    full_name: str
    phone: str
    email: EmailStr

# models / in the same file where CreateBookingIn lives
class CreateBookingIn(BaseModel):
    offer_id: str
    contact: ContactIn
    passengers: list[PassengerIn]
    user_id: Optional[str] = None
    route_from: str
    route_to: str
    departure_time: datetime
    arrival_time: datetime
    flight_number: str
    airline: Optional[str] = None
    cabin: Optional[str] = None
    fare_amount: int
    fare_currency: str

    class Config:
        json_schema_extra = {
            "examples": [
                {
                  "summary": "Minimal local draft (1 adult)",
                  "value": {
                    "offer_id": "OFF-20250814-0001",
                    "contact": {
                      "full_name": "Zulkarnaini",
                      "phone": "+62811111111",
                      "email": "zul@example.com"
                    },
                    "passengers": [
                      {
                        "type": "ADULT",
                        "full_name": "Zulkarnaini",
                        "dob": "1990-01-01",
                        "title": "Mr",
                        "baggage": "",
                        "passport_number": "",
                        "passport_expired": "2030-01-01"
                      }
                    ],
                    "user_id": "user-123",
                    "route_from": "CGK",
                    "route_to": "SUB",
                    "departure_time": "2025-09-01T06:00:00Z",
                    "arrival_time": "2025-09-01T07:30:00Z",
                    "flight_number": "QG-724",
                    "airline": "Citilink",
                    "cabin": "Economy",
                    "fare_amount": 850000,
                    "fare_currency": "IDR"
                  }
                },
                {
                  "summary": "Remote booking to MMBC (adult + child)",
                  "value": {
                    "offer_id": "OFF-20250814-0002",
                    "contact": {
                      "full_name": "Lady Diana",
                      "phone": "+628123456789",
                      "email": "lady@example.com"
                    },
                    "passengers": [
                      {
                        "type": "ADULT",
                        "full_name": "Dodi Alfayed",
                        "dob": "1987-09-02",
                        "title": "Mr",
                        "baggage": "20 Kg",
                        "passport_number": "A1234567",
                        "passport_expired": "2031-12-31"
                      },
                      {
                        "type": "CHILD",
                        "full_name": "Nurul",
                        "dob": "2016-02-01",
                        "title": "Miss",
                        "baggage": "15 Kg",
                        "passport_number": "",
                        "passport_expired": "2031-12-31"
                      }
                    ],
                    "user_id": "user-456",
                    "route_from": "CGK",
                    "route_to": "DPS",
                    "departure_time": "2025-09-10T09:00:00Z",
                    "arrival_time": "2025-09-10T11:30:00Z",
                    "flight_number": "SJ-268",
                    "airline": "Sriwijaya Air",
                    "cabin": "Economy",
                    "fare_amount": 1450000,
                    "fare_currency": "IDR"
                  }
                }
            ]
        }

class MMBCIssueResponse(BaseModel):
    result: str
    tid: str
    tanggal: str
    flight: str
    flight_code: str
    kodebooking: str
    flight_route: str
    flight_departure: str
    flight_time: str
    flight_transit: str
    flight_infotransit: str
    flight_class: str
    flight_totalpassenger: str
    flight_datapassengers_json: str
    flight_contactdetails_json: str
    flight_currency: str
    flight_publishfare: str
    flight_tax: str
    flight_totalfare: str
    flight_realneta: str
    flight_shownta: str
    flight_bonus_agen: str
    flight_timelimit: str
    flight_bookingby: str
    flight_bookingby_kodeagen: str
    flight_issued_date: str
    flight_issued_ticketnumber: Optional[str] = None
    flight_issuedby: str
    flight_issuedby_kodeagen: str
    flight_statusbooking: str


# --------- helpers ----------
def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def _normalize_issue_payload(bk, prov: dict) -> dict:
    # 1) passengers JSON
    pax = []
    if getattr(bk, "passengers", None):
        for p in bk.passengers:
            pax.append({
                "passenger_title": getattr(p, "title", "") or "",
                "passenger_fullname": getattr(p, "full_name", "") or "",
                "passenger_type": getattr(p, "type", "Adult").title(),
                "passenger_baggageintl": "",
                "passenger_ffnumber": "",
                "passenger_dob": getattr(p, "dob", "") or "",
                "passenger_passportnumber": getattr(p, "passport_number", "") or "",
                "passenger_passportexpired": getattr(p, "passport_expired", "") or "",
            })
    else:
        for _ in range(getattr(bk, "pax_adult", 0)):
            pax.append({"passenger_title": "Mr/Ms", "passenger_fullname": "", "passenger_type": "Adult"})
        for _ in range(getattr(bk, "pax_child", 0)):
            pax.append({"passenger_title": "Mstr/Miss", "passenger_fullname": "", "passenger_type": "Child"})
        for _ in range(getattr(bk, "pax_infant", 0)):
            pax.append({"passenger_title": "", "passenger_fullname": "", "passenger_type": "Infant"})
    pax_json = json.dumps(pax, ensure_ascii=False)

    # 2) contact JSON
    contact_json = json.dumps({
        "contact_title": "",
        "contact_fullname": getattr(bk, "contact_name", "") or "",
        "contact_email": getattr(bk, "contact_email", "") or "",
        "contact_phone": getattr(bk, "contact_phone", "") or "",
    }, ensure_ascii=False)

    # 3) prefer provider fields
    airline_name  = prov.get("flight") or getattr(bk, "airline", "") or ""
    flight_code   = prov.get("flight_code") or getattr(bk, "flight_number", "") or ""
    kodebooking   = prov.get("kodebooking") or getattr(bk, "offer_id", "") or ""
    route_text    = prov.get("flight_route") or f"{getattr(bk, 'route_from', '')}-{getattr(bk, 'route_to', '')}"
    depart_text   = prov.get("flight_departure") or _fmt(getattr(bk, "departure_time", datetime.utcnow()))
    time_text     = prov.get("flight_time") or ""
    transit_text  = prov.get("flight_transit") or "Nonstop"
    infotransit   = prov.get("flight_infotransit") or ""
    currency      = prov.get("flight_currency") or getattr(bk, "fare_currency", "IDR")
    issued_tid    = prov.get("tid", "")
    issued_date   = prov.get("flight_issued_date") or _fmt(datetime.utcnow())
    ticket_number = prov.get("flight_issued_ticketnumber") or ""

    publishfare = int(prov.get("flight_publishfare", prov.get("publish", 0) or 0))
    tax         = int(prov.get("flight_tax", prov.get("tax", 0) or 0))
    totalfare   = int(prov.get("flight_totalfare", prov.get("totalfare", getattr(bk, "fare_amount", 0)) or 0))
    realnta     = int(prov.get("flight_realnta", 0))
    shown_ta    = int(prov.get("flight_shownta", 0))
    bonus_agen  = int(prov.get("flight_bonus_agen", 0))

    # 4) passenger count as string (PDF samples look stringy)
    if getattr(bk, "passengers", None):
        total_pax = str(len(bk.passengers))
    else:
        total_pax = str(int(getattr(bk, "pax_adult", 0)) + int(getattr(bk, "pax_child", 0)) + int(getattr(bk, "pax_infant", 0)))

    return {
        "result": "ok",
        "tid": issued_tid,
        "tanggal": _fmt(datetime.utcnow()),
        "flight": airline_name,
        "flight_code": flight_code,
        "kodebooking": kodebooking,
        "flight_route": route_text,
        "flight_departure": depart_text,
        "flight_time": time_text,
        "flight_transit": transit_text,
        "flight_infotransit": infotransit,
        "flight_totalpassenger": total_pax,
        "flight_datapassengers_json": pax_json,
        "flight_contactdetails_json": contact_json,  # <-- exact key
        "flight_currency": currency,
        "flight_publishfare": publishfare,
        "flight_tax": tax,                            # <-- prefer flight_tax
        "flight_totalfare": totalfare,
        "flight_realnta": realnta,
        "flight_shownta": shown_ta,
        "flight_bonus_agen": bonus_agen,
        "flight_timelimit": prov.get("flight_timelimit", ""),
        "flight_bookingby": prov.get("flight_bookingby", ""),
        "flight_issued_date": issued_date,
        "flight_issued_ticketnumber": ticket_number,
        "flight_statusbooking": "issued",
    }

def _to_ddmmyyyy(d: date | None) -> str:
    return d.strftime("%d-%m-%Y") if d else ""

def _pdf_title(p: PassengerIn) -> str:
    if p.type == "ADULT":
        return p.title if p.title in {"Mr", "Mrs", "Ms"} else "Mr"
    # CHILD or INFANT
    return "Mstr" if (p.title in {"Mr", "Mstr"}) else "Miss"

def _count(pax: list[PassengerIn], kind: str) -> int:
    k = kind.upper()
    return sum(1 for p in pax if p.type == k)

# --------- repos & providers ----------
def repo_dep(session = Depends(get_session)):
    return SqlAlchemyBookingRepo(session)

def mmbc_dep():
    return MmbcClient()

# --------- create booking (local or remote) ----------
  # you already import this above

@bookings_router.post("/bookings")
def create_booking_endpoint(
    payload: CreateBookingIn,
    mode: str = Query("local", regex="^(local|remote)$"),
    repo: SqlAlchemyBookingRepo = Depends(repo_dep),
    mmbc: MmbcClient = Depends(mmbc_dep),
):
    if mode == "local":
        domain_pax = [
            Passenger(
                id=None,
                booking_id=None,
                full_name=p.full_name,
                type=p.type,
                dob=p.dob,
                title=p.title,
                baggage=p.baggage,
                passport_number=p.passport_number,
                passport_expired=p.passport_expired,
            )
            for p in payload.passengers
        ]

        new_booking = Booking(
            id=str(uuid4()),
            offer_id=payload.offer_id,
            user_id=payload.user_id,
            contact_name=payload.contact.full_name,
            contact_email=payload.contact.email,
            contact_phone=payload.contact.phone,
            route_from=payload.route_from,
            route_to=payload.route_to,
            departure_time=payload.departure_time,
            arrival_time=payload.arrival_time,
            flight_number=payload.flight_number,
            airline=payload.airline,
            cabin=payload.cabin,
            fare_amount=payload.fare_amount,
            fare_currency=payload.fare_currency,
            created_at=datetime.utcnow(),
            status="DRAFT",
            pax_adult=sum(1 for p in payload.passengers if p.type == "ADULT"),
            pax_child=sum(1 for p in payload.passengers if p.type == "CHILD"),
            pax_infant=sum(1 for p in payload.passengers if p.type == "INFANT"),
        )

        bk = svc_create_local(repo, new_booking, domain_pax)
        return {"data": asdict(bk), "error": None, "meta": {}}

    # ---------- remote (MMBC) ----------
    pax = payload.passengers

    # PDF validation: CHILD/INFANT must have DOB
    for p in pax:
        if p.type in {"CHILD", "INFANT"} and not p.dob:
            raise HTTPException(status_code=422, detail="dob required for CHILD/INFANT")

    # counts (send as strings)
    adult = str(sum(1 for p in pax if p.type == "ADULT"))
    child = str(sum(1 for p in pax if p.type == "CHILD"))
    infant = str(sum(1 for p in pax if p.type == "INFANT"))

    # titles per PDF: Adult = Mr/Mrs/Ms; Child/Infant = Mstr/Miss
    def _pdf_title(p):
        if p.type == "ADULT":
            return p.title if p.title in {"Mr", "Mrs", "Ms"} else "Mr"
        return "Mstr" if (p.title in {"Mr", "Mstr"}) else "Miss"

    names = ":".join(f"{_pdf_title(p)} {p.full_name}" for p in pax)
    dobs  = ":".join(_to_ddmmyyyy(p.dob) if p.dob else "" for p in pax)
    bags  = ":".join((getattr(p, "baggage", "") or "") for p in pax)
    pp_no = ":".join((getattr(p, "passport_number", "") or "") for p in pax)
    pp_ex = ":".join(_to_ddmmyyyy(getattr(p, "passport_expired", None)) for p in pax)

    form = {
        "username": mmbc.user,
        #"password": mmbc.password,
        "agencode": getattr(mmbc, "agent_code", None),
        "flight":   payload.flight_number,     # e.g. "QG-724"
        "from":     payload.route_from,
        "to":       payload.route_to,
        "date":     _to_ddmmyyyy(payload.departure_time.date()),  # ISO -> dd-mm-yyyy
        "adult":    adult, "child": child, "infant": infant,
        "email":    payload.contact.email,
        "phone":    payload.contact.phone,
        "passengername": names,
        "dateofbirth":   dobs,                 # airline-dependent
        "baggagevolume": bags,                 # AirAsia/Jetstar only (else empty is fine)
        "passportnumber":  pp_no,              # international only (else "")
        "passportexpired": pp_ex,              # international only (else "")
    }

    prov = mmbc.post_booking(form)
    if not isinstance(prov, dict):
        raise HTTPException(status_code=502, detail="invalid provider response")

    booking_id = str(uuid4())
    booking = Booking(
            id=str(uuid4()),
            offer_id=prov.get("booking_code") or payload.offer_id,
            user_id=payload.user_id,
            contact_name=payload.contact.full_name,
            contact_email=payload.contact.email,
            contact_phone=payload.contact.phone,
            route_from=payload.route_from,
            route_to=payload.route_to,
            departure_time=payload.departure_time,
            arrival_time=payload.arrival_time,
            flight_number=payload.flight_number,
            airline=payload.airline,
            cabin=payload.cabin,
            fare_amount=payload.fare_amount,
            fare_currency=payload.fare_currency,
            created_at=datetime.utcnow(),
            status="WAITING",
            pax_adult=int(adult),
            pax_child=int(child),
            pax_infant=int(infant),
            provider_kodebooking=prov.get("booking_code"),  # 👈 KEY LINE
            passenger_details_json=json.dumps(prov.get("passenger_json", {})),
            booking_status=prov.get("status"),
        )

        # then persist it
    domain_pax = [
        Passenger(
            id=None,
            booking_id=booking.id,
            full_name=p.full_name,
            type=p.type,
            dob=p.dob,
            title=p.title,
            baggage=p.baggage,
            passport_number=p.passport_number,
            passport_expired=p.passport_expired,
        )
        for p in payload.passengers
        ]

    bk = svc_create_local(repo, booking, domain_pax)


    repo.create_booking(booking)  # or use your repo.save() or svc_create_local() if needed

    return {"data": asdict(booking), "error": None, "meta": {"provider": prov}}


# --------- list/get bookings (local) ----------
@bookings_router.get("/bookings")
def list_bookings_endpoint(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    repo: SqlAlchemyBookingRepo = Depends(repo_dep),
):
    items, total = svc_list(repo, user_id=user_id, email=email, phone=phone, page=page, per_page=per_page)
    payload = jsonable_encoder([asdict(i) for i in items])
    return {"data": payload, "error": None, "meta": {"page": page, "per_page": per_page, "total": total, "total_pages": ceil(total/per_page) if per_page else 1}}

@bookings_router.get("/bookings/{booking_id}")
def get_booking_endpoint(booking_id: str, repo: SqlAlchemyBookingRepo = Depends(repo_dep)):
    try:
        bk = svc_get(repo, booking_id)
        return {"data": jsonable_encoder(asdict(bk)), "error": None, "meta": {}}
    except KeyError:
        raise HTTPException(status_code=404, detail="Booking not found")

# Payments (stub Snap)
@bookings_router.post("/payments/{booking_id}/snap")
def create_snap_endpoint(booking_id: str, repo: SqlAlchemyBookingRepo = Depends(repo_dep)):
    bk = svc_get(repo, booking_id)
    pay = create_payment_snap_stub(repo, booking_id, bk.fare_amount, bk.fare_currency)
    return {"data": jsonable_encoder(asdict(pay)), "error": None, "meta": {}}

# Midtrans webhook (stub)
class MidtransWebhookIn(BaseModel):
    payment_id: str
    raw: dict = Field(default_factory=dict)

@bookings_router.post("/payments/midtrans/webhook")
def midtrans_webhook_endpoint(body: MidtransWebhookIn, repo: SqlAlchemyBookingRepo = Depends(repo_dep)):
    pay = handle_midtrans_webhook_stub(repo, body.payment_id, jsonable_encoder(body.raw))
    return {"data": jsonable_encoder(asdict(pay)), "error": None, "meta": {}}

# ---------- provider-facing bookings extras ----------
bookings_ext_router = APIRouter(prefix="/api/v1/flight-service", tags=["bookings-ext"])

def mmbc_dep():
    return MmbcClient()

# --- replace your existing issue_booking with this version ---
@bookings_router.post(
    "/bookings/{booking_id}/issue",
    response_model=MMBCIssueResponse,
    responses={409: {"description": "Booking is not ready to be issued"}}
)

def issue_booking(booking_id: str,
                  repo: SqlAlchemyBookingRepo = Depends(repo_dep),
                  mmbc: MmbcClient = Depends(mmbc_dep)):
    booking = repo.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking is not confirmed and cannot be issued"
        )

    if not booking.provider_kodebooking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking has no provider code"
        )

    try:
        prov = mmbc.issue(booking.provider_kodebooking)

        if prov.get("result") != "ok":
            raise HTTPException(status_code=400, detail=f"Issue failed: {prov.get('reason')}")

        return _normalize_issue_payload(booking, prov)  # ✅ here

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@bookings_ext_router.get("/bookings/{booking_id}/status")
def status_booking(booking_id: str,
                   repo: SqlAlchemyBookingRepo = Depends(repo_dep),
                   mmbc: MmbcClient = Depends(mmbc_dep)):
    bk = repo.get_booking_by_id(booking_id)
    if not bk:
        raise HTTPException(404, "Booking not found")
    kode = getattr(bk, "provider_booking_code", None) or bk.offer_id
    resp = mmbc.status_booking(kode)
    if resp.get("result") != "ok":
        raise HTTPException(404, detail=resp.get("reason","not found"))
    return {"data": resp, "error": None, "meta": {}}

@bookings_ext_router.get("/bookings/{booking_id}/eticket")
def eticket_booking(booking_id: str,
                    repo: SqlAlchemyBookingRepo = Depends(repo_dep),
                    mmbc: MmbcClient = Depends(mmbc_dep)):
    bk = repo.get_booking_by_id(booking_id)
    if not bk:
        raise HTTPException(404, "Booking not found")
    kode = getattr(bk, "provider_booking_code", None) or bk.offer_id
    resp = mmbc.eticket_link(kode)
    if resp.get("result") != "ok":
        raise HTTPException(404, detail=resp.get("reason","not found"))
    return {"data": resp, "error": None, "meta": {}}
