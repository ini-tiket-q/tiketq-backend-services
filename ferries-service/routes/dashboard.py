from fastapi import APIRouter, Query
from domain.dashboard.services import (
    get_oneway_dashboard,
    get_roundtrip_dashboard,
    get_routes_dashboard,
    get_trips_dashboard
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/routes")
def routes(search: str = Query(None)):    
    return get_routes_dashboard(search)


@router.get("/trips")
def trips(origin: str = Query(...), destination: str = Query(...), date: str = Query(...)):
    return get_trips_dashboard(origin, destination, date)


# @router.get("/oneway")
# def oneway(origin: str = Query(...), destination: str = Query(...), date: str = Query(...)):
#     # Map ke nama param sesuai dokumentasi API eksternal
#     params = {
#         "embarkation": origin,
#         "destination": destination,
#         "tripdate": date
#     }
#     return get_oneway_dashboard(params)

@router.get("/roundtrip")
def roundtrip(origin: str = Query(...), destination: str = Query(...), depart_date: str = Query(...), return_date: str = Query(...)):
    params = {
        "embarkation": origin,
        "destination": destination,
        "depart_date": depart_date,   
        "return_date": return_date
    }
    return get_roundtrip_dashboard(params)

