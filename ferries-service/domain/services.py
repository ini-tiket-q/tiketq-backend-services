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
bookings_cache = {}
BOOKING_EXPIRY_HOURS = 1
# Booking list local cache (opsional, bisa dipakai untuk debug)
# _local_bookings = []
        
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

# Get All Trips for users to choose
# raw shedules from Sindo API
def get_ferry_trips(origin: str, destination: str, date: str):
    """
    Ambil daftar trip / jadwal ferry dari API Sindo.
    """
    try:
        sindo_date = date.replace("-", "")
        data = sindo_client.get_sindo_trips(origin, destination, date)
        logger.debug(f"Raw API response: {data}")
        # Kalau API balikin list langsung
        if isinstance(data, list):
            records = data
        else:
            # fallback kalau ada format lain
            records = data.get("data", {}).get("records", [])
        logger.info(f"Found {len(records)} trips")
        return {"trips": records}
    except Exception as e:
        logger.error(f"Error in get_ferry_trips: {str(e)}")
        raise

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
        print("DEBUG: Starting get_ferry_oneway")
        print(f"DEBUG: Search request fields: {search_request.dict()}")
        # Validate origin and destination
        if search_request.origin == search_request.destination:
            raise ValueError("Origin and destination cannot be the same")
            
        # Validate pax count
        if search_request.pax < 1:
            raise ValueError("Number of passengers must be at least 1")
       
        sindo_date = search_request.depart_date.strftime("%Y%m%d")
        
        # Get raw data from Sindo API 
        trips = get_ferry_trips(search_request.origin, search_request.destination, sindo_date)
        # Check if API returned an error
        if trips.get("status") == "error":
            raise ValueError(trips.get("message", "Error fetching ferry data")) 
        
        trips_list = trips.get("trips", [])
            
        # Transform data for frontend consumption
        display_trips = []
        # current_time = datetime.now()
        print("DEBUG: About to process trips list")
        for trip_data in trips_list:
            # Convert date objects to strings
            depart_date_str = search_request.depart_date.isoformat()
            return_date_str = search_request.return_date.isoformat() if search_request.return_date else None
            
            # Create a dictionary with all the data
            model_data = {}
            
            # Convert API response fields from camelCase to snake_case
            for key, value in trip_data.items():
                snake_key = camel_to_snake(key)
                model_data[snake_key] = value
            
            # Add search request fields (already in snake_case)
            model_data.update({
                'nationality': search_request.nationality,
                'origin': search_request.origin,
                'destination': search_request.destination,
                'depart_date': depart_date_str,
                'return_date': return_date_str,
                'pax': search_request.pax,
                'ferry_class': search_request.ferry_class.value,
                'is_round_trip': search_request.is_round_trip,
            })
            
            # Ensure all required fields have values
            model_data.setdefault('trip_sched_id', '')
            model_data.setdefault('departure_time', '')
            model_data.setdefault('trip_id', '')
            model_data.setdefault('used_seat', '0')
            
            print(f"DEBUG: Model data: {model_data}")
            
            try:
                display_trip = FerryTripDisplay(**model_data)
                display_trips.append(display_trip)
            except ValidationError as e:
                print(f"DEBUG: Validation error: {e}")
                raise     
        return display_trips
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        print(f"DEBUG: Error occurred at: {e}")
        raise 
    except Exception as e:
        logger.error(f"Error in get_ferry_oneway: {str(e)}", exc_info=True)
        logger.error(f"Validation error for trip data: {trip_data}. Error: {e}")
        raise Exception(f"Failed to fetch ferry data: {str(e)}")
        
    
