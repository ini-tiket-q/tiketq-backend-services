import os
import inspect
import json
from adapters.transaction_clients import create_transaction
from adapters.mmbc_factory import mmbc
from domain.schemas_bookings import (
    GetPriceRequest, GetPriceResponse,
    PostBookingRequest, PostBookingResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    KodeBookingRequest,
    GetIssuedResponseSuccess, GetIssuedResponseError,
    GetStatusBookingResponse, GetETicketRequest, GetETicketResponse
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

async def post_booking_service(req: PostBookingRequest, client_ip: str = "127.0.0.1"):
    kwargs = req.dict(by_alias=True)

    if inspect.iscoroutinefunction(mmbc.post_booking):
        result = await mmbc.post_booking(**kwargs)
    else:
        result = mmbc.post_booking(**kwargs)

    if result.get("result") == "no":
        raise BookingError(result.get("reason", "Booking failed"), result)

    try:
        # Parse contact + passengers
        contact_json = result.get("flight_contactdetails_json", "{}")
        contact_data = json.loads(contact_json)

        passengers_json = result.get("flight_datapassengers_json", "[]")
        passengers = json.loads(passengers_json)

        # ✅ Fix totals
        subtotal = float(result.get("publish", result["flight_totalfare"]))
        tax = float(result.get("flight_tax", 0))
        discount = 0
        total = subtotal + tax - discount

        # 🛒 Build transaction payload
        transaction_payload = {
            "email": contact_data.get("contact_email"),
            "transaction_type": "BOOKING",
            "currency": "IDR",
            "service_type": "FLIGHTS",
            "items": [
                {
                    "name": f"Flight {result.get('flight_code')} {result.get('flight_route')}",
                    "price": subtotal,
                    "quantity": len(passengers),
                    "description": f"Flight booking {result.get('flight_code')} on {result.get('flight_date')}",
                    "metadata": {
                        "departure_date": result.get("flight_date"),
                        "flight_number": result.get("flight_code"),
                        "airline": result.get("flight"),
                        "class": result.get("flight_class"),
                    },
                }
            ],
            "subtotal": subtotal,
            "tax": tax,
            "discount": discount,
            "total": total,
            "payment_method": "credit_card",
            "payment_gateway": "MIDTRANS",
            "transaction_metadata": {
                "order_id": f"FLIGHT-{result['kodebooking']}",
                "passenger_name": passengers[0]["passenger_fullname"] if passengers else None,
                "booking_reference": result["kodebooking"],
                "ip_address": client_ip,
            },
            "payment_metadata": {
                "bank_name": "BCA",
                "card_last_digits": "1234",
                "card_type": "visa",
            },
        }

        # ✅ Normalize payment status BEFORE sending to transaction-service
        raw_status = result.get("status", "PENDING")  # From MMBC/mock
        status_mapping = {
                    "COMPLETED": "SUCCESS",
                    "SETTLED": "SUCCESS",
                    "SETTLEMENT": "SUCCESS",   # Midtrans
                    "CAPTURE": "SUCCESS",      # Midtrans
                    "PAID": "SUCCESS",

                    "PENDING": "PROCESSING",
                    "IN_PROGRESS": "PROCESSING",

                    "EXPIRE": "EXPIRED",       # fix → matches DB exactly
                    "EXPIRED": "EXPIRED",

                    "CANCEL": "CANCELED",      # fix → matches DB spelling
                    "CANCELLED": "CANCELED",   # extra safeguard
                    "FAILURE": "FAILED",
                    "DENY": "FAILED",
                }

        normalized_status = status_mapping.get(raw_status.upper(), "PROCESSING")
        transaction_payload["status"] = normalized_status

        print(f"[DEBUG] Raw Status = {raw_status}, Normalized = {normalized_status}")


        # 🔗 Send to transaction-service
        transaction_response = await create_transaction(transaction_payload)

        # Store in result
        result["payment_status"] = normalized_status
        result["payment_response"] = transaction_response

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

    normalized = pay_status.upper()
    mapping = {
        "COMPLETED": "SUCCESS",
        "SETTLED": "SUCCESS",
        "SETTLEMENT": "SUCCESS",
        "CAPTURE": "SUCCESS",
        "PAID": "SUCCESS",

        "EXPIRE": "EXPIRED",
        "EXPIRED": "EXPIRED",

        "CANCEL": "CANCELED",
        "CANCELLED": "CANCELED",

        "FAILURE": "FAILED",
        "DENY": "FAILED",
    }
    normalized = mapping.get(normalized, normalized)

    if normalized in ("SUCCESS", "FAILED", "EXPIRED", "PROCESSING", "PENDING", "CANCELED", "REFUNDED"):
        return normalized

    return current_status



async def get_status_service(kodebooking: str) -> GetStatusBookingResponse:
    result = await mmbc.get_status_booking(kodebooking=kodebooking)

    if result.get("result") == "no":
        raise HTTPException(status_code=404, detail=result)

    # MMBC's reported status
    mm_status = result.get("flight_statusbooking", "waiting")

    # Check payment status via payment-service
    pay_status = reconcile_payment_status_if_needed(kodebooking, mm_status)

    # Build response aligned with schema
    response = GetStatusBookingResponse(
        result="ok",
        flight_statusbooking=mm_status,
        reason=result.get("reason", ""),
        payment_status=pay_status
    )

    return response


async def get_issued_service(kodebooking: str) -> GetIssuedResponseSuccess:
    # Check booking exists at MMBC
    status_resp = await mmbc.get_status_booking(kodebooking=kodebooking)
    if status_resp.get("result") == "no":
        raise HTTPException(status_code=404, detail=status_resp)

    # Reconcile payment first
    mm_status = status_resp.get("flight_statusbooking", "waiting")
    pay_status = reconcile_payment_status_if_needed(kodebooking, mm_status)

    if pay_status != "PAID":
        raise HTTPException(status_code=402, detail="Payment not completed")

    # Call MMBC to issue ticket
    issued = await mmbc.get_issued(kodebooking=kodebooking)

    if issued.get("result") == "no":
        # MMBC rejected issuance
        raise IssuedError(issued.get("reason", "Unknown error"))

    # Build response aligned with API docs
    response = GetIssuedResponseSuccess(
        result="ok",
        tid=issued.get("tid"),
        tanggal=issued.get("tanggal"),
        flight=issued.get("flight"),
        flight_code=issued.get("flight_code"),
        kodebooking=issued.get("kodebooking"),
        flight_route=issued.get("flight_route"),
        flight_departure=issued.get("flight_departure"),
        flight_time=issued.get("flight_time"),
        flight_transit=issued.get("flight_transit"),
        flight_infotransit=issued.get("flight_infotransit"),
        flight_class=issued.get("flight_class"),
        flight_totalpassenger=issued.get("flight_totalpassenger"),
        flight_datapassengers_json=issued.get("flight_datapassengers_json"),
        flight_contactdetails_json=issued.get("flight_contactdetails_json"),
        flight_currency=issued.get("flight_currency"),
        flight_publishfare=issued.get("flight_publishfare"),
        flight_tax=issued.get("flight_tax"),
        flight_totalfare=issued.get("flight_totalfare"),
        flight_realnta=issued.get("flight_realnta"),
        flight_shownta=issued.get("flight_shownta"),
        flight_bonus_agen=issued.get("flight_bonus_agen"),
        flight_timelimit=issued.get("flight_timelimit"),
        flight_bookingby=issued.get("flight_bookingby"),
        flight_bookingby_kodeagen=issued.get("flight_bookingby_kodeagen"),
        flight_issued_date=issued.get("flight_issued_date"),
        flight_issued_ticketnumber=issued.get("flight_issued_ticketnumber"),
        flight_issuedby=issued.get("flight_issuedby"),
        flight_issuedby_kodeagen=issued.get("flight_issuedby_kodeagen"),
        flight_statusbooking=issued.get("flight_statusbooking"),
    )
    return response







async def get_eticket_service(kodebooking: str) -> GetETicketResponse:
    result = await mmbc.get_eticket(kodebooking=kodebooking)

    if result.get("result") == "no":
        raise ETicketError(result.get("reason", "Failed to retrieve e-ticket"))

    # Build response aligned with schema
    response = GetETicketResponse(
        result=result.get("result", "no"),
        reason=result.get("reason", "")
    )
    return response



async def reset_password_service(req: ResetPasswordRequest) -> ResetPasswordResponse:
    return await mmbc.reset_password(**req.dict())
