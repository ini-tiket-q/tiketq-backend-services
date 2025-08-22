from fastapi import APIRouter
from domain.models import FerryBookingRequest, FerryBookingResponse
from domain import services

router = APIRouter(prefix="/ferries", tags=["Ferries"])

@router.post("/book", response_model=FerryBookingResponse)
def book_ferry(req: FerryBookingRequest):
    return services.handle_ferry_booking(req)

@router.get("/transactions")
def list_all_transactions():
    """
    Get all mock transactions (for testing admin dashboard)
    """
    return services.get_all_transactions()
