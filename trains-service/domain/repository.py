from abc import ABC, abstractmethod
from typing import List, Optional
from .models import TrainStation, TrainSchedule, TrainSearchRequest, TrainBooking, TrainBookingRequest

class TrainStationRepository(ABC):
    """Port for train station data access"""
    
    @abstractmethod
    def get_all_stations(self) -> List[TrainStation]:
        pass
    
    @abstractmethod
    def get_station_by_code(self, code: str) -> Optional[TrainStation]:
        pass
    
    @abstractmethod
    def search_stations(self, query: str) -> List[TrainStation]:
        pass

class TrainBookingRepository(ABC):
    """Port for train booking data access"""
    
    @abstractmethod
    def create_booking(self, booking: TrainBooking) -> TrainBooking:
        pass
    
    @abstractmethod
    def get_booking_by_id(self, booking_id: str) -> Optional[TrainBooking]:
        pass
    
    @abstractmethod
    def get_user_bookings(self, user_id: str) -> List[TrainBooking]:
        pass

class ExternalTrainAPIRepository(ABC):
    """Port for external train API integration"""
    
    @abstractmethod
    def search_trains(self, search_request: TrainSearchRequest) -> List[TrainSchedule]:
        pass
    
    @abstractmethod
    def create_booking(self, booking_request: TrainBookingRequest) -> TrainBooking:
        pass
    
    @abstractmethod
    def cancel_booking(self, booking_id: str) -> bool:
        pass
    
    @abstractmethod
    def get_booking_status(self, booking_id: str) -> str:
        pass