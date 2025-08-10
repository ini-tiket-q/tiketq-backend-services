from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, time

@dataclass
class TrainStation:
    """Domain model for train station"""
    code: str
    name: str
    city: str
    province: str

@dataclass
class TrainClass:
    """Domain model for train class"""
    class_name: str
    subclass: str
    fare: float
    available_seats: int

@dataclass
class TrainSchedule:
    """Domain model for train schedule"""
    train_number: str
    train_name: str
    departure_station: TrainStation
    arrival_station: TrainStation
    departure_time: time
    arrival_time: time
    duration: str
    classes: List[TrainClass]
    date: str

@dataclass
class TrainSearchRequest:
    """Domain model for train search request"""
    origin_code: str
    destination_code: str
    departure_date: str
    adult_count: int = 1
    infant_count: int = 0

@dataclass
class TrainBookingRequest:
    """Domain model for train booking request"""
    train_number: str
    departure_date: str
    class_name: str
    subclass: str
    passengers: List[dict]
    contact_info: dict

@dataclass
class TrainBooking:
    """Domain model for train booking"""
    booking_id: str
    pnr: str
    train_number: str
    train_name: str
    departure_station: TrainStation
    arrival_station: TrainStation
    departure_time: time
    arrival_time: time
    booking_date: datetime
    status: str
    total_price: float
    passengers: List[dict]
    contact_info: dict