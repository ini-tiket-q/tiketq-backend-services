import requests
from typing import List, Optional
from datetime import datetime, time
import os
from domain.models import TrainStation, TrainSchedule, TrainSearchRequest, TrainBooking, TrainBookingRequest, TrainClass
from domain.repository import ExternalTrainAPIRepository, TrainStationRepository

class StaticTrainStationAdapter(TrainStationRepository):
    """Static adapter for train stations (could be replaced with API or DB)"""
    
    def __init__(self):
        # Static data for Indonesian train stations
        self.stations = [
            TrainStation("GMR", "Gambir", "Jakarta", "DKI Jakarta"),
            TrainStation("PSE", "Pasar Senen", "Jakarta", "DKI Jakarta"),
            TrainStation("KMT", "Kota", "Jakarta", "DKI Jakarta"),
            TrainStation("TNK", "Tanah Abang", "Jakarta", "DKI Jakarta"),
            TrainStation("BD", "Bandung", "Bandung", "Jawa Barat"),
            TrainStation("YK", "Yogyakarta", "Yogyakarta", "DI Yogyakarta"),
            TrainStation("SLO", "Solo Balapan", "Surakarta", "Jawa Tengah"),
            TrainStation("SMG", "Semarang", "Semarang", "Jawa Tengah"),
            TrainStation("SB", "Surabaya", "Surabaya", "Jawa Timur"),
            TrainStation("ML", "Malang", "Malang", "Jawa Timur"),
        ]
    
    def get_all_stations(self) -> List[TrainStation]:
        """Get all train stations"""
        return self.stations
    
    def get_station_by_code(self, code: str) -> Optional[TrainStation]:
        """Get station by code"""
        for station in self.stations:
            if station.code == code:
                return station
        return None
    
    def search_stations(self, query: str) -> List[TrainStation]:
        """Search stations by name or city"""
        query_lower = query.lower()
        results = []
        
        for station in self.stations:
            if (query_lower in station.name.lower() or 
                query_lower in station.city.lower() or
                query_lower in station.code.lower()):
                results.append(station)
        
        return results

# TODO: KAI API Adapter will be implemented in next phase
class MockKAIAccessAPIAdapter(ExternalTrainAPIRepository):
    """Mock adapter for development purposes"""
    
    def search_trains(self, search_request: TrainSearchRequest) -> List[TrainSchedule]:
        # Return mock data for now
        return []
    
    def create_booking(self, booking_request: TrainBookingRequest) -> TrainBooking:
        # Return mock booking for now
        from datetime import datetime, time
        return TrainBooking(
            booking_id="MOCK123",
            pnr="PNRMOCK",
            train_number=booking_request.train_number,
            train_name="Mock Train",
            departure_station=TrainStation("GMR", "Gambir", "Jakarta", "DKI Jakarta"),
            arrival_station=TrainStation("BD", "Bandung", "Bandung", "Jawa Barat"),
            departure_time=time(8, 0),
            arrival_time=time(12, 0),
            booking_date=datetime.now(),
            status="confirmed",
            total_price=500000.0,
            passengers=booking_request.passengers,
            contact_info=booking_request.contact_info
        )
    
    def cancel_booking(self, booking_id: str) -> bool:
        return True
    
    def get_booking_status(self, booking_id: str) -> str:
        return "confirmed"