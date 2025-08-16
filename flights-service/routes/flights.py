from datetime import date, datetime
from dataclasses import asdict
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict
from typing import List, Optional, Dict, Any
from math import ceil
from domain.models import Flight
from domain.services import list_flights_paginated, list_flights, get_flight, create_flight, search_flights_external
from adapters.repository_sqlachemy import SqlAlchemyFlightRepo, get_session


class FlightOut(BaseModel):
    id: str
    flight_number: str
    from_airport: str
    to_airport: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: str
    gate: Optional[str] = None
    terminal: Optional[str] = None
    status: str
    notes: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "b3409a01825e47da826bf06540",
                "flight_number": "TQ 102",
                "from_airport": "CGK",
                "to_airport": "SIN",
                "departure_time": "2025-08-15T09:30:00",
                "arrival_time": "2025-08-15T12:25:00",
                "aircraft_type": "A320",
                "gate": "A12",
                "terminal": "2",
                "status": "SCHEDULED",
                "notes": None
            }
        }
    }

class PaginationMeta(BaseModel):
    page: int = Field(1, ge=1, description="Current page number (1-based)")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items matching the filter")
    total_pages: int = Field(..., ge=0, description="Total number of pages")  # was ge=1



class EnvelopeList(BaseModel):
    data: List[FlightOut]
    error: Optional[str] = None
    meta: PaginationMeta

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "id": "b3409a01825e47da826bf06540",
                        "flight_number": "TQ 102",
                        "from_airport": "CGK",
                        "to_airport": "SIN",
                        "departure_time": "2025-08-15T09:30:00",
                        "arrival_time": "2025-08-15T12:25:00",
                        "aircraft_type": "A320",
                        "gate": "A12",
                        "terminal": "2",
                        "status": "SCHEDULED",
                        "notes": None
                    }
                ],
                "error": None,
                "meta": {"page": 1, "per_page": 10, "total": 25, "total_pages": 3}
            }
        }
    }

class EnvelopeOne(BaseModel):
    data: FlightOut
    error: Optional[str] = None
    meta: dict = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": {
                    "id": "b3409a01825e47da826bf06540",
                    "flight_number": "TQ 102",
                    "from_airport": "CGK",
                    "to_airport": "SIN",
                    "departure_time": "2025-08-15T09:30:00",
                    "arrival_time": "2025-08-15T12:25:00",
                    "aircraft_type": "A320",
                    "gate": "A12",
                    "terminal": "2",
                    "status": "SCHEDULED",
                    "notes": None
                },
                "error": None,
                "meta": {}
            }
        }
    }



router = APIRouter(prefix="/api/v1/flight-service", tags=["flights"])

class CreateFlightBody(BaseModel):
    flight_number: str = Field(min_length=2, max_length=10)
    from_airport: str = Field(min_length=3, max_length=3)
    to_airport: str   = Field(min_length=3, max_length=3)
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: str
    gate: str | None = None
    terminal: str | None = None
    status: str = "SCHEDULED"
    notes: str | None = None

    @field_validator("from_airport", "to_airport")
    @classmethod
    def iata(cls, v: str) -> str:
        if not (len(v) == 3 and v.isalpha()):
            raise ValueError("IATA must be 3 letters")
        return v.upper()

def repo_dep(session = Depends(get_session)):
    return SqlAlchemyFlightRepo(session)

@router.get(
    "/flights",
    response_model=EnvelopeList,
    summary="List flights",
    description=(
        "Returns a paginated list of flights. "
        "Filter by origin/destination (IATA) and date (YYYY-MM-DD). "
        "Use `page` and `per_page` for pagination."
    ),
)
def list_flights_endpoint(
        frm: str | None = Query(None, description="Filter by origin IATA (e.g., CGK)"),
        to: str | None = Query(None, description="Filter by destination IATA (e.g., SIN)"),
        date_: str | None = Query(None, description="Filter by departure date (YYYY-MM-DD)"),
        page: int = Query(1, ge=1, description="Page number (1-based)"),
        per_page: int = Query(10, ge=1, le=100, description="Items per page"),
        repo: SqlAlchemyFlightRepo = Depends(repo_dep),
    ):
        d = date.fromisoformat(date_) if date_ else None
        items, total = list_flights_paginated(
            repo, frm=frm, to=to, day=d, page=page, per_page=per_page
        )
        payload = jsonable_encoder([asdict(f) for f in items])
        total_pages = (total + per_page - 1) // per_page
        return {
            "data": payload,
            "error": None,
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }

class FlightSearchItemOut(BaseModel):
    flight_id: str
    flight_name: str
    flight_code: str
    flight_from: str
    flight_to: str
    flight_departure: str            # "HH:mm" or ISO string; PDF shows string time
    flight_arrival: str              # same format as above
    flight_duration: int | None = None  # minutes if you have it
    flight_price: int
    flight_currency: str = "IDR"
    flight_availableseat: int | None = None
    flight_transit: int | None = None      # number of stops
    flight_baggage: int | None = None      # kg
    flight_hand_baggage: int | None = None # kg
    flight_facilities: list[str] | None = None
    flight_logo: str | None = None
    flight_image: str | None = None

# --- Helper: pull value with multiple possible keys & default ---
def _first(d: Dict[str, Any], *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, "", "null"):
            return d[k]
    return default

