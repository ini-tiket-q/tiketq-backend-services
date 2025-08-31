from domain.models import FerryBookingRequest, FerryBookingResponse
from adapters.external_api import (
    get_sindo_routes, 
    get_sindo_trips, 
    create_sindo_booking, 
    add_sindo_booking_detail,
    get_sindo_booking_details,
    get_sindo_countries
    )

# Booking list local cache (opsional, bisa dipakai untuk debug)
_local_bookings = []

# Get All Routes Provided
def get_ferry_routes(search: str = None):
    """
    Ambil daftar rute ferry (origin → destination).
    """
    data = get_sindo_routes(search=search)
    records = data.get("data", {}).get("records", [])
    return {"routes": records}

# Get All Trips for users to choose
def get_ferry_trips(origin: str, destination: str, date: str):
    """
    Ambil daftar trip / jadwal ferry dari API Sindo.
    """
    data = get_sindo_trips(origin, destination, date)

    # Kalau API balikin list langsung
    if isinstance(data, list):
        records = data
    else:
        # fallback kalau ada format lain
        records = data.get("data", {}).get("records", [])

    return {"trips": records}



# Create Booking
def create_ferry_booking(booking_data: dict):
    """
    Kirim booking ke API Sindo.
    """
    data = create_sindo_booking(booking_data)
    return data


# Add booking details
def add_ferry_booking_detail(booking_id: str, passenger_data: dict):
    """
    Tambahkan detail penumpang ke booking Sindo.
    """
    data = add_sindo_booking_detail(booking_id, passenger_data)
    return data


# Get Booking details 
def get_ferry_booking_details(booking_id: str, search: str = None):
    """
    Ambil detail penumpang dari sebuah booking.
    """
    data = get_sindo_booking_details(booking_id, search=search)
    return data

# Get countries
def get_ferry_countries(search: str = None):
    """
    Ambil daftar negara dari API Sindo.
    """
    data = get_sindo_countries(search)
    records = data.get("data", {}).get("records", [])
    return {"countries": records}

