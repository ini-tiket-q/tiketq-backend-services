from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import uuid
from fastapi import HTTPException
from pydantic import ValidationError
from domain.models import (
    BookingStatus,
    FerryBookingRequest, 
    FerryBookingResponse, 
    FerryTripDisplay,
    PriceBreakdown,
    TripSearchRequest, 
    TripSearchResponse
)
from adapters.external_api import SindoClient
import logging

logger = logging.getLogger(__name__)
# Initialize the SindoClient instance
sindo_client = SindoClient()

# In-memory storage for demonstration (replace with database in production)
# Route mapping cache
_route_mapping_cache = None
_route_cache_expiry = None
ROUTE_CACHE_DURATION = 3600  # Cache for 1 hour

routes = []
# trips_cache = {}

# Simpan booking_requirements secara lokal
BOOKING_REQUIREMENTS_STORE = {}


def get_route_mapping() -> Dict[str, str]:
    """
    Fetch route mapping from Sindo API and cache it.
    Returns a dictionary like {"BTC-HFC": "route-guid-123", ...}
    """
    global _route_mapping_cache, _route_cache_expiry
    
    # Return cached data if still valid
    if (_route_mapping_cache and _route_cache_expiry and 
        datetime.now() < _route_cache_expiry):
        return _route_mapping_cache
    
    # Fetch fresh data from Sindo
    try:
        logger.info("Fetching fresh route mapping from Sindo API")
        routes_response = sindo_client.get_sindo_routes()
        
         # Check if response has the expected structure
        if (not routes_response or 
            routes_response.get("status") != "Ok" or 
            "data" not in routes_response or 
            "records" not in routes_response["data"]):
            logger.warning("Invalid API response structure, using mock data")
            return _load_mock_route_mapping()
            
        records = routes_response["data"]["records"]
        
        if not records:
            logger.warning("No routes found in API response, using mock data")
            return _load_mock_route_mapping()
        
        records = routes_response["data"]["records"]
        
        if not records:
            logger.warning("No routes found in API response, using mock data")
            return _load_mock_route_mapping()
        
        routes = records
        _route_mapping_cache = {}
        
        for route in routes:
            try:
                route_id = route.get("id", "").strip()
                route_name = route.get("name", "").strip()
                
                if not route_id:
                    continue
                
                # Extract port codes from the exact structure in documentation
                embarkation_port = route.get("embarkationPort", {})
                destination_port = route.get("destinationPort", {})
                
                origin_code = embarkation_port.get("code", "").strip().upper()
                dest_code = destination_port.get("code", "").strip().upper()
                
                if origin_code and dest_code:
                    # Create mapping for both directions (one-way and round-trip)
                    key_forward = f"{origin_code}-{dest_code}"
                    key_backward = f"{dest_code}-{origin_code}"
                    
                    route_details = {
                        "route_id": route_id,
                        "route_name": route_name
                    }
                    
                    _route_mapping_cache[key_forward] = route_details
                    _route_mapping_cache[key_backward] = route_details
                    
                    logger.debug(f"Mapped {key_forward} -> {route_id}({route_name})")
                
            except Exception as e:
                logger.warning(f"Error processing route {route.get('id', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Successfully mapped {len(_route_mapping_cache)//2} routes from API")     
        # Set cache expiry
        _route_cache_expiry = datetime.now() + timedelta(seconds=ROUTE_CACHE_DURATION)
        return _route_mapping_cache
        
    except Exception as e:
        logger.error(f"Error fetching route mapping: {str(e)}")
        logger.info("Falling back to mock route data")
        return _load_mock_route_mapping()

