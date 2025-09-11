import os
import inspect
import json
from adapters.payment_clients import create_payment
from adapters.mmbc_factory import mmbc
from domain.schemas_bookings import (
    GetPriceRequest, GetPriceResponse,
    PostBookingRequest, PostBookingResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    KodeBookingRequest,
    GetIssuedResponseSuccess, GetIssuedResponseError,
    GetStatusBookingResponse
)
from fastapi import HTTPException
from adapters.payment_db_reader import get_payment_status_by_order_id


class PriceError(Exception):
    def __init__(self, reason: str):
        self.reason = reason

class IssuedError(Exception):
    def __init__(self, reason: str):
        self.reason = reason

class BookingError(Exception):
    def __init__(self, reason: str, full_body: dict):
        self.reason = reason
        self.full_body = full_body       

class StatusBookingError(Exception):
    def __init__(self, reason: str):
        self.reason = reason

class ETicketError(Exception):
    def __init__(self, reason: str):
        self.reason = reason        


async def get_price_service(req: GetPriceRequest) -> GetPriceResponse:
    call_args = dict(
        flight=req.flight,
        from_=req.from_,
        to=req.to,
        date=req.date,
        adult=req.adult,
        child=req.child,
        infant=req.infant,
    )

    # If the method is a coroutine (async), await it
    if inspect.iscoroutinefunction(mmbc.get_price):
        result = await mmbc.get_price(**call_args)
    else:
        result = mmbc.get_price(**call_args)

    if result.get("result") == "no":
        raise PriceError(result.get("reason", "No result"))

    return result




async def post_booking_service(req: PostBookingRequest):
    kwargs = req.dict(by_alias=True)

    if inspect.iscoroutinefunction(mmbc.post_booking):
        result = await mmbc.post_booking(**kwargs)
    else:
        result = mmbc.post_booking(**kwargs)

    if result.get("result") == "no":
        raise BookingError(result.get("reason", "Booking failed"), result)

    # 💳 Payment Integration
    try:
        # Parse contact details from stringified JSON
        contact_json = result.get("flight_contactdetails_json", "{}")
        contact_data = json.loads(contact_json)

        # Optional: parse passenger count from passenger JSON
        passengers_json = result.get("flight_datapassengers_json", "[]")
        passengers = json.loads(passengers_json)

        payment_payload = {
            "order_id": f"FLIGHT-{result['kodebooking']}",
            "amount": float(result["flight_totalfare"]),
            "payment_method": "credit_card",  # or make this dynamic later
            "customer_details": {
                "first_name": contact_data.get("contact_fullname", "").split(" ")[0],
                "last_name": " ".join(contact_data.get("contact_fullname", "").split(" ")[1:]),
                "email": contact_data.get("contact_email"),
                "phone": contact_data.get("contact_phone")
            },
            "item_details": [
                {
                    "id": f"flight-{result['kodebooking']}",
                    "price": float(result["flight_totalfare"]),
                    "quantity": len(passengers),
                    "name": f"Flight Ticket {result.get('flight_route', result['flight_code'])}"
                }
            ],
            "description": f"Flight booking payment for {result['flight_code']}"
        }

        payment_response = await create_payment(payment_payload)

        result["payment_status"] = "initiated"
        result["payment_response"] = payment_response

    except Exception as e:
        result["payment_status"] = "failed"
        result["payment_error"] = str(e)

    return result

def reconcile_payment_status_if_needed(kodebooking: str, current_status: str) -> str:
    order_id = f"FLIGHT-{kodebooking}"
    pay_status = get_payment_status_by_order_id(order_id)

    print(f"[DEBUG] reconcile: order_id={order_id}, pay_status={pay_status}, current_status={current_status}")

    if not pay_status:
        return current_status

    if pay_status.upper() in ("SUCCESS", "PAID"):
        return "PAID"
    elif pay_status.upper() in ("FAILED", "EXPIRED"):
        return pay_status.upper()

    return current_status



async def get_status_service(kodebooking: str) -> GetStatusBookingResponse:
    result = await mmbc.get_status_booking(kodebooking=kodebooking)

    if result.get("result") == "no":
        raise HTTPException(status_code=404, detail=result)

    # Internal reconciliation check (do not mutate MMBC status)
    mm_status = result.get("flight_statusbooking", "waiting")
    pay_status = reconcile_payment_status_if_needed(kodebooking, mm_status)

    # Optionally include payment info in a separate field (non-breaking)
    result["payment_status"] = pay_status

    return result


async def get_issued_service(kodebooking: str) -> dict:
    # First check MMBC knows the booking
    status_resp = await mmbc.get_status_booking(kodebooking=kodebooking)
    if status_resp.get("result") == "no":
        raise HTTPException(status_code=404, detail=status_resp)

    mm_status = status_resp.get("flight_statusbooking", "waiting")
    pay_status = reconcile_payment_status_if_needed(kodebooking, mm_status)

    if pay_status != "PAID":
        raise HTTPException(status_code=402, detail="Payment not completed")

    issued = await mmbc.get_issued(kodebooking=kodebooking)
    if issued.get("result") == "no":
        raise IssuedError(issued.get("reason", "Unknown error"))

    return issued






async def get_eticket_service(kodebooking: str) -> dict:
    result = await mmbc.get_eticket(kodebooking=kodebooking)

    if result.get("result") == "no":
        raise ETicketError(result.get("reason", "Failed to retrieve e-ticket"))

    return result


async def reset_password_service(req: ResetPasswordRequest) -> ResetPasswordResponse:
    return await mmbc.reset_password(**req.dict())
