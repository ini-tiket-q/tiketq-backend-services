# routes/pricing.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from datetime import datetime
from adapters.external_api import MmbcClient
from adapters.repository_sqlachemy import get_session, SqlAlchemyBookingRepo

router = APIRouter(prefix="/api/v1/flight-service", tags=["pricing"])

# ---------- Models ----------
class PriceIn(BaseModel):
    frm: str
    to: str
    date_: str            # ISO e.g. "2025-09-01"
    flight_code: str      # e.g. "QG-724"
    adult: int = 1
    child: int = 0
    infant: int = 0

class PriceRefreshOut(BaseModel):
    booking_id: str
    currency: str
    previous_total: int
    new_total: int
    available_seat: int
    changed: bool
    message: str | None = None

# ---------- Helpers ----------
def _iso_to_ddmmyyyy(d: str) -> str:
    # robust parse: supports "YYYY-MM-DD" and full ISO timestamps
    return datetime.fromisoformat(d).strftime("%d-%m-%Y")

def _to_int(x, default=0) -> int:
    try:
        return int(float(str(x)))
    except Exception:
        return default
    
# ----- Normalizer to PDF spec -----
# Ensures the keys & types look like the PDF sample.
def _normalize_pdf_price(payload: dict) -> dict:
    return {
        "result":               payload.get("result", "ok"),
        "flight":               payload.get("flight"),                       # airline name
        "flight_code":          payload.get("flight_code"),                  # e.g. QG-724
        "flight_from":          payload.get("flight_from"),
        "flight_to":            payload.get("flight_to"),
        "flight_route":         payload.get("flight_route"),                 # e.g. CGK-SUB
        "flight_date":          payload.get("flight_date"),                  # e.g. 2018-05-30 (string)
        "flight_departure":     payload.get("flight_departure"),             # e.g. "30 May 2018 18:40"
        "flight_transit":       payload.get("flight_transit", "Nonstop"),
        "flight_infortransit":  payload.get("flight_infortransit"),
        "flight_time":          payload.get("flight_time"),                  # "18:40 - 20:20"
        "flight_class":         payload.get("flight_class"),
        "flight_availableseat": _int(payload.get("flight_availableseat")),
        "flight_baggage":       payload.get("flight_baggage"),
        "flight_facilities":    payload.get("flight_facilities", "-"),
        "publish":              _int(payload.get("publish")),
        "tax":                  _int(payload.get("tax")),
        "totalfare":            _int(payload.get("totalfare")),
        "adult":                str(payload.get("adult", "1")),
        "child":                str(payload.get("child", "0")),
        "infant":               str(payload.get("infant", "0")),
        "flight_currency":      payload.get("flight_currency", "IDR"),
    }


def mmbc_dep():
    # factory so FastAPI doesn’t expose constructor args as query params
    return MmbcClient()

def repo_dep(session = Depends(get_session)):
    return SqlAlchemyBookingRepo(session)

# ---------- Endpoints ----------
@router.post("/flights/price", summary="Check Price (PDF-conformant)")
def check_price(
    body: PriceIn,
    mmbc: MmbcClient = Depends(),
    # optional: return raw provider payload if you ever need it
    raw: bool = Query(False, description="If true, return provider payload as-is")
):
    ddmmyyyy = _iso_to_ddmmyyyy(body.date_)
    resp = mmbc.get_price(
        frm=body.frm.upper(),
        to=body.to.upper(),
        date_ddmmyyyy=ddmmyyyy,
        flight_code=body.flight_code,
        adult=body.adult, child=body.child, infant=body.infant,
    )

    if not isinstance(resp, dict) or resp.get("result") != "ok":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=resp.get("reason", "not found") if isinstance(resp, dict) else "not found")

    # When the provider already matches the PDF, this is basically a no-op.
    pdf_payload = _normalize_pdf_price(resp) if not raw else resp
    # Keep your service’s envelope structure:
    return {"data": pdf_payload, "error": None, "meta": {}}

@router.post("/bookings/{booking_id}/pricing/refresh", response_model=PriceRefreshOut)
def refresh_booking_price(
    booking_id: str,
    repo: SqlAlchemyBookingRepo = Depends(repo_dep),
    mmbc: MmbcClient = Depends(mmbc_dep),
):
    booking = repo.get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status != "INCOMPLETE":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking not refreshable")

    prov = mmbc.get_price(
        frm=booking.route_from,
        to=booking.route_to,
        date_ddmmyyyy=_iso_to_ddmmyyyy(booking.departure_time.date().isoformat()),
        flight_code=booking.flight_number,
        adult=booking.pax_adult, child=booking.pax_child, infant=booking.pax_infant
    )
    if not isinstance(prov, dict) or prov.get("result") != "ok":
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=prov.get("reason", "no result") if isinstance(prov, dict) else "no result"
        )

    prev_total = _to_int(getattr(booking, "fare_amount", 0))
    new_total  = _to_int(prov.get("totalfare", prev_total), default=prev_total)
    changed = new_total != prev_total
    new_currency = prov.get("flight_currency") or getattr(booking, "fare_currency", None) or "IDR"

    if changed:
        # persist only pricing fields via a narrow repo method
        repo.update_booking_pricing(booking_id=booking.id, fare_amount=new_total, fare_currency=new_currency)

    return PriceRefreshOut(
        booking_id=str(booking.id),
        currency=new_currency,
        previous_total=prev_total,
        new_total=new_total,
        available_seat=_to_int(prov.get("flight_availableseat"), default=0),
        changed=changed,
        message=(
            f"Price increased by {new_total - prev_total}" if changed and new_total > prev_total
            else f"Price decreased by {prev_total - new_total}" if changed
            else "No change"
        ),
    )