def _load_mock_route_mapping() -> Dict[str, str]:
    """Load fallback mock route data"""
    mock_routes = {
        "HFC-BTC": {
            "route_id": "07adda23-56e2-475d-15ac-08d7934ea487",
            "route_name": "HarbourFront Centre Terminal - Batam Centre Terminal"
        },
        "BTC-HFC": {
            "route_id": "07adda23-56e2-475d-15ac-08d7934ea487", 
            "route_name": "Batam Centre Terminal - HarbourFront Centre Terminal"
        },
        "HFC-SKP": {
            "route_id": "70695ec6-b859-4074-15ad-08d7934ea487",
            "route_name": "HarbourFront Centre Terminal - Sekupang Terminal"
        },
        "SKP-HFC": {
            "route_id": "70695ec6-b859-4074-15ad-08d7934ea487",
            "route_name": "Sekupang Terminal - HarbourFront Centre Terminal"
        },
        "HFC-WFC": {
            "route_id": "ad320221-95ce-4b1d-15ae-08d7934ea487",
            "route_name": "HarbourFront Centre Terminal - Waterfront City Terminal"
        },
        "WFC-HFC": {
            "route_id": "ad320221-95ce-4b1d-15ae-08d7934ea487",
            "route_name": "Waterfront City Terminal - HarbourFront Centre Terminal"
        },
        "BTC-TMF": {
            "route_id": "29bcaf7b-a38e-4e32-b971-08d84405955f",
            "route_name": "Batam Centre Terminal - Tanah Merah Ferry Terminal"
        },
        "TMF-BTC": {
            "route_id": "29bcaf7b-a38e-4e32-b971-08d84405955f",
            "route_name": "Tanah Merah Ferry Terminal - Batam Centre Terminal"
        }
    }
    logger.info(f"Using mock route data with {len(mock_routes)} routes")
    return mock_routes

def camel_to_snake(name):
    """Convert camelCase to snake_case"""
    import re
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()         
            
# Get All Routes Provided
def get_ferry_routes(search: str = None):
    """
    Ambil daftar rute ferry (origin → destination).
    """
    data = sindo_client.get_sindo_routes(search=search)
    records = data.get("data", {}).get("records", [])
    return {"routes": records}

def get_route_id(origin: str, destination: str) -> str:
    route_id = None
    
    try:
        route_mapping = get_route_mapping()
        route_key = f"{origin.upper()}-{destination.upper()}"
        route_details = route_mapping.get(route_key)
        
        if not route_details:
            available_routes = list(route_mapping.keys())
            logger.error(f"Route {route_key} not found. Available routes: {available_routes}")
            raise ValueError(f"Route from {origin} to {destination} not found in available routes")
        
        route_id = route_details.get("route_id")
        
        if not route_id:
            logger.error(f"Route ID not found in route details for {route_key}")
            raise ValueError(f"Route ID not found for route from {origin} to {destination}")
        
        logger.debug(f"Found route {route_key} -> {route_id}")
        return route_id
    except Exception as e:
        logger.error(f"Error in get_route_id: {str(e)}")
        raise

def get_route_details(origin: str, destination: str) -> Dict[str, str]:
    route_mapping = get_route_mapping()
    route_key = f"{origin.upper()}-{destination.upper()}"
    route_details = route_mapping.get(route_key)
    
    if not route_details:
        available_routes = list(route_mapping.keys())
        logger.error(f"Route {route_key} not found. Available routes: {available_routes}")
        raise ValueError(f"Route from {origin} to {destination} not found in available routes")
    
    logger.debug(f"Found route {route_key} -> {route_details}")
    return route_details

def get_roundtrip_route_details(origin: str, destination: str) -> tuple[Dict[str, str], Dict[str, str]]:
    try:
        outward_route_details = get_route_details(origin, destination)
        return_route_details = get_route_details(destination, origin)
        
        # Validate that we found both routes
        if not outward_route_details or not return_route_details:
            missing_routes = []
            if not outward_route_details:
                missing_routes.append(f"{origin} to {destination}")
            if not return_route_details:
                missing_routes.append(f"{destination} to {origin}")
            
            error_msg = f"Routes not found: {', '.join(missing_routes)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Roundtrip routes: {origin}→{destination}: {outward_route_details}, {destination}→{origin}: {return_route_details.get('route_id')}")
        return outward_route_details, return_route_details
    except Exception as e:
        logger.error(f"Error getting roundtrip route details: {str(e)}")
        raise

# Get All Trips for users to choose
# raw shedules from Sindo API
def get_ferry_trips(origin: str, destination: str, date: str):
    """
    Ambil daftar trip / jadwal ferry dari API Sindo.
    """
    data = sindo_client.get_sindo_trips(origin, destination, date)

    # Kalau API balikin list langsung
    if isinstance(data, list):
        records = data
    else:
        # fallback kalau ada format lain
        records = data.get("data", {}).get("records", [])
    return {"trips": records}


