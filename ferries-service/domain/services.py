# from domain.models import FerryBookingRequest, FerryBookingResponse
# from adapters.external_api import create_ferry_booking
# from adapters.transaction_api import create_transaction

# def handle_ferry_booking(request: FerryBookingRequest) -> FerryBookingResponse:
#     # Step 1: create booking in external ferry API
#     booking_res = create_ferry_booking(request.schedule_id, request.passengers)

#     booking_id = booking_res.get("booking_id")
#     total_price = booking_res.get("total_price", 0.0)
#     status = booking_res.get("status", "incomplete")

#     # Step 2: create transaction in internal transaction-service
#     create_transaction(booking_id, total_price)

#     return FerryBookingResponse(
#         booking_id=booking_id,
#         status=status,
#         total_price=total_price,
#         message="Booking created and transaction recorded"
#     )

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