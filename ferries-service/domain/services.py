from datetime import datetime, timedelta
from typing import Optional
import uuid
from fastapi import HTTPException
from domain.models import FerryBookingRequest, FerryBookingResponse
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


def get_ferry_oneway(nationality: str, origin: str, destination: str, depart_date: str,
                       pax: int = 1, ferry_class: str = "economy"):
    try:
        # Validate origin and destination
        if origin == destination:
            raise ValueError("Origin and destination cannot be the same")
            
        # Validate pax count
        if pax < 1:
            raise ValueError("Number of passengers must be at least 1")
        
        sindo_date = format_date_for_sindo(depart_date)
        
        # Get raw data from Sindo API using the general function
        schedules = get_ferry_trips(origin, destination, sindo_date)
        # Check if API returned an error
        if schedules.get("status") == "error":
            raise ValueError(schedules.get("message", "Error fetching ferry data")) 
        
        trips_list = schedules.get("trips", [])
            
        # Transform data for frontend consumption
        display_trips = []
        internal_trips = []
        
        for item in trips_list:
            display_trips = {                         
                "nationality": nationality,
                "pax": pax,
                "ferry_class": ferry_class,
                
                
            }
            display_trips.append(display_trips) 
             
            # Internal data for booking
            internal_trip = {
                "route": f"{origin}-{destination}",
                "raw_data": item
                
            #     "departure_time": item.get("departureTime"),
            #     "arrival_time": item.get("arrivalTime"),
            #     "status": item.get("status"),
            #     "available_seats": item.get("usedSeat"),                            
            #      # Basic pricing info (if available)
            #     # "price_per_pax": item.get("price", 0),  # Simple price per passenger
            #     # "currency": "IDR",
                
            #     # Other info
            
            }
                    
        return {
            "status": "success", 
            "display_data": display_trips,  # For frontend display
            "internal_data": internal_trips  # For internal booking use
        }
    except ValueError as e:
        
        raise 
    except Exception as e:
        logger.error(f"Error in get_ferry_oneway: {str(e)}", exc_info=True)
        raise Exception("Failed to fetch ferry data from provider")
        
    
def get_ferry_roundtrip(nationality: str, origin: str, destination: str, 
                       depart_date: str, return_date: str, pax: int = 1, 
                       ferry_class: str = "economy"):
    try:
        # Validate origin and destination
        if origin == destination:
            raise ValueError("Origin and destination cannot be the same")
            
        # Validate pax count
        if pax < 1:
            raise ValueError("Number of passengers must be at least 1")
        
        # Format and validate dates
        sindo_depart_date = format_date_for_sindo(depart_date)
        sindo_return_date = format_date_for_sindo(return_date)
        
        # Validate return date is not before departure date
        depart_dt = datetime.strptime(depart_date, '%Y-%m-%d')
        return_dt = datetime.strptime(return_date, '%Y-%m-%d')
        
        if return_dt < depart_dt:
            raise ValueError("Return date cannot be before departure date")    
        
        # Get departure trips (origin → destination)
        depart_result = get_ferry_oneway(
            nationality, origin, destination, depart_date, pax, ferry_class
        )
        
        # Get return trips (destination → origin) 
        return_result = get_ferry_oneway(
            nationality, destination, origin, return_date, pax, ferry_class
        )
        
        # Check if either request failed
        if depart_result.get("status") == "error":
            return depart_result
        if return_result.get("status") == "error":
            return return_result
        
        # Combine the results
        return {
            "status": "success",
            "display_data": {
                "departure_trips": depart_result.get("display_data", []),
                "return_trips": return_result.get("display_data", [])
            },
            "internal_data": {
                "departure_trips": depart_result.get("internal_data", []),
                "return_trips": return_result.get("internal_data", [])
            }
        }
    except ValueError as e:
        # Convert ValueError to HTTPException
        raise 
    except Exception as e:
        # Log the error here if needed
        raise Exception("Failed to fetch roundtrip ferry data")