def calculate_base_price(item: Dict[str, Any], ferry_class: str) -> float:
    """
    Calculate base price based on item and ferry class.
    This is a placeholder implementation.
    """
    # Your actual implementation here
    base_price = 100000  # Example base price
    # Apply class multiplier
    if ferry_class == "Business Class":
        base_price *= 1.5
    elif ferry_class == "First Class":
        base_price *= 2.0
    return base_price

def get_ferry_oneway(search_request: TripSearchRequest):
    try:
        # Validasi origin & destination
        if search_request.origin == search_request.destination:
            raise ValueError("Origin and destination cannot be the same")
        if search_request.pax < 1:
            raise ValueError("Number of passengers must be at least 1")

        #get route ID & name
        route_details = get_route_details(search_request.origin, search_request.destination)
        
        sindo_date = search_request.depart_date.strftime("%Y%m%d")
        
        trips = get_ferry_trips(search_request.origin, search_request.destination, sindo_date)
        if trips.get("status") == "error":
            raise ValueError(trips.get("message", "Error fetching ferry data"))

        trips_list = trips.get("trips", [])
        
        display_trips = []
        for trip_data in trips_list:
            model_data = {camel_to_snake(k): v for k, v in trip_data.items()}
            model_data.update({
                "route_id": route_details.get("route_id"),
                "route_name": route_details.get("route_name"),
                "nationality": search_request.nationality,
                "origin": search_request.origin,
                "destination": search_request.destination,
                "depart_date": search_request.depart_date.isoformat(),
                "return_date": search_request.return_date.isoformat() if search_request.return_date else None,
                "pax": search_request.pax,
                "ferry_class": search_request.ferry_class.value,
                "is_round_trip": search_request.is_round_trip,
                # "base_price": calculate_base_price(trip_data, search_request.ferry_class.value)
            })

            model_data.setdefault("trip_sched_id", "")
            model_data.setdefault("departure_time", "")
            model_data.setdefault("trip_id", "")
            model_data.setdefault("used_seat", "0")

            try:
                display_trip = FerryTripDisplay(**model_data)
                # trips_cache[display_trip.route_id] = display_trip
                display_trips.append(display_trip)
            except ValidationError as e:
                logger.error(f"Validation error for trip data: {trip_data}. Error: {e}")
                continue # Skip invalid entries   

        return display_trips
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise 
    except Exception as e:
        logger.error(f"Error in get_ferry_oneway: {str(e)}", exc_info=True)
        logger.error(f"Validation error for trip data: {trip_data}. Error: {e}")
        raise Exception(f"Failed to fetch ferry data: {str(e)}")
        
    
