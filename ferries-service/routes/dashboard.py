from fastapi import APIRouter, Query
from domain.dashboard.services import (
    get_roundtrip_dashboard,
    get_routes_dashboard,
    get_trips_dashboard
)
from utils.error_handling import handle_sync_api_errors

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/routes")
def routes(search: str = Query(None)):    
    return get_routes_dashboard(search)
    

@router.get("/oneway")
@handle_sync_api_errors("oneway trips endpoint")
def trips(
    nationality: str = Query(..., description="Passenger nationality (country code)"),
    origin: str = Query(..., description="Departure port code"), 
    destination: str = Query(..., description="Arrival port code"), 
    date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    pax: int = Query(1, description="Number of passengers"),
    ferry_class: str = Query("economy", description="Ferry class")
):
    return get_trips_dashboard(nationality, origin, destination, date, pax, ferry_class)


@router.get("/roundtrip")
@handle_sync_api_errors("oneway trips endpoint")
def roundtrip(
    nationality: str = Query(..., description="Passenger nationality (country code)"),
    origin: str = Query(..., description="Departure port code"), 
    destination: str = Query(..., description="Arrival port code"), 
    depart_date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    return_date: str = Query(..., description="Return date in YYYY-MM-DD format"),
    pax: int = Query(1, description="Number of passengers"),
    ferry_class: str = Query("economy", description="Ferry class")
):
    return get_roundtrip_dashboard(nationality, origin, destination, depart_date, return_date, pax, ferry_class)

