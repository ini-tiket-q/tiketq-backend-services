from domain.models import FerryBookingRequest, FerryBookingResponse
from adapters.external_api import get_sindo_routes, get_sindo_trips

# Booking list local cache (opsional, bisa dipakai untuk debug)
_local_bookings = []


def get_ferry_routes(search: str = None):
    """
    Ambil daftar rute ferry (origin → destination).
    """
    data = get_sindo_routes(search=search)
    records = data.get("data", {}).get("records", [])
    return {"routes": records}


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



def get_ferry_schedules(origin: str = None, destination: str = None, date: str = None):
    """
    Wrapper:
    - Tanpa origin/destination/date → return routes
    - Dengan origin+destination+date → return trips
    """
    if origin and destination and date:
        return get_ferry_trips(origin, destination, date)
    else:
        return get_ferry_routes()


