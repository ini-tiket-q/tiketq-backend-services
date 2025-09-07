from fastapi import APIRouter, HTTPException, Query, Body
from domain.models import FerryBookingRequest
from domain import services

router = APIRouter(prefix="/ferries", tags=["Ferries"])

# Routes
@router.get("/routes")
def list_routes(search: str = Query(None, description="Search route by name or code")):
    """
    Ambil daftar rute ferry (origin → destination).
    """
    try:
        return services.get_ferry_routes(search)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Trips
@router.get("/trips")
def list_trips(
    origin: str = Query(..., description="Origin port code (ex: BTC)"),
    destination: str = Query(..., description="Destination port code (ex: HFC)"),
    date: str = Query(..., description="Departure date (YYYY-MM-DD)")
):
    """
    Ambil daftar trip / jadwal ferry untuk route tertentu.
    - Wajib isi origin, destination, dan date.
    """
    try:
        return services.get_ferry_trips(origin, destination, date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create booking
@router.post("/bookings")
def create_booking(booking_data: dict = Body(...)):
    """
    Buat booking baru ke Sindo API.
    """
    try:
        return services.create_ferry_booking(booking_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add booking details
@router.post("/bookings/{booking_id}/details")
def add_booking_detail(booking_id: str, passenger_data: dict = Body(...)):
    """
    Tambah detail penumpang ke booking (berdasarkan booking_id).
    """
    try:
        return services.add_ferry_booking_detail(booking_id, passenger_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get booking details
@router.get("/bookings/{booking_id}/details")
def list_booking_details(booking_id: str, search: str = Query(None, description="Cari nama penumpang")):
    """
    Ambil detail penumpang dari booking tertentu.
    Bisa difilter pakai `?search=Nama`.
    """
    try:
        return services.get_ferry_booking_details(booking_id, search)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# get coutries
@router.get("/countries")
def list_countries(search: str = Query(None, description="Search country by code or name")):
    """
    Ambil daftar negara dari Sindo API.
    - Bisa pakai query param ?search=INDONESIA atau ?search=ID
    """
    try:
        return services.get_ferry_countries(search)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete Booking
@router.delete("/bookings/{booking_id}/details/{booking_detail_id}")
def remove_booking_detail(booking_id: str, booking_detail_id: str):
    """
    Hapus booking detail (penumpang) dari booking.
    """
    try:
        return services.delete_booking_detail(booking_id, booking_detail_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# submit booking


# get available sectors
@router.get("/sectors")
def list_available_sectors():
    """
    Ambil daftar sektor ferry yang tersedia.
    """
    try:
        return services.get_available_sectors()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
