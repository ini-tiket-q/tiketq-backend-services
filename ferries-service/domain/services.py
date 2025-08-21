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
from adapters.transaction_api import create_transaction

def handle_ferry_booking(request: FerryBookingRequest) -> FerryBookingResponse:
    # Step 1: Mock external booking
    booking_res = create_ferry_booking(request.schedule_id, request.passengers)

    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]
    status = booking_res["status"]

    # Step 2: Mock transaction
    transaction_res = create_transaction(booking_id, total_price)

    return FerryBookingResponse(
        booking_id=booking_id,
        status=status,
        total_price=total_price,
        message=f"Booking created. Transaction ID: {transaction_res['transaction_id']}"
    )
