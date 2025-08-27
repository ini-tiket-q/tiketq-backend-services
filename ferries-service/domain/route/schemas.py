rom __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time


# ---------- Port ----------
class PortBase(BaseModel):
    code: str
    name: str
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class PortCreate(PortBase):
    pass

class PortRead(PortBase):
    id: int
    
    class Config:
        from_attributes = True


# ---------- Route ----------
class RouteBase(BaseModel):
    origin_id: int
    destination_id: int
    distance_km: Optional[float] = None
    duration_est: Optional[int] = None
    is_popular: bool = False

class RouteCreate(RouteBase):
    pass

class RouteRead(RouteBase):
    id: int
    
    class Config:
        from_attributes = True


# ---------- Sector ----------
class SectorBase(BaseModel):
    name: str
    primary_route_id: int
    next_sector_id: Optional[int] = None
    is_roundtrip: bool = False

class SectorCreate(SectorBase):
    pass

class SectorRead(SectorBase):
    id: int
    
    class Config:
        from_attributes = True


# ---------- Trip ----------
class TripBase(BaseModel):
    route_id: int
    ferry_id: int
    sector_id: int
    ferry_class_id: int
    departure_datetime: datetime
    arrival_datetime: datetime
    price_override: Optional[float] = None
    status: str = "SCHEDULED"
    metadata: Optional[dict] = None

class TripCreate(TripBase):
    pass

class TripRead(TripBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
        
