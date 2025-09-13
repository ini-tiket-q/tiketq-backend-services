from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import uuid
from fastapi import HTTPException
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

def format_date_for_sindo(date_str: str) -> str:
    """
    Convert date string to Sindo's required yyyyMMdd format.
    Raises ValueError for invalid dates.
    """
    try:
        return date_obj.strftime('%Y%m%d')
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        raise ValueError("Invalid date format")
            
            
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
def get_ferry_trips(departure: str, destination: str, date: str):
    """
    Ambil daftar trip / jadwal ferry dari API Sindo.
    """
    data = sindo_client.get_sindo_trips(departure, destination, date)

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
        # Validate origin and destination
        if search_request.departure == search_request.destination:
            raise ValueError("Origin and destination cannot be the same")
            
        # Validate pax count
        if search_request.pax < 1:
            raise ValueError("Number of passengers must be at least 1")
        
        # Get available sectors to validate the route
        sectors_response = get_ferry_available_sectors()
        if sectors_response.get("status") == "error":
            raise ValueError(sectors_response.get("message", "Error fetching available sectors"))
        
        sectors = sectors_response.get("sectors", [])
        
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
                available_seats=item.get("availableSeats", 0), # Use actual field from API
                base_price=base_price,
                currency="IDR",
                vessel_name=item.get("vesselName", "Unknown Vessel"),
                operator=item.get("operator", "Unknown Operator"),
                departure_port=search_request.departure,
                arrival_port=search_request.destination,
                tax_percentage=0.1,  # Example 10% tax
                tax_amount=base_price * 0.1,
                total_price=base_price * 1.1  # Base + tax,
                metadata=item
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
