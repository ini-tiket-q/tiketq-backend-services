from fastapi import APIRouter, Depends, Form, Query, HTTPException, status, Request
from typing import Optional
from typing import List
from datetime import datetime
from domain.schemas_flights import (
    FlightSearchParams,
    FlightResultSchema,
    CodeAreaResponse,
    AirlineSchema,
    AirportCode,
)
from domain.services_flights import FlightService
from domain.repository_flights import FlightRepository
from adapters.external_api_flights import ExternalFlightAPI

print("📦 routes_flights.py LOADED")

router = APIRouter(prefix="/json", tags=["Flight Services"])


# --- Service Dependency ---
def get_flight_service() -> FlightService:
    print("✈️ get_flight_service() CALLED")
    repo = FlightRepository(ExternalFlightAPI())
    return FlightService(repo)


# -------------------------------
# Check Balance Endpoint
# -------------------------------
@router.post(
    "/ceksaldo",
    summary="Check balance with username & password",
    responses={
        200: {"description": "Success"},
        401: {"description": "Invalid login"},
        500: {"description": "Internal server error"},
    },
)
def check_balance(
    username: str = Form(...),
    password: str = Form(...),
    service: FlightService = Depends(get_flight_service),
):
    """
    Validate user and return account balance.
    """
    try:
        saldo_data = service.check_balance(username, password)
        if saldo_data and saldo_data.balance > 0:
            return {"result": "ok", "saldo": f"{saldo_data.balance:,}"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"result": "no", "reason": "invalid login"},
        )
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"❌ Error in /ceksaldo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"result": "no", "reason": "internal server error"},
        )


# -------------------------------
# Get Code Area (Airport)
# -------------------------------
@router.get(
    "/getcodearea-json",
    summary="Get airport code and city",
    response_model=CodeAreaResponse,
    responses={
        200: {"description": "Success"},
        500: {"description": "Internal server error"},
    },
)
def get_code_area(service: FlightService = Depends(get_flight_service)):
    """
    Return list of airport codes and city names.
    """
    try:
        print("🌍 Fetching airport codes...")
        return service.get_code_area()
    except Exception as e:
        print(f"❌ Error in /getcodearea-json: {e}")
        raise HTTPException(500, detail="Internal server error")


# -------------------------------
# Get Code Flights (Airlines)
# -------------------------------
@router.get(
    "/getcodeflights-json",
    summary="Get airline code and name",
    response_model=List[AirlineSchema],
    responses={
        200: {"description": "Success"},
        500: {"description": "Internal server error"},
    },
)
def get_code_flights(service: FlightService = Depends(get_flight_service)):
    """
    Return list of airline codes, names, and logos.
    """
    try:
        print("✈️ Fetching airline codes...")
        return service.get_code_flights()
    except Exception as e:
        print(f"❌ Error in /getcodeflights-json: {e}")
        raise HTTPException(500, detail="Internal server error")


# -------------------------------
# Search Available Flights
# -------------------------------
from fastapi import Request  # Add this at the top

@router.get(
    "/getflights-json",
    response_model=List[FlightResultSchema],
    responses={
        200: {"description": "Success"},
        401: {"description": "Invalid login"},
        404: {"description": "No flights found"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal server error"},
    },
)
def get_flights(
    request: Request,  # ✅ Move this line before default arguments
    username: str = Query(...),
    password: str = Query(...),
    origin: AirportCode = Query(..., alias="flight_from"),
    destination: AirportCode = Query(..., alias="flight_to"),
    date: str = Query(...),

    # Extra filters
    airline: Optional[str] = Query(None),
    transit: Optional[str] = Query(None),
    baggage: Optional[str] = Query(None),
    flight_class: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    page: Optional[int] = Query(1),
    per_page: Optional[int] = Query(10),

    service: FlightService = Depends(get_flight_service),
    
    ):
        try:
            try:
                parsed_date = datetime.strptime(date, "%d-%m-%Y").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Date must be in format dd-mm-yyyy",
                )

            params = FlightSearchParams(
                origin=origin,
                destination=destination,
                date=parsed_date,
                airline=request.query_params.get("airline"),
                transit=request.query_params.get("transit"),
                baggage=request.query_params.get("baggage"),
                flight_class=request.query_params.get("flight_class"),
                sort_by=request.query_params.get("sort_by"),
                page=int(request.query_params.get("page", 1)),
                per_page=int(request.query_params.get("per_page", 10)),
            )

            if not service.validate_login(username, password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"result": "no", "reason": "invalid login"},
                )

            results = service.get_flights(params)
            if not results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"result": "no", "reason": "no result"},
                )

            return results

        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Error in /getflights-json: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"result": "no", "reason": "internal server error"},
            )
