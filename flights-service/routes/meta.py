from fastapi import APIRouter, Depends
from adapters.external_api import MmbcClient

router = APIRouter(prefix="/api/v1/flight-service/meta", tags=["meta"])

def mmbc_dep():
    return MmbcClient()  # reads creds from env

@router.get("/airports")
def list_airports(mmbc: MmbcClient = Depends(mmbc_dep)):
    data = mmbc.get_code_area()  # -> list[{code, city}]
    return {"data": data, "error": None, "meta": {"count": len(data)}}

@router.get("/airlines")
def list_airlines(mmbc: MmbcClient = Depends(mmbc_dep)):
    data = mmbc.get_code_flights()  # -> list[{flight_code, flight_name, flight_image}]
    return {"data": data, "error": None, "meta": {"count": len(data)}}
