from fastapi import APIRouter, HTTPException, Query
from domain.models import FerryBookingRequest
from domain import services

router = APIRouter(prefix="/ferries", tags=["Ferries"])


@router.get("/routes")
def list_schedules(
    origin: str = Query(None, description="Origin port code (ex: BTC)"),
    destination: str = Query(None, description="Destination port code (ex: HFC)"),
    date: str = Query(None, description="Departure date (YYYY-MM-DD)")
):
    """
    Ambil jadwal ferry:
    - Tanpa query → daftar routes
    - Dengan query (origin, destination, date) → daftar trips
    """
    try:
        if origin and destination and date:
            return services.get_ferry_trips(origin, destination, date)
        else:
            return services.get_ferry_routes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

