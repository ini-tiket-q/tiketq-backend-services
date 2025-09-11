from datetime import datetime, timedelta
from typing import Optional
import uuid
from fastapi import HTTPException
from domain.models import (
    FerryBookingRequest, 
    FerryBookingResponse, 
    FerryTripDisplay, 
    TripSearchRequest, 
    TripSearchResponse
)
from adapters.external_api import SindoClient
import logging

logger = logging.getLogger(__name__)
# Initialize the SindoClient instance
sindo_client = SindoClient()
BOOKING_EXPIRY_HOURS = 1
# Booking list local cache (opsional, bisa dipakai untuk debug)
# _local_bookings = []

def format_date_for_sindo(date_str: str) -> str:
    """
    Convert date string to Sindo's required yyyyMMdd format.
    Raises ValueError for invalid dates.
    """
    try:
        # Try to parse the date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Ensure date is not in the past
        if date_obj.date() < datetime.now().date():
            raise ValueError("Date cannot be in the past")
            
        return date_obj.strftime('%Y%m%d')
    except ValueError:
        # Re-raise with a more specific message
        raise ValueError("Date must be in YYYY-MM-DD format and not in the past")

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
    data = sindo_client.get_sindo_trips(origin, destination, date)

    # Kalau API balikin list langsung
    if isinstance(data, list):
        records = data
    else:
        # fallback kalau ada format lain
        records = data.get("data", {}).get("records", [])

    return {"trips": records}


def get_ferry_oneway(search_request: TripSearchRequest):
    try:
        # Validate origin and destination
        if search_request.departure == search_request.destination:
            raise ValueError("Origin and destination cannot be the same")
            
        # Validate pax count
        if search_request.pax < 1:
            raise ValueError("Number of passengers must be at least 1")
        
        # Get available sectors to validate the route
        sectors = get_ferry_available_sectors()
        
        # Find the sector that matches the departure and destination
        matching_sector = None
        for sector in sectors:
            if (search_request.departure in sector["code"] and 
                search_request.destination in sector["code"]):
                matching_sector = sector
                break
        
        if not matching_sector:
            raise ValueError("No available route between selected locations")
        
        sindo_date = format_date_for_sindo(search_request.depart_date)
        
        # Get raw data from Sindo API 
        trips = get_ferry_trips(matching_sector[""], sindo_date)
        # Check if API returned an error
        if trips.get("status") == "error":
            raise ValueError(trips.get("message", "Error fetching ferry data")) 
        
        trips_list = trips.get("trips", [])
            
        # Transform data for frontend consumption
        display_trips = []
        current_time = datetime.now()
        
        for item in trips_list:
           # Calculate duration from departure and arrival times
            dep_time = datetime.strptime(item.get("departureTime", "00:00"), "%H:%M")
            arr_time = datetime.strptime(item.get("arrivalTime", "00:00"), "%H:%M")
            duration_minutes = (arr_time - dep_time).total_seconds() / 60
            duration = f"{int(duration_minutes // 60)}h {int(duration_minutes % 60)}m"
            
            # Calculate base price per passenger
            base_price = calculate_base_price(item, search_request.ferry_class)
              
            #create FerryTripDisplay object with pricing info    
            display_trip = FerryTripDisplay(
                schedule_id=uuid.UUID(item.get("tripSchedID", str(uuid.uuid4()))),
                departure_time=item.get("departureTime"),
                arrival_time=item.get("arrivalTime"),
                duration=duration,
                status=item.get("status", "Available"),
                available_seats=calculate_available_seats(item),
                base_price=base_price,
                currency="IDR",
                vessel_name=get_vessel_name(item.get("tripID")),
                operator=get_operator_name(item.get("tripID")),
                departure_port=search_request.departure,
                arrival_port=search_request.destination,
                tax_percentage=0.1,  # Example 10% tax
                tax_amount=base_price * 0.1,
                total_price=base_price * 1.1  # Base + tax
            )
            display_trips.append(display_trip)
        
        return TripSearchResponse(
            status="success",
            departure_trips=display_trips
        )
    except ValueError as e:
        # Re-raise ValueError exceptions
        raise 
    except Exception as e:
        logger.error(f"Error in get_ferry_oneway: {str(e)}", exc_info=True)
        raise Exception(f"Failed to fetch ferry data: {str(e)}")
        
    
