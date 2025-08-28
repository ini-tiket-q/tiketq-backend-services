from fastapi import APIRouter, HTTPException
from domain.models import FerryBookingRequest, FerryBookingResponse
from domain import services_mock
from fastapi import APIRouter, Query
from domain.services_mock import get_ferry_schedules, get_all_bookings


router_mock = APIRouter(prefix="/ferries", tags=["Ferries"])

## Schedules

# get all routes for user/guest to choose
@router_mock.get("/schedules")
def list_schedules(
    origin: str = Query(None),
    destination: str = Query(None),
    date: str = Query(None)
):
    return get_ferry_schedules(origin, destination, date)

## -------------------------
## Bookings

# create booking for user/guest
@router_mock.post("/book", response_model=FerryBookingResponse)
def book_ferry(req: FerryBookingRequest):
    return services_mock.handle_ferry_booking(req)

# get all bookings (admin)
@router_mock.get("/bookings")
def list_all_bookings():
    """
    Get all mock ferry bookings (admin view).
    """
    return get_all_bookings()

## ----------------------------
## Transactions

# get all transactions (admin)
@router_mock.get("/transactions")
def list_all_transactions():
    """
    Get all mock transactions (for testing admin dashboard)
    """
    return services_mock.get_all_transactions()

# update transaction status. enum: incomplete, failed, cancelled
@router_mock.put("/transactions/{transaction_id}")
def update_transaction(transaction_id: str, status: str):
    """
    Update transaction status (mock).
    Example: paid, failed, cancelled
    """
    try:
        tx = services_mock.update_transaction_status(transaction_id, status)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return tx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    