def get_ferry_roundtrip(search_request: TripSearchRequest):
    try:
        # Validate origin and destination
        if search_request.origin == search_request.destination:
            raise ValueError("Origin and destination cannot be the same")
            
        # Validate pax count
        if search_request.pax < 1:
            raise ValueError("Number of passengers must be at least 1")

        # Get both route IDs in one call
        depart_details, return_details = get_roundtrip_route_details(
            search_request.origin, 
            search_request.destination
        )

        # logger.info(f"Processing roundtrip: {search_request.origin}→{search_request.destination} "
        #            f"(depart_route_id: {depart_route_id}, return_route_id: {return_route_id})")

        # Format and validate dates
        sindo_depart_date = search_request.depart_date.strftime("%Y%m%d")
        sindo_return_date = search_request.return_date.strftime("%Y%m%d")

        depart_trips = get_ferry_trips(search_request.origin, search_request.destination, sindo_depart_date)
        return_trips = get_ferry_trips(search_request.destination, search_request.origin, sindo_return_date)

        if depart_trips.get("status") == "error":
            raise ValueError(depart_trips.get("message", "Error fetching departure ferry data"))
        if return_trips.get("status") == "error":
            raise ValueError(return_trips.get("message", "Error fetching return ferry data"))

        # transform departure trips
        depart_display_trips = []
        
        for trip_data in depart_trips.get("trips", []):
            model_data = {camel_to_snake(k): v for k, v in trip_data.items()}
            model_data.update({
                "nationality": search_request.nationality,
                "origin": search_request.origin,
                "destination": search_request.destination,
                "depart_date": search_request.depart_date.isoformat(),
                "return_date": search_request.return_date.isoformat(),
                "pax": search_request.pax,
                "ferry_class": search_request.ferry_class.value,
                "is_round_trip": search_request.is_round_trip,
                "route_id": depart_details.get("route_id"),
                "route_name": depart_details.get("route_name")
            })
            model_data.setdefault("trip_sched_id", "")
            model_data.setdefault("departure_time", "")
            model_data.setdefault("trip_id", "")
            model_data.setdefault("used_seat", "0")
            
            display_trip = (FerryTripDisplay(**model_data))
            # trips_cache[display_trip.route_id] = display_trip #for booking later
            depart_display_trips.append(display_trip)

        # transform return trips
        return_display_trips = []
        for trip_data in return_trips.get("trips", []):
            model_data = {camel_to_snake(k): v for k, v in trip_data.items()}
            model_data.update({
                "nationality": search_request.nationality,
                "origin": search_request.destination,
                "destination": search_request.origin,
                "depart_date": search_request.return_date.isoformat(),
                "return_date": None,
                "pax": search_request.pax,
                "ferry_class": search_request.ferry_class.value,
                "is_round_trip": search_request.is_round_trip,
                "route_id": return_details.get("route_id"),
                "route_name": return_details.get("route_name")
            })
            model_data.setdefault("trip_sched_id", "")
            model_data.setdefault("departure_time", "")
            model_data.setdefault("trip_id", "")
            model_data.setdefault("used_seat", "0")
            
            display_trip = (FerryTripDisplay(**model_data))
            # trips_cache[display_trip.route_id] = display_trip
            return_display_trips.append(display_trip)

        return {
            "departure_trips": depart_display_trips,
            "return_trips": return_display_trips
        }
    except ValueError as e:
        # Convert ValueError to HTTPException
        raise 
    except Exception as e:
        print(f"DEBUG: Error in get_ferry_roundtrip: {str(e)}")
        logger.error(f"Error in get_ferry_roundtrip: {str(e)}", exc_info=True)
        raise Exception(f"Failed to fetch roundtrip ferry data: {str(e)}")


def search_ferry_trips(search_request: TripSearchRequest):
    """Coordinator function to search for ferry trips (handles both one-way and round-trip)"""
    try:
        if search_request.is_round_trip:
            return get_ferry_roundtrip(search_request)
            
        else:
            return get_ferry_oneway(search_request)

    except HTTPException:
        raise  # Re-raise HTTPExceptions
    except ValueError as e:
        logger.error(f"ValueError in search_ferry_trips: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in search_ferry_trips: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search ferry trips: {str(e)}")
    
#Transaction---------------------------------------------------------------------------------
async def call_transaction_service(transaction_data: dict) -> dict:
    """
    Call the transaction service to create a payment transaction
    """
    try:
        # This would be an actual API call to transaction service
        # For development, use mock service
        from .tx_mock_service import create_mock_transaction

        return await create_mock_transaction(transaction_data)

    except Exception as e:
        logger.error(f"Error calling transaction service: {str(e)}")
        raise Exception("Failed to create payment transaction")


def calculate_price(departure_trip: Dict, return_trip: Optional[Dict], 
                   passenger_count: int, ferry_class: str) -> PriceBreakdown:
    """
     Calculate base price based on item and ferry class.
    This is a placeholder implementation.
    """
    # Your implementation here
    base_fare = 100000  # Example base fare
    tax_percentage = 0.1
    tax_amount = base_fare * tax_percentage
    total_amount = base_fare + tax_amount
    
    return PriceBreakdown(
        base_fare=base_fare,
        tax_percentage=tax_percentage,
        tax_amount=tax_amount,
        total_amount=total_amount
    )
    

