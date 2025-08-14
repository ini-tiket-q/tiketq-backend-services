from typing import List, Optional
from .models import TrainStation, TrainSchedule, TrainSearchRequest, TrainBooking, TrainBookingRequest
from .repository import TrainStationRepository, ExternalTrainAPIRepository, TrainBookingRepository

class TrainSearchService:
    """Business logic for train search operations"""
    
    def __init__(self, external_api: ExternalTrainAPIRepository, station_repo: TrainStationRepository):
        self.external_api = external_api
        self.station_repo = station_repo
    
    def search_trains(self, search_request: TrainSearchRequest) -> List[TrainSchedule]:
        """Search for available trains"""
        # Validate stations exist
        origin = self.station_repo.get_station_by_code(search_request.origin_code)
        destination = self.station_repo.get_station_by_code(search_request.destination_code)
        
        if not origin:
            raise ValueError(f"Origin station with code {search_request.origin_code} not found")
        
        if not destination:
            raise ValueError(f"Destination station with code {search_request.destination_code} not found")
        
        # Search trains via external API
        schedules = self.external_api.search_trains(search_request)
        
        # Apply business rules (filtering, sorting, etc.)
        return self._apply_business_rules(schedules)
    
    def _apply_business_rules(self, schedules: List[TrainSchedule]) -> List[TrainSchedule]:
        """Apply business rules like filtering sold out trains, sorting by price, etc."""
        # Filter out trains with no available seats
        available_schedules = [
            schedule for schedule in schedules 
            if any(cls.available_seats > 0 for cls in schedule.classes)
        ]
        
        # Sort by departure time
        available_schedules.sort(key=lambda s: s.departure_time)
        
        return available_schedules

class TrainStationService:
    """Business logic for train station operations"""
    
    def __init__(self, station_repo: TrainStationRepository):
        self.station_repo = station_repo
    
    def get_all_stations(self) -> List[TrainStation]:
        """Get all available train stations"""
        return self.station_repo.get_all_stations()
    
    def search_stations(self, query: str) -> List[TrainStation]:
        """Search stations by name or city"""
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
        return self.station_repo.search_stations(query)

class TrainBookingService:
    """Business logic for train booking operations"""
    
    def __init__(self, external_api: ExternalTrainAPIRepository, booking_repo: TrainBookingRepository):
        self.external_api = external_api
        self.booking_repo = booking_repo
    
    def create_booking(self, booking_request: TrainBookingRequest, user_id: str) -> TrainBooking:
        """Create a new train booking"""
        # Validate booking request
        self._validate_booking_request(booking_request)
        
        # Create booking via external API
        booking = self.external_api.create_booking(booking_request)
        
        # Store booking locally for tracking
        if self.booking_repo:
            booking = self.booking_repo.create_booking(booking)
        
        return booking
    
    def get_booking(self, booking_id: str, user_id: str) -> Optional[TrainBooking]:
        """Get booking by ID (with user authorization)"""
        if not self.booking_repo:
            return None
            
        booking = self.booking_repo.get_booking_by_id(booking_id)
        
        if not booking:
            return None
        
        # Check if user owns this booking (implement based on your auth system)
        return booking
    
    def cancel_booking(self, booking_id: str, user_id: str) -> bool:
        """Cancel a booking"""
        booking = self.get_booking(booking_id, user_id)
        
        if not booking:
            raise ValueError("Booking not found or unauthorized")
        
        if booking.status != "confirmed":
            raise ValueError("Can only cancel confirmed bookings")
        
        return self.external_api.cancel_booking(booking_id)
    
    def _validate_booking_request(self, booking_request: TrainBookingRequest):
        """Validate booking request"""
        if not booking_request.passengers:
            raise ValueError("At least one passenger is required")
        
        if not booking_request.contact_info:
            raise ValueError("Contact information is required")