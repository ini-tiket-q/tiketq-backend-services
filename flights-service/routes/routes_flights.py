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
    FlightSearchRequest,
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
    description="""
    Validates user credentials (username & password) and returns the agent's MMBC balance if login is successful.

    **Form Data**:
    - `username`: MMBC login username (e.g. `Paris`)
    - `password`: MMBC login password (e.g. `xxxxxxxxx`)

    **Returns**:
    - On success: `{ "result": "ok", "saldo": "1,000,000" }`
    - On failure: `401 Unauthorized` with reason `"invalid login"`
    """,
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
    description="""
    Returns a list of supported airport codes along with the associated city names.

    No parameters required.

    **Returns**:
    - List of airport codes, e.g. `CGK` (Jakarta), `DPS` (Denpasar)
    """,
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
    description="""
    Returns a list of available airline codes, names, and their logos.

    No parameters required.

    **Returns**:
    - Example: `[{ "code": "GA", "name": "Garuda Indonesia", "logo": "..." }]`
    """,
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
# from fastapi import Request  # Add this at the top


@router.post(
    "/getflights-json",
    summary="Search available flights",
    description="""
    Search available flights based on origin, destination, and travel date. Supports optional filters like airline, transit, baggage, class, and pagination.

    Login is optional but recommended to fetch pricing and availability tied to agent account.

    **Request Body**:
    - `flight_from`: Departure airport code (e.g. `CGK`)
    - `flight_to`: Arrival airport code (e.g. `DPS`)
    - `date`: Date of travel in format `dd-mm-yyyy` (e.g. `01-09-2025`)
    - `airline`: Airline code filter (optional)
    - `transit`: Whether to include transit flights (`true`/`false`) (optional)
    - `baggage`: Filter by baggage allowance (optional)
    - `flight_class`: Economy / Business / First (optional)
    - `sort_by`: Sorting option: `cheapest`, `fastest`, etc. (optional)
    - `page`: Page number for pagination (default: 1)
    - `per_page`: Number of results per page (default: 10)
    - `username`: MMBC login username (optional)
    - `password`: MMBC login password (optional)

    **Returns**:
    - A list of matching flight options.
    - `401 Unauthorized`: If login provided but invalid.
    - `404 Not Found`: If no flights match the search.
    """,
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
    request_data: FlightSearchRequest,
    service: FlightService = Depends(get_flight_service),
):
    try:
        # Validasi format tanggal
        try:
            parsed_date = datetime.strptime(request_data.date, "%d-%m-%Y").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Date must be in format dd-mm-yyyy",
            )

        # Buat params
        params = FlightSearchParams(
            origin=request_data.flight_from,
            destination=request_data.flight_to,
            date=parsed_date,
            airline=request_data.airline,
            transit=request_data.transit,
            baggage=request_data.baggage,
            flight_class=request_data.flight_class,
            sort_by=request_data.sort_by,
            page=request_data.page,
            per_page=request_data.per_page,
        )

        # Login opsional
        if request_data.username and request_data.password:
            if not service.validate_login(request_data.username, request_data.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"result": "no", "reason": "invalid login"},
                )

        results = service.get_flights(
            params,
            username=request_data.username,
            password=request_data.password,
        )

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
