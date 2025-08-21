from fastapi import APIRouter
from domain.models import FerryBookingRequest, FerryBookingResponse
from domain import services

router = APIRouter(prefix="/ferries", tags=["Ferries"])

@router.post("/book", response_model=FerryBookingResponse)
def book_ferry(req: FerryBookingRequest):
    """
    Create ferry booking & transaction record
    """
    return services.handle_ferry_booking(req)
