from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from domain.models import FerryBookingRequest, TripSearchRequest
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

    
@router.get("/trips/oneway")
def oneway(
    nationality: str = Query(..., description="Passenger nationality (country code)"),
    origin: str = Query(..., description="Departure port code"), 
    destination: str = Query(..., description="Arrival port code"), 
    date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    pax: int = Query(1, description="Number of passengers"),
    ferry_class: str = Query("economy", description="Ferry class")
):
    try:
        result = services.get_ferry_oneway(nationality, origin, destination, date, pax, ferry_class)
         # Return only display data to frontend
        return {"status": "success", "data": result.get("display_data", [])}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trips/roundtrip")
def roundtrip(
    nationality: str = Query(..., description="Passenger nationality (country code)"),
    origin: str = Query(..., description="Departure port code"), 
    destination: str = Query(..., description="Arrival port code"), 
    depart_date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    return_date: str = Query(..., description="Return date in YYYY-MM-DD format"),
    pax: int = Query(1, description="Number of passengers"),
    ferry_class: str = Query("economy", description="Ferry class")
):
    try:
        result = services.get_ferry_roundtrip(
            nationality, origin, destination, 
            depart_date, return_date, pax, ferry_class
        )
         # Return only display data to frontend
        return {
            "status": "success",
            "departure_trips": result.get("display_data", {}).get("departure_trips", []),
            "return_trips": result.get("display_data", {}).get("return_trips", [])
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

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

@router.post("/bookings/v2")
def create_booking_v2(booking_request: FerryBookingRequest):
    try:
        return services.create_ferry_booking_v2(booking_request)
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


@router.post("/bookings/{booking_id}/submit")
def submit_booking(booking_id: str, email_confirmation: str = Query(...), remarks: str = Query("")):
    try:
        return services.submit_ferry_booking(booking_id, email_confirmation, remarks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get available sectors
@router.get("/sectors")
def list_available_sectors():
    """
    Ambil daftar sektor ferry yang tersedia.
    """
    try:
        return services.get_ferry_available_sectors()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
