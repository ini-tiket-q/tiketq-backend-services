from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, Literal, Annotated, List, Dict
from datetime import datetime, date

# --------------------------------
# ENUM-LIKE Literals
# --------------------------------
BookingStatus = Literal["INCOMPLETE", "PAID", "CANCELLED"]
PaymentStatus = Literal["PENDING", "PAID", "FAILED"]
PassengerType = Literal["ADULT", "CHILD", "INFANT"]
FlightStatus = Literal["SCHEDULED", "DELAYED", "CANCELLED", "DEPARTED", "ARRIVED"]

# --------------------------------
# Custom Types
# --------------------------------
AirportCode = Annotated[str, Field(min_length=3, max_length=3)]
AirlineCode = Annotated[str, Field(min_length=2, max_length=3)]


# --------------------------------
# Airline Schema
# --------------------------------
class AirlineSchema(BaseModel):
    flight_code: AirlineCode
    flight_name: str
    flight_image: Optional[HttpUrl] = None


# --------------------------------
# Balance
# --------------------------------
class BalanceResponse(BaseModel):
    balance: int
    currency: str


# --------------------------------
# Code Area
# --------------------------------
class CodeAreaResponse(BaseModel):
    codes: List[Dict[str, str]]


# --------------------------------
# Flight Search Params
# --------------------------------
from typing import Literal, Optional


class FlightSearchParams(BaseModel):
    origin: AirportCode = Field(..., alias="flight_from")
    destination: AirportCode = Field(..., alias="flight_to")
    date: date
    airline: Optional[str] = None
    transit: Optional[str] = None
    baggage: Optional[str] = None
    flight_class: Optional[Literal["economy", "business", "first"]] = None
    sort_by: Optional[Literal["harga_tertinggi", "harga_terendah", "waktu_terbaik"]] = (
        None
    )
    page: int = 1
    per_page: int = 10

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%d-%m-%Y").date()
            except ValueError:
                raise ValueError("Date must be in format dd-mm-yyyy")
        return v

    model_config = {"validate_by_name": True}


# --------------------------------
# Flight Result Schema
# --------------------------------
class FlightResultSchema(BaseModel):
    flight_id: str
    flight: str
    flight_code: str
    flight_image: Optional[HttpUrl]
    flight_from: str
    flight_to: str
    flight_route: str
    flight_date: str  # yyyy-mm-dd
    flight_transit: Optional[str]
    flight_infotransit: Optional[str]
    flight_datetime: Optional[str]
    flight_price: str
    flight_publishfare: str
    flight_seatavail: str
    flight_baggage: Optional[str]
    flight_facilities: Optional[str]


# --------------------------------
# Flight Search Request (for body request)
# --------------------------------
class FlightSearchRequest(BaseModel):
    username: str
    password: str
    flight_from: AirportCode
    flight_to: AirportCode
    date: str
    airline: Optional[str] = None
    transit: Optional[str] = None
    baggage: Optional[str] = None
    flight_class: Optional[str] = None
    sort_by: Optional[str] = None
    page: Optional[int] = 1
    per_page: Optional[int] = 10


__all__ = [
    "BookingStatus",
    "PaymentStatus",
    "PassengerType",
    "FlightStatus",
    "AirportCode",
    "AirlineCode",
    "AirlineSchema",
    "BalanceResponse",
    "CodeAreaResponse",
    "FlightSearchParams",
    "FlightResultSchema",
]