# --- Helper: normalize one raw provider item into our spec ---
def _normalize_provider_item(raw: Dict[str, Any]) -> FlightSearchItemOut:
    # IDs & codes
    code = _first(raw,
        "flight_code", "code", "flight_iata", "flightnumber", "flight_number",
        default="UNKNOWN"
    )
    frm = str(_first(raw, "flight_from", "from", "origin", "from_airport", default=""))
    to  = str(_first(raw, "flight_to",   "to",   "destination", "to_airport", default=""))

    # Departure/arrival strings — accept multiple possible keys
    dep = _first(raw, "flight_departure", "etd", "flight_etd", "departure_time", default="")
    arr = _first(raw, "flight_arrival",   "eta", "flight_eta", "arrival_time",   default="")

    # Price & currency — MMBC commonly returns totalfare / flight_currency
    price = _first(raw, "flight_price", "totalfare", "price", default=0)
    try:
        price = int(float(str(price)))
    except Exception:
        price = 0
    currency = _first(raw, "flight_currency", "currency", default="IDR")

    return FlightSearchItemOut(
        flight_id=str(_first(raw, "flight_id", "id", default=f"{code}:{frm}-{to}")),
        flight_name=str(_first(raw, "flight_name", "airline", "flight", "carrier", default="")),
        flight_code=str(code),
        flight_from=frm,
        flight_to=to,
        flight_departure=str(dep),
        flight_arrival=str(arr),
        flight_duration=_first(raw, "flight_duration", "duration", default=None),
        flight_price=price,
        flight_currency=str(currency or "IDR"),
        flight_availableseat=_first(raw, "flight_availableseat", "available_seat", "seat", default=None),
        flight_transit=_first(raw, "flight_transit", "transit", "stops", default=None),
        flight_baggage=_first(raw, "flight_baggage", "baggage", "checked_baggage", default=None),
        flight_hand_baggage=_first(raw, "flight_hand_baggage", "hand_baggage", "cabin_baggage", default=None),
        flight_facilities=_first(raw, "flight_facilities", "facilities", default=None),
        flight_logo=_first(raw, "flight_logo", "logo", default=None),
        flight_image=_first(raw, "flight_image", "image", default=None),
    )

@router.get("/flights/search", summary="Search Flights",
            response_model=dict)  # envelope with data/meta
def search_flights(
    frm: str = Query(..., min_length=3, max_length=3, description="IATA of origin"),
    to: str  = Query(..., min_length=3, max_length=3, description="IATA of destination"),
    date_: str = Query(..., description="YYYY-MM-DD"),
    pax: int = Query(1, ge=1, le=9),
    cabin: str | None = Query(None, description="ECONOMY | BUSINESS | FIRST")
):
    raw_list = search_flights_external(frm.upper(), to.upper(), date_, pax, cabin)

    # Normalize each item to the PDF’s schema
    normalized = [_normalize_provider_item(item) for item in (raw_list or [])]

    # FastAPI auto-serializes Pydantic models
    return {
        "data": normalized,
        "error": None,
        "meta": {
            "provider": "MMBC",
            "count": len(normalized),
            "params": {"frm": frm.upper(), "to": to.upper(), "date_": date_, "pax": pax, "cabin": cabin}
        }
    }

@router.get(
    "/flights/{flight_id}",
    response_model=EnvelopeOne,
    summary="Get a flight by ID",
    responses={404: {"description": "Flight not found"}},
)
def get_flight_endpoint(flight_id: str, repo: SqlAlchemyFlightRepo = Depends(repo_dep)):
    try:
        f = get_flight(repo, flight_id)
        payload = jsonable_encoder(asdict(f))  # <-- serialize single dataclass
        return {"data": payload, "error": None, "meta": {}}
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")


@router.post(
    "/flights",
    status_code=201,
    summary="Create a flight",
    responses={
        201: {"description": "Flight created"},
        409: {"description": "Duplicate (flight_number + departure_time)"},
        422: {"description": "Validation error"},
    },
)
def create_flight_endpoint(body: CreateFlightBody, repo: SqlAlchemyFlightRepo = Depends(repo_dep)):
    try:
        created = create_flight(repo, Flight(id=None, **body.model_dump()))
        return {"data": {"id": created.id}, "error": None, "meta": {}}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

class PatchFlightBody(BaseModel):
    flight_number: Optional[str] = None
    from_airport: Optional[str] = Field(default=None, min_length=3, max_length=3)
    to_airport:   Optional[str] = Field(default=None, min_length=3, max_length=3)
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("from_airport", "to_airport")
    @classmethod
    def iata(cls, v: Optional[str]) -> Optional[str]:
        if v is None: return v
        if not (len(v) == 3 and v.isalpha()):
            raise ValueError("IATA must be 3 letters")
        return v.upper()

    @field_validator("arrival_time")
    @classmethod
    def arrival_after_dep_if_both_present(cls, v, info):
        dep = info.data.get("departure_time")
        if v is not None and dep is not None and v <= dep:
            raise ValueError("arrival_time must be after departure_time")
        return v
    
# PATCH
@router.patch(
    "/flights/{flight_id}",
    response_model=EnvelopeOne,
    summary="Update (partial) a flight",
    responses={
        200: {"description": "Updated"},
        404: {"description": "Flight not found"},
        422: {"description": "Validation error or business rule violation"},
    },
)
def patch_flight_endpoint(
    flight_id: str,
    body: PatchFlightBody,
    repo: SqlAlchemyFlightRepo = Depends(repo_dep)
):
    try:
        updated = repo.update(flight_id, **{k: v for k, v in body.model_dump().items() if v is not None})
        from dataclasses import asdict
        from fastapi.encoders import jsonable_encoder
        return {"data": jsonable_encoder(asdict(updated)), "error": None, "meta": {}}
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    except ValueError as e:
        # bad time order or unique conflict
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

# DELETE (soft delete)
@router.delete(
    "/flights/{flight_id}",
    status_code=204,
    summary="Soft delete a flight",
    responses={404: {"description": "Flight not found"}},
)
def delete_flight_endpoint(flight_id: str, repo: SqlAlchemyFlightRepo = Depends(repo_dep)):
    try:
        repo.soft_delete(flight_id)
        return
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    