def get_ferry_roundtrip(search_request: TripSearchRequest):
    
    try:
        print("DEBUG: Starting get_ferry_roundtrip")
        # Validate origin and destination
        if search_request.origin == search_request.destination:
            raise ValueError("Origin and destination cannot be the same")
            
        # Validate pax count
        if search_request.pax < 1:
            raise ValueError("Number of passengers must be at least 1")

        # Format and validate dates
        sindo_depart_date = search_request.depart_date.strftime("%Y%m%d")
        sindo_return_date = search_request.return_date.strftime("%Y%m%d")
       
        # Get departure trips (origin → destination)
        depart_trips = get_ferry_trips(
            search_request.origin, 
            search_request.destination, 
            sindo_depart_date
        )
        
        # Get return trips (destination → origin)
        return_trips = get_ferry_trips(
            search_request.destination, 
            search_request.origin, 
            sindo_return_date
        )
        
        # Check if API returned errors
        if depart_trips.get("status") == "error":
            raise ValueError(depart_trips.get("message", "Error fetching departure ferry data"))
            
        if return_trips.get("status") == "error":
            raise ValueError(return_trips.get("message", "Error fetching return ferry data"))
        
        # Transform departure trips
        depart_display_trips = []
        print("DEBUG: Processing departure trips")
        for trip_data in depart_trips.get("trips", []):
            print(f"DEBUG: Processing departure trip data: {trip_data}")
            model_data = {}
            for key, value in trip_data.items():
                snake_key = camel_to_snake(key)
                model_data[snake_key] = value
        
            model_data.update({
                'nationality': search_request.nationality,
                'origin': search_request.origin,
                'destination': search_request.destination,
                'depart_date': search_request.depart_date.isoformat(),
                'return_date': search_request.return_date.isoformat(),
                'pax': search_request.pax,
                'ferry_class': search_request.ferry_class.value,
                'is_round_trip': search_request.is_round_trip,
            })
            
            # Ensure required fields
            model_data.setdefault('trip_sched_id', '')
            model_data.setdefault('departure_time', '')
            model_data.setdefault('trip_id', '')
            model_data.setdefault('used_seat', '0')
            
            display_trip = FerryTripDisplay(**model_data)
            depart_display_trips.append(display_trip)
        
        # Transform return trips
        return_display_trips = []
        print("DEBUG: Processing return trips")
        for trip_data in return_trips.get("trips", []):
            print(f"DEBUG: Processing return trip data: {trip_data}")
            model_data = {}
            for key, value in trip_data.items():
                snake_key = camel_to_snake(key)
                model_data[snake_key] = value
                
            model_data.update({
                'nationality': search_request.nationality,
                'origin': search_request.destination,  # Note: swapped for return trip
                'destination': search_request.origin,   # Note: swapped for return trip
                'depart_date': search_request.return_date.isoformat(),  # Use return date for departure
                'return_date': None,
                'pax': search_request.pax,
                'ferry_class': search_request.ferry_class.value,
                'is_round_trip': search_request.is_round_trip,
            })
            
            # Ensure required fields
            model_data.setdefault('trip_sched_id', '')
            model_data.setdefault('departure_time', '')
            model_data.setdefault('trip_id', '')
            model_data.setdefault('used_seat', '0')
            
            display_trip = FerryTripDisplay(**model_data)
            return_display_trips.append(display_trip)
        print("DEBUG: Roundtrip processing completed successfully")
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
        logger.info(f"Searching ferry trips with request: {search_request.dict()}")
        if search_request.is_round_trip:
            logger.info("Processing round trip")
            return get_ferry_roundtrip(search_request)
            
        else:
            logger.info("Processing one-way trip")
            return get_ferry_oneway(search_request)

    except Exception as e:
        logger.error(f"Error in search_ferry_trips: {str(e)}")
        # import traceback
        # traceback.print_exc()
        raise ValueError(f"Failed to search ferry trips: {str(e)}")
    
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

# def create_ferry_booking_v2(booking_data: dict):
#     """
#     Kirim booking ke API Sindo.
#     """
#     data = sindo_client.create_sindo_booking(booking_data)
    # return the full response here 
    # so frontend can get booking ID and other info
    # return data
    
