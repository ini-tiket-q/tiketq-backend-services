import os
import requests
import uuid
from domain.models import Passenger

# FERRY_BASE_URL = os.getenv("EXTERNAL_FERRY_API_URL")
# FERRY_API_KEY = os.getenv("EXTERNAL_FERRIES_API_KEY")

# def create_ferry_booking(schedule_id: str, passengers: list):
#     """
#     Call external ferry API to create booking
#     """
#     url = f"{FERRY_BASE_URL}/Agent/Booking/Bookings"
#     headers = {"Authorization": f"Bearer {FERRY_API_KEY}"}
#     payload = {
#         "schedule_id": schedule_id,
#         "passengers": [p.dict() for p in passengers]
#     }
#     res = requests.post(url, json=payload, headers=headers)
#     res.raise_for_status()
#     return res.json()


def create_ferry_booking(schedule_id: str, passengers: list[Passenger]):
    """
    Mock external ferry API booking
    """
    booking_id = str(uuid.uuid4())
    total_price = 150.0 * len(passengers)  # mock harga Rp150k per orang

    return {
        "booking_id": booking_id,
        "status": "incomplete",
        "total_price": total_price
    }