def prepare_transaction_data(booking_data: FerryBookingRequest, 
                           trip_details: Dict[str, Any],
                           price_breakdown: PriceBreakdown) -> dict:
    """
    Prepare data for transaction service API call
    """
    # Generate a unique order ID
    order_id = f"FERRY_{uuid.uuid4().hex[:8].upper()}"
    
    # Create transaction items
    items = []
    
    # Main fare item
    items.append({
        "name": f"Ferry Ticket: {trip_details['departure_port']} to {trip_details['arrival_port']}",
        "price": price_breakdown.base_fare,
        "quantity": len(booking_data.passengers),
        "description": f"{trip_details['vessel_name']} - {booking_data.ferry_class}",
    })
    
    # Tax item
    if price_breakdown.tax_amount > 0:
        items.append({
            "name": "Tax and Fees",
            "price": price_breakdown.tax_amount,
            "quantity": 1,
            "description": "Government taxes and service fees",
        })
    
    # Prepare customer details
    customer_details = {
        "email": booking_data.contact_info.email,
        "phone": booking_data.contact_info.mobile_phone,
        "first_name": booking_data.passengers[0].name.split()[0] if booking_data.passengers else "",
        "last_name": booking_data.passengers[0].name.split()[-1] if booking_data.passengers else "",
    }
    
    # Prepare the request for transaction service
    return {
        "order_id":order_id,
        "amount":price_breakdown.total_amount,
        "payment_method":booking_data.payment_method.value, # Convert enum to string
        "customer_details":customer_details,
        "item_details":items,
        "description":f"Ferry booking from {trip_details['departure_port']} to {trip_details['arrival_port']}",
        "expiry_duration":24  # 24 hours
    }

#booking---------------------------------------------------------------------------------------    
#Create Booking
def create_ferry_booking(booking_data: dict):
    """
    Kirim booking ke API Sindo.
    """
    data = sindo_client.create_sindo_booking(booking_data)
    # return the full response here 
    # so frontend can get booking ID and other info
    return data

# Add passenger details to an already created booking 
def add_ferry_booking_detail(booking_id: str, passenger_data: dict):
    """
    Tambahkan detail penumpang ke booking Sindo + Booking Requirements.
    """
    # Booking detail ke Sindo API
    data = sindo_client.add_sindo_booking_detail(booking_id, passenger_data)

    # Simpan info tambahan dari frontend (booking requirements)
    booking_requirements = {
        "email": passenger_data.get("email"),
        "confirmation_email": passenger_data.get("confirmation_email"),
        "mobile_phone": passenger_data.get("mobile_phone"),
        "whatsapp_no": passenger_data.get("whatsapp_no"),
    }

    # Simpan di store (bisa diganti DB)
    BOOKING_REQUIREMENTS_STORE[booking_id] = booking_requirements

    # Bungkus response supaya bisa dipakai lagi di get_ferry_booking_details
    return {
        "status": data.get("status", "Ok"),
        "data": data.get("data"),
        "booking_requirements": booking_requirements
    }


