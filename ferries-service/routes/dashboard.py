from fastapi import APIRouter, Query
from domain.dashboard.services import (
    get_roundtrip_dashboard,
    get_routes_dashboard,
    get_trips_dashboard
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/routes")
def routes(search: str = Query(None)):    
    return get_routes_dashboard(search)


@router.get("/oneway")
def trips(
    origin: str = Query(..., description="Departure port code"), 
    destination: str = Query(..., description="Arrival port code"), 
    date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    # pax: int = Query(1, description="Number of passengers")
):
    return get_trips_dashboard(origin, destination, date)



@router.get("/roundtrip")
def roundtrip(
    origin: str = Query(..., description="Departure port code"), 
    destination: str = Query(..., description="Arrival port code"), 
    depart_date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    return_date: str = Query(..., description="Return date in YYYY-MM-DD format"),
    pax: int = Query(1, description="Number of passengers")
):
    return get_roundtrip_dashboard(origin, destination, depart_date, return_date, pax)

