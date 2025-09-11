from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from domain.models import (
    FerryBookingRequest, 
    FerryBookingResponse, 
    TripSearchRequest
)
from domain import services
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ferries"])

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

# Simple trip listing endpoint (for basic use cases)
@router.get("/trips")
def list_trips(
    departure: str = Query(..., description="Origin port code (ex: BTC)"),
    destination: str = Query(..., description="Destination port code (ex: HFC)"),
    date: str = Query(..., description="Departure date (YYYY-MM-DD)")
):
    """
    Ambil daftar trip / jadwal ferry untuk route tertentu.
    - Wajib isi origin, destination, dan date.
    """
    try:
        # Convert string date to date object
        depart_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Create a basic search request
        search_request = TripSearchRequest(
            nationality="ID",  # Default value
            departure=departure,
            destination=destination,
            depart_date=depart_date,
            pax=1,
            ferry_class="Economy Class",
            is_round_trip=False
        )
        
        # Use the search function
        result = services.search_ferry_trips(search_request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@router.get("/trips/oneway")
def search_oneway_trips(
    nationality: str = Query(..., description="Passenger nationality (country code)"),
    departure: str = Query(..., description="Departure port code"), 
    destination: str = Query(..., description="Arrival port code"), 
    date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    pax: int = Query(1, description="Number of passengers"),
    ferry_class: str = Query("Economy Class", description="Ferry class")
):
    try:
        # Convert string date to date object
        depart_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Create search request
        search_request = TripSearchRequest(
            nationality=nationality,
            departure=departure,
            destination=destination,
            depart_date=depart_date,
            pax=pax,
            ferry_class=ferry_class,
            is_round_trip=False
        )
        
        # Use the search function
        result = services.search_ferry_trips(search_request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # logger.error(f"Error in search_oneway_trips: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trips/search/roundtrip")
def search_roundtrip_trips(
    nationality: str = Query(..., description="Passenger nationality (country code)"),
    departure: str = Query(..., description="Departure port code"), 
    destination: str = Query(..., description="Arrival port code"), 
    depart_date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    return_date: str = Query(..., description="Return date in YYYY-MM-DD format"),
    pax: int = Query(1, description="Number of passengers"),
    ferry_class: str = Query("Economy Class", description="Ferry class")
):
    try:
        # Convert string dates to date objects
        depart_date_obj = datetime.strptime(depart_date, "%Y-%m-%d").date()
        return_date_obj = datetime.strptime(return_date, "%Y-%m-%d").date()
        
        # Create search request
        search_request = TripSearchRequest(
            nationality=nationality,
            departure=departure,
            destination=destination,
            depart_date=depart_date_obj,
            pax=pax,
            ferry_class=ferry_class,
            is_round_trip=True,
            return_date=return_date_obj
        )
        
        # Use the search function
        result = services.search_ferry_trips(search_request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Create booking
@router.post("/bookings", response_model=FerryBookingResponse)
async def create_booking(
    booking_data: FerryBookingRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new ferry booking with transaction service integration.
    """
    try:
        # Validate request
        if booking_data.is_round_trip and not booking_data.return_schedule_id:
            raise HTTPException(
                status_code=400,
                detail="Return schedule ID is required for round trips"
            )
        
        # Create booking
        booking_result = await services.create_ferry_booking(booking_data)
        
        # Add background task for confirmation email
        background_tasks.add_task(
            send_booking_confirmation,
            booking_data.contact_info.email,
            booking_result.booking_id
        )
        
        return booking_result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/bookings/v2")
# def create_booking_v2(booking_request: FerryBookingRequest):
#     try:
#         return services.create_ferry_booking_v2(booking_request)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

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
        booking_details = services.get_ferry_booking_details(booking_id, search)
        if not booking_details:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return booking_details
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


# Helper function for sending confirmation email
def send_booking_confirmation(email: str, booking_id: str):
    """
    Send booking confirmation email (placeholder implementation)
    """
    # This would be your actual email sending logic
    print(f"Sending confirmation email to {email} for booking {booking_id}")