# Get Booking details 
def get_ferry_booking_details(booking_id: str, search: str = None):
    data = sindo_client.get_sindo_booking_details(booking_id, search=search)
    records = data.get("data", {}).get("records", [])

    if not records:
        return {"status": "error", "message": "No booking details found"}

    passenger_count = len(records)

    # Ambil harga tiket dari BookingTypePricings
    pricing_data = sindo_client.get_booking_type_pricings()
    pricing_items = pricing_data.get("data", {}).get("records", [])
    default_price = 654000
    price_map = {
        item.get("bookingType", {}).get("name"): item.get("totalPrice", default_price)
        for item in pricing_items
        if isinstance(item.get("bookingType"), dict)
    }

    # Nama penumpang utama
    first_record = records[0]
    passenger_name = (
        first_record.get("passengerName")
        or first_record.get("identification", {}).get("fullName")
        or "Unknown Passenger"
    )

    # Ambil booking header (departureCoreApiTrip.date)
    booking_header = {}
    try:
        header_resp = sindo_client.get_sindo_booking(booking_id)
        booking_header = header_resp.get("data", {}) if header_resp else {}
    except Exception as e:
        logger.warning("Gagal ambil booking header untuk %s: %s", booking_id, e)
        booking_header = {}

    # Normalisasi tanggal
    def _normalize_date(date_str):
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y%m%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        if "T" in date_str:
            return date_str.split("T")[0]
        return date_str.split(" ")[0]

    trip_date = None
    possible_keys = ["departureCoreApiTrip", "departureTrip", "departure", "coreApiTrip"]
    for k in possible_keys:
        trip = booking_header.get(k)
        if isinstance(trip, dict):
            trip_date = _normalize_date(trip.get("date"))
            if trip_date:
                break
    if not trip_date:
        for list_key in ("trips", "coreApiTrips", "departureCoreApiTrips"):
            items = booking_header.get(list_key)
            if isinstance(items, list) and items:
                trip_date = _normalize_date(items[0].get("date"))
                if trip_date:
                    break

    passenger = records[0]
    id_issue_date = passenger.get("identification", {}).get("issueDate")
    departure_date = trip_date or _normalize_date(id_issue_date)

    # 🔑 Ambil email dari BOOKING_REQUIREMENTS_STORE
    booking_requirements = BOOKING_REQUIREMENTS_STORE.get(booking_id, {})
    customer_email = booking_requirements.get("email", "customer@example.com")

    # Buat item list
    items = []
    subtotal = 0
    for i, rec in enumerate(records):
        price = price_map.get(
            rec.get("bookingType", {}).get("name"),
            default_price
        )
        subtotal += price
        items.append({
            "name": f"Ferry Ticket {i+1}",
            "price": price,
            "quantity": 1,
            "description": f"Ferry ticket for passenger {passenger_name}",
            "metadata": {
                "departure_date": departure_date,
                "ferry_number": "SF-123",
                "operator": "Sindo Ferry",
                "class": "Economy"
            }
        })

    tax = int(subtotal * 0.1)
    discount = 0
    total = subtotal + tax - discount

    mapped_response = {
        "email": customer_email,  # ✅ email konsisten dari add_booking_detail
        "transaction_type": "BOOKING",
        "currency": "IDR",
        "service_type": "FERRIES",
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "discount": discount,
        "total": total,
        "payment_method": "credit_card",
        "payment_gateway": "MIDTRANS",
        "transaction_metadata": {
            "order_id": booking_id,
            "passenger_name": passenger_name,
            "booking_reference": f"TQ-FR-{booking_id[:6]}",
            "ip_address": "192.168.1.100"
        },
        "payment_metadata": {
            "bank_name": "BCA",
            "card_last_digits": "1234",
            "card_type": "visa"
        }
    }

    return mapped_response




# Get countries
def get_ferry_countries(search: str = None):
    """
    Ambil daftar negara dari API Sindo.
    """
    data = sindo_client.get_sindo_countries(search)
    records = data.get("data", {}).get("records", [])
    return {"countries": records}

# Delete Booking
def delete_booking_detail(booking_id: str, booking_detail_id: str):
    """
    Service untuk hapus booking detail.
    """
    data = sindo_client.delete_sindo_booking_detail(booking_id, booking_detail_id)
    return data

# submit booking
def submit_ferry_booking(booking_id: str, email_confirmation: str, remarks: str):
    """
    Submit a booking for final processing.
    """
    data = sindo_client.sindo_submit_booking(booking_id, email_confirmation, remarks)
    if data.get("status") == "Ok":
        return {"status": "success", "message": "Booking submitted successfully"}
    else:
        return {"status": "error", "message": "Failed to submit booking"}

# get available sectors
def get_ferry_available_sectors():
    """
    Service untuk ambil sektor ferry yang tersedia.
    """
    data = sindo_client.get_sindo_available_sectors()
    records = data.get("data", {}).get("records", [])
    return {"sectors": records}



# get booking type pricing
def list_booking_type_pricings(search: str = None):
    """
    Service untuk ambil Booking Type Pricings (daftar harga tiket).
    """
    data = sindo_client.get_booking_type_pricings(search)
    if data.get("status") != "Ok":
        return {"status": "error", "message": data}

    records = data["data"].get("records", [])
    # bisa tambahkan normalisasi kalau mau (misal ambil code, name, price saja)
    simplified = [
        {
            "id": rec.get("id"),
            "code": rec.get("bookingType", {}).get("code"),
            "name": rec.get("bookingType", {}).get("name"),
            "isRoundTrip": rec.get("bookingType", {}).get("isRoundTrip"),
            "departureSector": rec.get("bookingType", {}).get("departureSector", {}).get("name"),
            "price": rec.get("totalPrice"),
            "effectiveDate": rec.get("effectiveDate"),
            "expiryDate": rec.get("expiryDate"),
        }
        for rec in records
    ]

    return {"status": "ok", "total": len(simplified), "records": simplified}
