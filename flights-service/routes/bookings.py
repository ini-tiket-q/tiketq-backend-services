import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from domain.schemas import (
    GetPriceRequest, GetPriceResponse,
    PostBookingRequest, PostBookingResponse,
    KodeBookingRequest, GetIssuedResponseSuccess, GetIssuedResponseError,
    GetStatusBookingResponse,
    ResetPasswordRequest, ResetPasswordResponse
)
from domain.mmbc_services import mmbc, MOCK_REMOTE
from domain.schemas import GetETicketRequest, GetETicketResponse
from pydantic import BaseModel, Field
from typing import Optional
from adapters.store import BOOKING_STATUS



router = APIRouter(prefix="/json", tags=["MMBC Flight-Service"])



class GetETicketResponse(BaseModel):
    result: str
    eticket_url: Optional[str] = None

# 1. Get Price
@router.post("/getprice-json", response_model=GetPriceResponse, summary="Check flight price",
    description="""
Hit MMBC to retrieve price for a given route, number of pax, and travel date.

Returns publish fare, tax, NTA values, and available seats.
    """
)
async def get_price(req: GetPriceRequest):
    result = await mmbc.get_price(**req.dict())

    if result.get("result") == "no":
        raise HTTPException(404, detail=result.get("reason", "No result"))

    

    return result


# 2. Post Booking
@router.post("/postbooking-json", response_model=PostBookingResponse,summary="Book a flight",
description="""
Creates a new booking on MMBC. This can be used by both guests and registered users.

You must provide contact details, passenger name, and booking information.
"""
)

async def post_booking(req: PostBookingRequest):
    result = await mmbc.post_booking(**req.dict())

    if result.get("result") == "no":
        raise HTTPException(400, detail=result.get("reason", "Booking failed"))

    kodebooking = result["kodebooking"]

    # Save mock booking status
    BOOKING_STATUS[kodebooking] = "incomplete"

    return result


# 3. Get Issued
@router.post(
    "/getissued-json",
    response_model=GetIssuedResponseSuccess,
    responses={
        403: {"model": GetIssuedResponseError, "description": "Booking not paid"},
        404: {"model": GetIssuedResponseError, "description": "Booking not found"}, 
    }, summary="Check if booking is issued",
        description="""
        Queries MMBC to check whether the booking has been issued.

        Returns ticket document info if issued, otherwise error.
        """
)

async def get_issued(req: KodeBookingRequest):
    # Simulate payment check
    if BOOKING_STATUS.get(req.kodebooking) != "PAID":
        raise HTTPException(status_code=403, detail={"result": "no", "reason": "Payment not completed"})

    result = await mmbc.get_issued(kodebooking=req.kodebooking)


    if result.get("result") == "no":
        raise HTTPException(status_code=404, detail={"result": "no", "reason": result.get("reason", "Unknown error")})

    return result


# 4. Get Booking Status
@router.post("/getstatusbooking-json", response_model=GetStatusBookingResponse, summary="Check booking status",
description="""
Retrieves current status of the booking (e.g., pending, confirmed, cancelled).

Based on booking code from MMBC.
"""
)

async def get_status(req: KodeBookingRequest):
    result = await mmbc.get_status_booking(kodebooking=req.kodebooking)


    if result.get("result") == "no":
        raise HTTPException(404, detail=result.get("reason", "Booking not found"))

  

    return result



# 5. Reset Password
@router.post("/resetpassword", response_model=ResetPasswordResponse, summary="Reset agent password",
description="""
Allows travel agents to reset their MMBC credentials using email, phone, and agent code.

Returns success message or reason for failure.
"""
)

async def reset_password(req: ResetPasswordRequest):
    result = await mmbc.reset_password(**req.dict())

    if result.get("result") == "no":
        raise HTTPException(400, detail=result.get("reason", "Reset failed"))


    return result

@router.post("/getetiket-json", response_model=GetETicketResponse, summary="Retrieve E-Ticket",
description="""
Fetches issued ticket document and ticket number from MMBC, if available.

Can be used after booking is marked as 'issued'.
"""
)
async def get_eticket(req: GetETicketRequest):
    result = await mmbc.get_eticket(kodebooking=req.kodebooking)

    if result.get("result") == "no":
        raise HTTPException(404, detail=result.get("reason", "Failed to retrieve e-ticket"))

    
    match = re.search(r"https?://[^\s]+etiket-[\w\d]+\.pdf", result.get("reason", ""))
    url = match.group(0) if match else None

    return {"result": "ok", "eticket_url": url}


class MidtransWebhook(BaseModel):
    order_id: str

@router.post("/simulate-payment", summary="Simulate payment callback (Midtrans mock)")
async def simulate_payment(req: MidtransWebhook):
    kodebooking = req.order_id

    if kodebooking not in BOOKING_STATUS:
        raise HTTPException(404, detail="Booking not found")

    # Update to paid
    BOOKING_STATUS[kodebooking] = "PAID"

    return {"message": f"Booking {kodebooking} updated to 'paid'"}

