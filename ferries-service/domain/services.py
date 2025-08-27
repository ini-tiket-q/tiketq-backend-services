from domain.models import FerryBookingRequest, FerryBookingResponse
from adapters.external_api import get_sindo_routes


# Booking list local cache (opsional, bisa dipakai untuk debug)
_local_bookings = []



def get_ferry_schedules(origin: str = None, destination: str = None, date: str = None):
    # Ambil routes dari API Sindo
    data = get_sindo_routes()
    records = data.get("data", {}).get("records", [])

    # Filter manual (origin/destination) kalau diperlukan
    if origin:
        records = [r for r in records if r["name"].lower().startswith(origin.lower())]
    if destination:
        records = [r for r in records if r["name"].lower().endswith(destination.lower())]

    return {"schedules": records}




# def handle_ferry_booking(request: FerryBookingRequest):
#     booking_res = create_sindo_booking(
#         request.schedule_id,
#         request.passengers,
#         request.requirements.dict()
#     )

#     # simpan di local memory (opsional)
#     _local_bookings.append(booking_res)

#     return booking_res


# def get_all_bookings():
#     """Return local cache bookings (not official Sindo API)."""
#     return _local_bookings

