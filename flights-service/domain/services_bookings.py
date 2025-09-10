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

async def get_issued_service(kodebooking: str) -> dict:
    result = await mmbc.get_issued(kodebooking=kodebooking)
    if result.get("result") == "no":
        raise IssuedError(result.get("reason", "Unknown error"))

    return result

async def get_status_service(kodebooking: str) -> GetStatusBookingResponse:
    result = await mmbc.get_status_booking(kodebooking=kodebooking)

    if result.get("result") == "no":
        raise HTTPException(status_code=404, detail=result)

    return result


async def get_eticket_service(kodebooking: str) -> dict:
    result = await mmbc.get_eticket(kodebooking=kodebooking)

    if result.get("result") == "no":
        raise ETicketError(result.get("reason", "Failed to retrieve e-ticket"))

    return result


async def reset_password_service(req: ResetPasswordRequest) -> ResetPasswordResponse:
    return await mmbc.reset_password(**req.dict())
