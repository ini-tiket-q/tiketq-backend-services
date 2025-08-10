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