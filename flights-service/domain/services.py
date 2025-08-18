from adapters.mmbc_factory import mmbc
from domain.schemas import (
    GetPriceRequest, GetPriceResponse,
    PostBookingRequest, PostBookingResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    KodeBookingRequest,
    IssuedResponseSuccess, IssuedResponseError,
    GetStatusBookingResponse
)

async def get_price_service(req: GetPriceRequest) -> GetPriceResponse:
    return await mmbc.get_price(**req.dict(by_alias=True))


async def post_booking_service(req: PostBookingRequest) -> PostBookingResponse:
    return await mmbc.post_booking(**req.dict(by_alias=True))


async def get_issued_service(kodebooking: str):
    return await mmbc.get_issued(kodebooking)


async def get_status_service(kodebooking: str) -> GetStatusBookingResponse:
    return await mmbc.get_status_booking(kodebooking=kodebooking)


async def reset_password_service(req: ResetPasswordRequest) -> ResetPasswordResponse:
    return await mmbc.reset_password(**req.dict())
