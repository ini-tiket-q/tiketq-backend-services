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

router = APIRouter(prefix="/json", tags=["MMBC Flight-Service"])

# 1. Get Price
@router.post("/getprice-json", response_model=GetPriceResponse)
async def get_price(req: GetPriceRequest):
    result = await mmbc.get_price(**req.dict())

    if result.get("result") == "no":
        raise HTTPException(404, detail=result.get("reason", "No result"))

    if MOCK_REMOTE:
        # bypass response model validation in mock mode
        return JSONResponse(content=result)

    return result


# 2. Post Booking
@router.post("/postbooking-json", response_model=PostBookingResponse)
async def post_booking(req: PostBookingRequest):
    result = await mmbc.post_booking(**req.dict())

    if result.get("result") == "no":
        raise HTTPException(400, detail=result.get("reason", "Booking failed"))

    if MOCK_REMOTE:
        return JSONResponse(content=result)

    return result


# 3. Get Issued
@router.post(
    "/getissued-json",
    response_model=GetIssuedResponseSuccess,
    responses={
        403: {"model": GetIssuedResponseError, "description": "Booking not paid"},
        404: {"model": GetIssuedResponseError, "description": "Booking not found"},
    },
)
async def get_issued(req: KodeBookingRequest):
    result = await mmbc.get_issued(req.kodebooking)

    if result.get("result") == "no":
        reason = result.get("reason", "").lower()
        if "not completed" in reason:
            raise HTTPException(status_code=403, detail={"result": "no", "reason": reason})
        else:
            raise HTTPException(status_code=404, detail={"result": "no", "reason": reason})

    if MOCK_REMOTE:
        return JSONResponse(content=result)

    return result


# 4. Get Booking Status
@router.post("/getstatusbooking-json", response_model=GetStatusBookingResponse)
async def get_status(req: KodeBookingRequest):
    result = await mmbc.get_status_booking(req.kodebooking)

    if result.get("result") == "no":
        raise HTTPException(404, detail=result.get("reason", "Booking not found"))

    if MOCK_REMOTE:
        return JSONResponse(content=result)

    return result



# 5. Reset Password
@router.post("/resetpassword", response_model=ResetPasswordResponse)
async def reset_password(req: ResetPasswordRequest):
    result = await mmbc.reset_password(**req.dict())

    if result.get("result") == "no":
        raise HTTPException(400, detail=result.get("reason", "Reset failed"))

    if MOCK_REMOTE:
        return JSONResponse(content=result)

    return result
