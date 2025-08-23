import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from domain.schemas_bookings import (
    GetPriceRequest, GetPriceResponse,
    PostBookingRequest, PostBookingResponse,
    KodeBookingRequest, GetIssuedResponseSuccess, GetIssuedResponseError,
    GetStatusBookingResponse,
    ResetPasswordRequest, ResetPasswordResponse
)
from domain.services_bookings import (
    get_issued_service, IssuedError, post_booking_service, 
    BookingError, get_status_service, StatusBookingError, 
    get_eticket_service, ETicketError, get_price_service, PriceError
    )

#from domain.mmbc_services import mmbc, MOCK_REMOTE
from domain.schemas_bookings import GetETicketRequest, GetETicketResponse, MMBCErrorResponse
from pydantic import BaseModel, Field
from typing import Optional
from adapters.store import BOOKING_STATUS
from adapters.mmbc_factory import mmbc
from domain.repository_bookings import BookingRepository


booking_repo = BookingRepository()

router = APIRouter(prefix="/json", tags=["MMBC Flight-Service (Bookings)"])

# -------------------------------
# Reset Password Endpoint
# -------------------------------
@router.post(
    "/resetpassword",
    response_model=ResetPasswordResponse,
    summary="Reset agent password",
    description="""
    Allows travel agents to reset their MMBC credentials using email, phone, and agent code.

    **Request Body**:
    - `username`: dummy  
    - `email`: user@bemail.com  
    - `phone`: 0812xxxxx  
    - `agencode`: JKT-111  
    - `newpassword`: Sd1231 (min. 6 characters)

    Returns success message or reason for failure.
    """,
    responses={
        200: {"description": "Password reset success"},
        400: {"description": "Validation error / reset failed"},
        500: {"description": "Internal server error"},
    }
)
async def reset_password(req: ResetPasswordRequest):
    result = await mmbc.reset_password(**req.dict())

    if result.get("result") == "no":
        raise HTTPException(status_code=400, detail=result.get("reason", "Reset failed"))

    return result

# -------------------------------
# Get Price Endpoint
# -------------------------------
@router.post(
    "/getprice-json",
    response_model=GetPriceResponse,
    responses={
        200: {"description": "Price retrieved", "model": GetPriceResponse},
        404: {"description": "No result / route not found", "model": MMBCErrorResponse},
        500: {"description": "Internal server error"},
    },
    summary="Check flight price",
    description="Retrieve flight fare, tax, seat info for a specific route/date."
)
async def get_price(req: GetPriceRequest):
    try:
        return await get_price_service(req)

    except PriceError as e:
        return JSONResponse(
            status_code=404,
            content={"result": "no", "reason": e.reason}
        )
    
# -------------------------------
# Post Bookings Endpoint
# -------------------------------
@router.post(
    "/postbooking-json",
    response_model=PostBookingResponse,
    summary="Book a flight",
    description="""
Creates a new booking on MMBC. This can be used by both guests and registered users.
""",
responses={
    200: {"description": "Booking success", "model": PostBookingResponse},
    400: {"description": "Booking failed", "model": MMBCErrorResponse},
    500: {"description": "Internal server error"},
})
async def post_booking(req: PostBookingRequest):
    try:
        result = await post_booking_service(req)

        if result.get("result") != "no":
            kodebooking = result.get("kodebooking")
        if kodebooking:
            booking_repo.set_status(kodebooking, "incomplete")


        return result

    except BookingError as e:
        return JSONResponse(
            status_code=400,
            content=e.full_body  # MMBC might include flight_code, seat info, message, etc.
        )

# -------------------------------
# Get Issued Endpoint
# -------------------------------
@router.post(
    "/getissued-json",
    response_model=GetIssuedResponseSuccess,
    responses={
        200: {"description": "Issued ticket retrieved", "model": GetIssuedResponseSuccess},
        403: {"description": "Booking not paid", "model": GetIssuedResponseError},
        404: {"description": "Booking not found", "model": GetIssuedResponseError},
        410: {"description": "Booking expired", "model": GetIssuedResponseError},
        400: {"description": "Other error", "model": GetIssuedResponseError},
    },
    summary="Check if booking is issued",
    description="Returns full ticket + passenger info if issued."
)
async def get_issued(req: KodeBookingRequest):
    if booking_repo.get_status(req.kodebooking) != "PAID":
        return JSONResponse(
            status_code=403,
            content={
                "result": "no",
                "reason": "Sisa saldo tidak cukup untuk Issued tiket, sisa saldo anda adalah 0."
            }
        )

    try:
        result = await get_issued_service(kodebooking=req.kodebooking)
        return result

    except IssuedError as e:
        reason = e.reason.lower()
        if "expired" in reason:
            return JSONResponse(status_code=410, content={"result": "no", "reason": e.reason})
        elif "sisa saldo" in reason:
            return JSONResponse(status_code=403, content={"result": "no", "reason": e.reason})
        elif "tidak ditemukan" in reason:
            return JSONResponse(status_code=404, content={"result": "no", "reason": e.reason})
        else:
            return JSONResponse(status_code=400, content={"result": "no", "reason": e.reason})

# -------------------------------
# Get Booking Status Endpoint
# -------------------------------
@router.post(
    "/getstatusbooking-json",
    response_model=GetStatusBookingResponse,
    responses={
        200: {"description": "Booking status retrieved", "model": GetStatusBookingResponse},
        404: {"description": "Booking not found", "model": MMBCErrorResponse},
        500: {"description": "Internal server error"},
    },
    summary="Check booking status",
    description="Retrieves full details and status of a booking using its booking code."
)
async def get_status(req: KodeBookingRequest):
    try:
        return await get_status_service(req.kodebooking)

    except StatusBookingError as e:
        return JSONResponse(
            status_code=404,
            content={"result": "no", "reason": e.reason}
        )

# -------------------------------
# Get Etiket
# -------------------------------
class GetETicketResponse(BaseModel):
    result: str
    eticket_url: Optional[str] = None

@router.post(
    "/getetiket-json",
    response_model=GetETicketResponse,
    responses={
        200: {"description": "E-ticket URL returned", "model": GetETicketResponse},
        404: {"description": "E-ticket not found", "model": MMBCErrorResponse},
        500: {"description": "Internal server error"},
    },
    summary="Retrieve E-Ticket",
    description="Fetches e-ticket download URL if booking is issued."
)
async def get_eticket(req: GetETicketRequest):
    try:
        result = await get_eticket_service(req.kodebooking)

        # Extract URL from reason
        match = re.search(r"https?://[^\s]+etiket-[\w\d]+\.pdf", result.get("reason", ""))
        url = match.group(0) if match else None

        return {"result": "ok", "eticket_url": url}

    except ETicketError as e:
        return JSONResponse(
            status_code=404,
            content={"result": "no", "reason": e.reason}
        )






class MidtransWebhook(BaseModel):
    order_id: str

@router.post("/simulate-payment", summary="Simulate payment callback (Midtrans mock)")
async def simulate_payment(req: MidtransWebhook):
    kodebooking = req.order_id

    if not booking_repo.has(kodebooking):
        raise HTTPException(404, detail="Booking not found")

    booking_repo.set_status(kodebooking, "PAID")

    return {"message": f"Booking {kodebooking} updated to 'paid'"}