def search_ferry_trips(nationality: str, origin: str, destination: str,
                      depart_date: str, is_round_trip: bool = False,
                      return_date: Optional[str] = None, pax: int = 1,
                      ferry_class: str = "economy"):
    """
    Coordinator function that calls the appropriate specific service
    """
   
    if is_round_trip:
        if not return_date:
            raise ValueError("Return date required for round trips")
            
        return get_ferry_roundtrip(
            nationality, origin, destination, 
            depart_date, return_date, pax, ferry_class
        )
                
    else:
        return get_ferry_oneway(
            nationality, origin, destination, 
            depart_date, pax, ferry_class
        )
    

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
    data = sindo_client.get_sindo_booking_details(booking_id, search=search)
    records = data.get("data", {}).get("records", [])

    if not records:
        return {"status": "error", "message": "No booking details found"}

    passenger_count = len(records)

    # --- Ambil harga tiket dari BookingTypePricings ---
    pricing_data = sindo_client.get_booking_type_pricings()
    pricing_items = pricing_data.get("data", {}).get("records", [])
    default_price = 654000
    price_map = {
        item.get("bookingType", {}).get("name"): item.get("totalPrice", default_price)
        for item in pricing_items
        if isinstance(item.get("bookingType"), dict)
    }

    # --- Nama penumpang utama ---
    first_record = records[0]
    passenger_name = (
        first_record.get("passengerName")
        or first_record.get("identification", {}).get("fullName")
        or "Unknown Passenger"
    )

    # Coba ambil booking header (supaya dapat departureCoreApiTrip.date)
    booking_header = {}
    try:
        header_resp = sindo_client.get_sindo_booking(booking_id)
        booking_header = header_resp.get("data", {}) if header_resp else {}
    except Exception as e:
        logger.warning("Gagal ambil booking header untuk %s: %s", booking_id, e)
        booking_header = {}

    # helper untuk normalisasi tanggal ke YYYY-MM-DD
    def _normalize_date(date_str):
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y%m%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        # fallback sederhana
        if "T" in date_str:
            return date_str.split("T")[0]
        return date_str.split(" ")[0]

    # Coba beberapa key yang mungkin mengandung tanggal trip
    trip_date = None
    # biasanya: booking_header.get("departureCoreApiTrip", {}).get("date")
    possible_keys = ["departureCoreApiTrip", "departureTrip", "departure", "coreApiTrip"]
    for k in possible_keys:
        trip = booking_header.get(k)
        if isinstance(trip, dict):
            trip_date = _normalize_date(trip.get("date"))
            if trip_date:
                break

    # fallback: jika header berisi list trips / coreApiTrips
    if not trip_date:
        for list_key in ("trips", "coreApiTrips", "departureCoreApiTrips"):
            items = booking_header.get(list_key)
            if isinstance(items, list) and items:
                trip_date = _normalize_date(items[0].get("date"))
                if trip_date:
                    break

    # terakhir fallback: pakai identification.issueDate dari passenger (sebelumnya dipakai)
    passenger = records[0]
    id_issue_date = passenger.get("identification", {}).get("issueDate")
    departure_date = trip_date or _normalize_date(id_issue_date)


    # --- Ambil harga tiap penumpang (sementara 1 flight saja) ---
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
                "departure_date": departure_date,   # TODO: ambil dari rec kalau ada
                "ferry_number": "SF-123",         # TODO: mapping ke data asli
                "operator": "Sindo Ferry",        # fixed untuk sekarang
                "class": "Economy"                # default sementara
            }
        })


    # --- Hitung tax & discount ---
    tax = int(subtotal * 0.1)    # contoh 10% pajak
    discount = 0                 # sementara belum ada diskon
    total = subtotal + tax - discount

    # --- Mapping ke format baru ---
    mapped_response = {
        "email": "customer@example.com",
        "transaction_type": "BOOKING",
        "currency": "IDR",
        "service_type": "FERRIES",
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "discount": discount,
        "total": total,
        "payment_method": "credit_card",
        "payment_gateway": "MIDTRANS",  # default sementara
        "transaction_metadata": {
            "order_id": booking_id,
            "passenger_name": passenger_name,
            "booking_reference": f"TQ-FR-{booking_id[:6]}",  # contoh reference
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
