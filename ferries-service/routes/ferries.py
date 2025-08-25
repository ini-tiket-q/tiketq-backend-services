from fastapi import APIRouter, HTTPException
from domain.models import FerryBookingRequest, FerryBookingResponse
from domain import services
from fastapi import APIRouter, Query
from domain.services import get_ferry_schedules


router = APIRouter(prefix="/ferries", tags=["Ferries"])

@router.get("/schedules")
def list_schedules(
    origin: str = Query(None),
    destination: str = Query(None),
    date: str = Query(None)
):
    return get_ferry_schedules(origin, destination, date)

@router.post("/book", response_model=FerryBookingResponse)
def book_ferry(req: FerryBookingRequest):
    return services.handle_ferry_booking(req)

@router.get("/transactions")
def list_all_transactions():
    """
    Get all mock transactions (for testing admin dashboard)
    """
    return services.get_all_transactions()


@router.put("/transactions/{transaction_id}")
def update_transaction(transaction_id: str, status: str):
    """
    Update transaction status (mock).
    Example: paid, failed, cancelled
    """
    try:
        tx = services.update_transaction_status(transaction_id, status)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return tx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))