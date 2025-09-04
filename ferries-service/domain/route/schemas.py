
from pydantic import BaseModel
from typing import List, Optional

class TripSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None  # only for round trip

class TripOption(BaseModel):
    id: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price: float

class TripSearchResponse(BaseModel):
    trips: List[TripOption]

