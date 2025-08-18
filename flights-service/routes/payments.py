from fastapi import APIRouter, HTTPException
from domain import services
from domain.schemas import (
    GetPriceRequest, GetPriceResponse,
    PostBookingRequest, PostBookingResponse,
    KodeBookingRequest,
    GetStatusBookingResponse, ResetPasswordRequest,
    ResetPasswordResponse,
    IssuedResponseSuccess, IssuedResponseError,
    GetStatusResponseError,
    BookingResponseError
)

router = APIRouter(prefix="/json", tags=["MMBC Payments"])


@router.post("/getprice-json", response_model=GetPriceResponse)
async def get_price(req: GetPriceRequest):
    try:
        return await services.get_price_service(req)
    except Exception as e:
        raise HTTPException(502, detail=f"MMBC error: {e}")


@router.post("/postbooking-json", response_model=PostBookingResponse,
             responses={502: {"model": BookingResponseError}})
async def post_booking(req: PostBookingRequest):
    try:
        return await services.post_booking_service(req)
    except Exception as e:
        raise HTTPException(502, detail={"result": "no", "reason": str(e)})


@router.post(
    "/getissued-json",
    summary="Get Issued Ticket",
    response_model=IssuedResponseSuccess,
    responses={
        403: {"model": IssuedResponseError, "description": "Payment not completed"},
        404: {"model": IssuedResponseError, "description": "Booking not found"},
        502: {"description": "MMBC Error"},
    },
)
async def get_issued(payload: KodeBookingRequest):
    try:
        result = await services.get_issued_service(payload.kodebooking)
        if result["result"] == "no":
            reason = result.get("reason", "")
            if "not completed" in reason.lower():
                raise HTTPException(status_code=403, detail=result)
            else:
                raise HTTPException(status_code=404, detail=result)
        return result
    except Exception as e:
        raise HTTPException(502, detail=f"MMBC error: {e}")


@router.post(
    "/getstatusbooking-json",
    response_model=GetStatusBookingResponse,
    responses={
        404: {"model": GetStatusResponseError, "description": "Booking not found"},
        502: {"description": "MMBC Error"}
    }
)
async def get_status_booking(req: KodeBookingRequest):
    try:
        result = await services.get_status_service(req.kodebooking)
        if result["result"] == "no":
            raise HTTPException(status_code=404, detail=result)
        return result
    except Exception as e:
        raise HTTPException(502, detail=f"MMBC error: {e}")


@router.post(
    "/resetpassword",
    response_model=ResetPasswordResponse,
    responses={502: {"description": "MMBC Error"}}
)
async def reset_password(req: ResetPasswordRequest):
    try:
        return await services.reset_password_service(req)
    except Exception as e:
        raise HTTPException(502, detail=f"MMBC error: {e}")
