from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(slots=True)
class Flight:
    id: Optional[str]
    flight_number: str
    from_airport: str
    to_airport: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: str
    gate: Optional[str] = None
    terminal: Optional[str] = None
    status: str = "SCHEDULED"
    notes: Optional[str] = None