#booking---------------------------------------------------------------------------------------    
async def create_ferry_booking(booking_data: FerryBookingRequest) -> FerryBookingResponse:
    """
    Create a ferry booking with transaction service integration
    """
    try:
        # 1. Validate availability (pseudo-code)
        # if not validate_availability(booking_data.departure_schedule_id, len(booking_data.passengers)):
        #     raise ValueError("Not enough available seats")
        
        # if booking_data.is_round_trip and booking_data.return_schedule_id:
        #     if not validate_availability(booking_data.return_schedule_id, len(booking_data.passengers)):
        #         raise ValueError("Not enough available seats for return trip")
        
        # 2. Get trip details and calculate price (pseudo-code)
        # departure_trip = get_trip_details(booking_data.departure_schedule_id)
        # return_trip = None
        # if booking_data.is_round_trip and booking_data.return_schedule_id:
        #     return_trip = get_trip_details(booking_data.return_schedule_id)
        
        # For demonstration, create mock trip details
        departure_trip = {
            "departure_port": "BTC",
            "arrival_port": "HFC", 
            "vessel_name": "Fast Ferry",
            "departure_time": "08:00",
            "arrival_time": "10:00"
        }
        
        price_breakdown = calculate_price(
            departure_trip, 
            None, 
            len(booking_data.passengers),
            booking_data.ferry_class
        )
        
        # 3. Prepare transaction data as dict
        transaction_data = prepare_transaction_data(
            booking_data, 
            departure_trip, 
            price_breakdown
        )
        
        # 4. Call transaction service
        transaction_response = await call_transaction_service(transaction_data)
        # 5. Create Sindo booking (pseudo-code)
        # sindo_booking_data = normalize_booking_for_sindo(booking_data)
        # sindo_response = sindo_client.create_sindo_booking(sindo_booking_data)
        
        # For demonstration,create a mock Sindo response
        sindo_booking_id = f"SINDO_{uuid.uuid4().hex[:8].upper()}"
        # 6. Create booking record
        internal_booking_id = str(uuid.uuid4())
        expiry_time = datetime.now() + timedelta(hours=BOOKING_EXPIRY_HOURS)
        
        # Store booking in cache(replace with database in production)
        bookings_cache[internal_booking_id] = {
            "sindo_booking_id": booking_data.sindo_booking_id,
            "status": BookingStatus.PENDING,
            "total_amount": price_breakdown.total_amount,
            "currency": "IDR",
            "transaction_id": transaction_response.transaction_id, #access as dict
            "passengers": booking_data.passengers,
            "contact_info": booking_data.contact_info,
            "expires_at": expiry_time,
            "created_at": datetime.now()
        }
        
        # 7. Return response
        return FerryBookingResponse(
            booking_id=internal_booking_id,
            sindo_booking_id=sindo_booking_id,
            status=BookingStatus.PENDING,
            total_amount=price_breakdown.total_amount,
            currency="IDR",
            transaction_id=transaction_response["transaction_id"],  # Access as dict key
            payment_url=transaction_response["payment_url"],  # Access as dict key
            expires_at=expiry_time,
            metadata={}
        )
        
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}", exc_info=True)
        raise
             

# Add passenger details to an already created booking
def add_ferry_booking_detail(booking_id: str, passenger_data: dict):
    """
    Tambahkan detail penumpang ke booking Sindo.
    """
    data = sindo_client.add_sindo_booking_detail(booking_id, passenger_data)
    return data


# Get Booking details 
def get_ferry_booking_details(booking_id: str, search: str = None):
    """
    Ambil detail penumpang dari sebuah booking.
    """
    data = sindo_client.get_sindo_booking_details(booking_id, search=search)
    records = data.get("data", {}).get("records", [])
    return {"booking_details": records}

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
    try:
        data = sindo_client.get_sindo_available_sectors()
        
        if data.get("status") == "Ok":
            sectors = data.get("data", {}).get("records", [])
            return {"status": "success", "sectors": sectors}
        else:
            return {"status": "error", "message": "Failed to fetch sectors"}
    except Exception as e:
        logger.error(f"Error in get_available_sectors: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}