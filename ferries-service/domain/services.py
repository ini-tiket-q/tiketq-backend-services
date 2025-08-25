
from domain.models import FerryBookingRequest, FerryBookingResponse
from adapters.external_api import create_ferry_booking
from adapters.transaction_api import create_transaction, list_transactions

from adapters.transaction_api import (
    create_transaction, 
    list_transactions, 
    update_transaction_status
)
from domain.models import FerryBookingRequest, FerryBookingResponse
from adapters.external_api import create_ferry_booking
from adapters.external_api import get_mock_schedules

def get_ferry_schedules(origin: str = None, destination: str = None, date: str = None):
    schedules = get_mock_schedules()

    if origin:
        schedules = [s for s in schedules if s["origin"].lower() == origin.lower()]
    if destination:
        schedules = [s for s in schedules if s["destination"].lower() == destination.lower()]
    if date:
        schedules = [s for s in schedules if s["departure_time"].startswith(date)]

    return {"schedules": schedules}


def handle_ferry_booking(request: FerryBookingRequest) -> FerryBookingResponse:
    # Step 1: Mock external booking
    booking_res = create_ferry_booking(request.schedule_id, request.passengers)

    booking_id = booking_res["booking_id"]
    total = booking_res["total"]

    # Step 2: Mock transaction
    transaction_res = create_transaction(booking_id, total)

    return FerryBookingResponse(
        booking_id=booking_id,
        status="incomplete",
        subtotal=booking_res["subtotal"],
        tax=booking_res["tax"],
        discount=booking_res["discount"],
        total=total,
        items=booking_res["items"],
        metadata=booking_res["metadata"],
    )


def get_all_transactions():
    return list_transactions()

def change_transaction_status(transaction_id: str, new_status: str):
    return update_transaction_status(transaction_id, new_status)