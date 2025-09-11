import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from domain.schemas_bookings import (
    GetPriceRequest, GetPriceResponse,
    PostBookingRequest, PostBookingResponse,
    KodeBookingRequest, GetIssuedResponseSuccess, GetIssuedResponseError,
    GetStatusBookingResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    GetETicketRequest, GetETicketResponse, MMBCErrorResponse
)
from domain.services_bookings import (
    get_issued_service, IssuedError, post_booking_service,
    BookingError, get_status_service, StatusBookingError,
    get_eticket_service, ETicketError, get_price_service, PriceError
)
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/json", tags=["MMBC Flight-Service (Bookings)"])

# -------------------------------
# Reset Password Endpoint
# -------------------------------
@router.post(
    "/resetpassword",
    response_model=ResetPasswordResponse,
    summary="Reset agent password",
    responses={
        200: {"description": "Password reset success"},
        400: {"description": "Validation error / reset failed"},
        500: {"description": "Internal server error"},
    }
)
async def reset_password(req: ResetPasswordRequest):
    result = await get_price_service(req)
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
    summary="Check flight price"
)
async def get_price(req: GetPriceRequest):
    try:
        return await get_price_service(req)
    except PriceError as e:
        return JSONResponse(status_code=404, content={"result": "no", "reason": e.reason})

# -------------------------------
# Post Bookings Endpoint
# -------------------------------
@router.post(
    "/postbooking-json",
    response_model=PostBookingResponse,
    summary="Book a flight",
    responses={
        200: {"description": "Booking success", "model": PostBookingResponse},
        400: {"description": "Booking failed", "model": MMBCErrorResponse},
        500: {"description": "Internal server error"},
    },
)
async def post_booking(req: PostBookingRequest):
    try:
        return await post_booking_service(req)
    except BookingError as e:
        return JSONResponse(status_code=400, content=e.full_body)

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
    summary="Check if booking is issued"
)
async def get_issued(req: KodeBookingRequest):
    try:
        return await get_issued_service(kodebooking=req.kodebooking)
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
    summary="Check booking status"
)
async def get_status(req: KodeBookingRequest):
    try:
        return await get_status_service(req.kodebooking)
    except StatusBookingError as e:
        return JSONResponse(status_code=404, content={"result": "no", "reason": e.reason})

# -------------------------------
# Get E-Ticket Endpoint
# -------------------------------
class GetETicketOut(BaseModel):
    result: str
    eticket_url: Optional[str] = None

@router.post(
    "/getetiket-json",
    response_model=GetETicketOut,
    responses={
        200: {"description": "E-ticket URL returned", "model": GetETicketOut},
        404: {"description": "E-ticket not found", "model": MMBCErrorResponse},
        500: {"description": "Internal server error"},
    },
    summary="Retrieve E-Ticket"
)
async def get_eticket(req: GetETicketRequest):
    try:
        result = await get_eticket_service(req.kodebooking)

        # Extract URL from reason (as per MMBC spec)
        match = re.search(r"https?://[^\s]+etiket-[\w\d]+\.pdf", result.reason)
        url = match.group(0) if match else None

        return {"result": "ok", "eticket_url": url}
    except ETicketError as e:
        return JSONResponse(status_code=404, content={"result": "no", "reason": e.reason})
