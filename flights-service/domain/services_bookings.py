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
    result = await mmbc.get_price(**req.dict(by_alias=True))

    if result.get("result") == "no":
        raise PriceError(result.get("reason", "No result"))

    return result

async def post_booking_service(req: PostBookingRequest) -> PostBookingResponse:
    result = await mmbc.post_booking(**req.dict(by_alias=True))

    if result.get("result") == "no":
        raise BookingError(
            reason=result.get("reason") or result.get("message") or "Booking failed",
            full_body=result
        )

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