def get_ferry_roundtrip(search_request: TripSearchRequest):
    
    try:
        # Validate origin and destination
        if search_request.departure == search_request.destination:
            raise ValueError("Origin and destination cannot be the same")
            
        # Validate pax count
        if search_request.pax < 1:
            raise ValueError("Number of passengers must be at least 1")
        
        # Get departure trips
        depart_search = TripSearchRequest(
            nationality=search_request.nationality,
            departure=search_request.departure,
            destination=search_request.destination,
            depart_date=search_request.depart_date,
            pax=search_request.pax,
            ferry_class=search_request.ferry_class,
            is_round_trip=False
        )
        # Get departure trips (origin → destination)
        depart_result = get_ferry_oneway(depart_search)        
             
        # Get return trips
        return_search = TripSearchRequest(
            nationality=search_request.nationality,
            departure=search_request.destination,
            destination=search_request.departure,
            depart_date=search_request.return_date,
            pax=search_request.pax,
            ferry_class=search_request.ferry_class,
            is_round_trip=True
        )
        # Get return trips (destination → origin) 
        return_result = get_ferry_oneway(return_search)

        
        # Check if either request failed
        if depart_result.get("status") == "error":
            return depart_result
        if return_result.get("status") == "error":
            return return_result
        
        return TripSearchResponse(
            status="success",
            departure_trips=depart_result.departure_trips,
            return_trips=return_result.departure_trips
        )
    except ValueError as e:
        # Convert ValueError to HTTPException
        raise 
    except Exception as e:
        logger.error(f"Error in get_ferry_roundtrip: {str(e)}", exc_info=True)
        raise Exception(f"Failed to fetch roundtrip ferry data: {str(e)}")


def search_ferry_trips(search_request: TripSearchRequest):
    """Coordinator function to search for ferry trips (handles both one-way and round-trip)"""
    try:
        if search_request.is_round_trip:
            return get_ferry_roundtrip(search_request)
        else:
            return get_ferry_oneway(search_request)
            
    except ValueError as e:
        # Re-raise ValueError exceptions
        raise
    except Exception as e:
        logger.error(f"Error in search_ferry_trips: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to search ferry trips: {str(e)}")
    

#Create Booking
def create_ferry_booking(booking_data: dict):
    """
    Kirim booking ke API Sindo.
    """
    data = sindo_client.create_sindo_booking(booking_data)
    # return the full response here 
    # so frontend can get booking ID and other info
    return data
    
    
def create_ferry_booking_v2(booking_request: FerryBookingRequest) -> FerryBookingResponse:
    """
    Create a ferry booking with proper normalization between frontend and Sindo API
    """
    try:
        # Normalize data for Sindo API
        sindo_booking_data = normalize_booking_for_sindo(booking_request)
        
        # Add agent information (required by Sindo API)
        sindo_booking_data["AgentCode"] = sindo_client.agent_code
        sindo_booking_data["UserName"] = sindo_client.username
        
        # Call the Sindo API
        sindo_response = sindo_client.create_sindo_booking(sindo_booking_data)
        
        # Normalize response for frontend later
        #booking_response = normalize_booking_for_frontend(sindo_response, booking_request)
        #Basic response mapping (can be enhanced later for frontend)
        internal_booking_id = str(uuid.uuid4())
        
        return FerryBookingResponse(
            booking_id=internal_booking_id,
            sindo_booking_id=sindo_response.get("BookingId", ""),
            status=sindo_response.get("Status", "PENDING"),
            total=sindo_response.get("TotalAmount", 0),
            currency=sindo_response.get("Currency", "IDR"),
            payment_url=None,  # Can be implemented later
            expires_at=datetime.now() + timedelta(hours=BOOKING_EXPIRY_HOURS),
            metadata=sindo_response  
        )
        # return booking_response       
    except Exception as e:
        logger.error(f"Error in create_booking_v2: {str(e)}", exc_info=True)
        raise Exception("Failed to create booking: {str(e)}")
        
        
def normalize_booking_for_sindo(booking_request: FerryBookingRequest) -> dict:        
    
    departure_trip = booking_request.departure_trip
    return_trip = booking_request.return_trip
    
    base_data = {
        "IsRoundTrip": booking_request.is_round_trip,
        "FerryClass": booking_request.ferry_class,
        "DepartureTrip": {
            "TripID": departure_trip.get("trip_id"),
            "ScheduleID": departure_trip.get("schedule_id"),
            "Origin": departure_trip.get("origin"),
            "Destination": departure_trip.get("destination"),
            "DepartureDate": departure_trip.get("departure_date"),
            "DepartureTime": departure_trip.get("departure_time"),
            "Operator": departure_trip.get("operator", ""),
        },
        "Passengers": [{
            "Type": passenger.type,
            "Title": passenger.title,
            "Name": passenger.name,
            "PassportNo": passenger.passport_no,
            "Nationality": passenger.nationality,
            "IssuingCountry": passenger.issuing_country,
            "DateOfBirth": passenger.date_of_birth.isoformat(),
            "PassportExpiry": passenger.passport_expiry.isoformat(),
            "PassportIssue": passenger.passport_issue.isoformat()
        } for passenger in booking_request.passengers],
        "Requirements": {
            "Email": booking_request.requirements.email,
            "ConfirmEmail": booking_request.requirements.confirm_email,
            "MobilePhone": booking_request.requirements.mobile_phone,
            "WhatsappNo": booking_request.requirements.whatsapp_no
        }
    }
    # Add return trip if it's a round trip
    if booking_request.is_round_trip and return_trip:
        base_data["ReturnTrip"] = {
            "TripID": return_trip.get("trip_id"),
            "ScheduleID": return_trip.get("schedule_id"),
            "Origin": return_trip.get("origin"),
            "Destination": return_trip.get("destination"),
            "DepartureDate": return_trip.get("departure_date"),
            "DepartureTime": return_trip.get("departure_time"),
            "Operator": return_trip.get("operator", ""),
        }
    
    return base_data

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