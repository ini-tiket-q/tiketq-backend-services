from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel


### Ferry & FerryClass ###
class FerryClassBase(BaseModel):
    class_name: str
    seat_capacity: int
    price_base: float


class FerryClassCreate(FerryClassBase):
    ferry_id: int


class FerryClassRead(FerryClassBase):
    id: int
    ferry_id: int

    class Config:
        from_attributes = True


class FerryBase(BaseModel):
    ferry_name: str
    ferry_number: str
    capacity: int
    operator_name: str


class FerryCreate(FerryBase):
    pass


class FerryRead(FerryBase):
    id: int
    classes: List[FerryClassRead] = []

    class Config:
        from_attributes = True
