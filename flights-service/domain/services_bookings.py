import os
import inspect
import json
import logging
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
from adapters.transaction_clients import get_transaction_by_order_number

logger = logging.getLogger("uvicorn")
kodebooking_to_order_number = {}


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

async def store_booking_mapping(kodebooking: str, order_number: str):
    kodebooking_to_order_number[kodebooking] = order_number

async def get_order_number_by_kodebooking(kodebooking: str) -> str:
    return kodebooking_to_order_number.get(kodebooking)

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

    logger.info(f"Received get price request: {json.dumps(call_args)}")

    # If the method is a coroutine (async), await it
    if inspect.iscoroutinefunction(mmbc.get_price):
        result = await mmbc.get_price(**call_args)
    else:
        result = mmbc.get_price(**call_args)

    logger.debug(f"MMBC get_price response: {json.dumps(result)}")

    if result.get("result") == "no":
        logger.error(f"Price retrieval failed: {result.get('reason', 'No result')}")
        raise PriceError(result.get("reason", "No result"))

    return result

async def post_booking_service(req: PostBookingRequest, client_ip: str = "127.0.0.1"):
    kwargs = req.dict(by_alias=True)

    logger.info(f"Received post booking request from IP {client_ip} with payload: {json.dumps(kwargs)}")

    if inspect.iscoroutinefunction(mmbc.post_booking):
        result = await mmbc.post_booking(**kwargs)
    else:
        result = mmbc.post_booking(**kwargs)

    logger.debug(f"MMBC post_booking response: {json.dumps(result)}")

    if result.get("result") == "no":
        logger.error(f"Booking failed: {result.get('reason', 'Booking failed')}")
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

        logger.info(f"Transaction payload to be sent: {json.dumps(transaction_payload)}")

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

        logger.debug(f"Raw Status = {raw_status}, Normalized = {normalized_status}")

        # 🔗 Send to transaction-service
        transaction_response = await create_transaction(transaction_payload)

        order_number = transaction_response.get("order_number")

        if order_number:
            kodebooking_to_order_number[result["kodebooking"]] = order_number
            logger.info(f"[MAP] Stored: {result['kodebooking']} → {order_number}")
    

        # Store in result
        result["payment_status"] = normalized_status
        result["payment_response"] = transaction_response

        logger.info(f"Booking processed successfully for kodebooking={result['kodebooking']} with status={normalized_status}")

    except Exception as e:
        logger.exception(f"Exception during post booking processing: {e}")
        result["payment_status"] = "failed"
        result["payment_error"] = str(e)

    return result


async def reconcile_payment_status_if_needed(kodebooking: str, current_status: str) -> str:
    order_number = await get_order_number_by_kodebooking(kodebooking)

    if not order_number:
        logger.warning(f"No order_number found for {kodebooking}")
        return current_status

    try:
        trx = await get_transaction_by_order_number(order_number)
        pay_status = trx.get("status", "").upper()
        logger.debug(f"reconcile: order_number={order_number}, pay_status={pay_status}, current_status={current_status}")
        
    except Exception as e:
        logger.warning(f"Failed to fetch transaction for {order_number}: {e}")
        return current_status  # Early return if error

    # ✅ Only run this if pay_status was successfully set
    mapping = {
        "PAID": "SUCCESS",
        "COMPLETED": "SUCCESS",
        "SETTLED": "SUCCESS",
        "SETTLEMENT": "SUCCESS",
        "CAPTURE": "SUCCESS",
        "PENDING": "PROCESSING",
        "IN_PROGRESS": "PROCESSING",
        "EXPIRE": "EXPIRED",
        "EXPIRED": "EXPIRED",
        "CANCEL": "CANCELED",
        "CANCELLED": "CANCELED",
        "FAILURE": "FAILED",
        "DENY": "FAILED",
    }

    return mapping.get(pay_status, current_status)


async def get_status_service(kodebooking: str) -> GetStatusBookingResponse:
    logger.info(f"Received get status request for kodebooking={kodebooking}")
    result = await mmbc.get_status_booking(kodebooking=kodebooking)

    logger.debug(f"MMBC get_status_booking response: {json.dumps(result)}")

    if result.get("result") == "no":
        logger.error(f"Status retrieval failed for kodebooking={kodebooking}: {result.get('reason', '')}")
        raise HTTPException(status_code=404, detail=result)

    # MMBC's reported status
    mm_status = result.get("flight_statusbooking", "waiting")

    # Check payment status via payment-service
    pay_status = await reconcile_payment_status_if_needed(kodebooking, mm_status)

    # Build response aligned with schema
    response = GetStatusBookingResponse(
        result="ok",
        flight_statusbooking=mm_status,
        reason=result.get("reason", ""),
        payment_status=pay_status
    )

    logger.info(f"Status for kodebooking={kodebooking}: mm_status={mm_status}, payment_status={pay_status}")

    return response


async def get_issued_service(kodebooking: str) -> GetIssuedResponseSuccess:
    logger.info(f"Received get issued request for kodebooking={kodebooking}")
    # Check booking exists at MMBC
    status_resp = await mmbc.get_status_booking(kodebooking=kodebooking)
    logger.debug(f"MMBC get_status_booking (for issued) response: {json.dumps(status_resp)}")
    if status_resp.get("result") == "no":
        logger.error(f"Issued retrieval failed for kodebooking={kodebooking}: {status_resp.get('reason', '')}")
        raise HTTPException(status_code=404, detail=status_resp)

    # Reconcile payment first
    mm_status = status_resp.get("flight_statusbooking", "waiting")
    pay_status = await reconcile_payment_status_if_needed(kodebooking, mm_status)

    if pay_status != "SUCCESS":
        logger.warning(f"Cannot issue ticket for kodebooking={kodebooking}: payment_status={pay_status}")
        raise HTTPException(status_code=402, detail="Payment not completed")

    # Call MMBC to issue ticket
    issued = await mmbc.get_issued(kodebooking=kodebooking)
    logger.debug(f"MMBC get_issued response: {json.dumps(issued)}")

    if issued.get("result") == "no":
        # MMBC rejected issuance
        logger.error(f"MMBC rejected issuance for kodebooking={kodebooking}: {issued.get('reason', 'Unknown error')}")
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
    logger.info(f"Issued ticket for kodebooking={kodebooking} successfully.")
    return response


async def get_eticket_service(kodebooking: str) -> GetETicketResponse:
    logger.info(f"Received get eticket request for kodebooking={kodebooking}")
    result = await mmbc.get_eticket(kodebooking=kodebooking)

    logger.debug(f"MMBC get_eticket response: {json.dumps(result)}")

    if result.get("result") == "no":
        logger.error(f"ETicket retrieval failed for kodebooking={kodebooking}: {result.get('reason', '')}")
        raise ETicketError(result.get("reason", "Failed to retrieve e-ticket"))

    # Build response aligned with schema
    response = GetETicketResponse(
        result=result.get("result", "no"),
        reason=result.get("reason", "")
    )
    logger.info(f"ETicket retrieved for kodebooking={kodebooking}")
    return response


async def reset_password_service(req: ResetPasswordRequest) -> ResetPasswordResponse:
    logger.info(f"Received reset password request for email={req.email}")
    return await mmbc.reset_password(**req.dict())