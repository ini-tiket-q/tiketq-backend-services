from fastapi import APIRouter, HTTPException, Query
from domain.models import FerryBookingRequest
from domain import services

router = APIRouter(prefix="/ferries", tags=["Ferries"])


# # ==========================
# # Schedules
# # ==========================
# @router.get("/schedules")
# def list_schedules(
#     origin: str = Query(None, description="Origin port ID"),
#     destination: str = Query(None, description="Destination port ID"),
#     date: str = Query(None, description="Departure date (YYYY-MM-DD)")
# ):
#     """
#     Ambil jadwal ferry dari Sindo API.
#     - Jika hanya `origin` diberikan → return daftar route
#     - Jika `origin`, `destination`, dan `date` diberikan → return trips
#     """
#     try:
#         return services.get_ferry_schedules(origin, destination, date)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules")
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


# # ==========================
# # Booking
# # ==========================
# @router.post("/book")
# def book_ferry(req: FerryBookingRequest):
#     """
#     Buat booking ferry di Sindo API.
#     """
#     try:
#         return services.handle_ferry_booking(req)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # ==========================
# # Admin/debug (local cache)
# # ==========================
# @router.get("/bookings")
# def list_all_bookings():
#     """
#     Get all cached ferry bookings (local memory).
#     Hanya untuk debug, bukan data resmi dari Sindo.
#     """
#     return services.get_all_bookings()
