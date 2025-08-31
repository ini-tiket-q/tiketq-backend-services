import uuid
from domain.models import Passenger
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv


# In-memory store
mock_bookings = []


def get_mock_schedules():
    return [
        {
            "schedule_id": "SCH-001",
            "origin": "Tanjung Priok",
            "destination": "Pontianak",
            "departure_time": "2025-09-10T08:00:00",
            "arrival_time": "2025-09-10T20:00:00",
            "operator": "Pelni",
            "base_price": 170000,
            "currency": "IDR",
            "available_seats": 120,
            "metadata": {
                "ship_name": "KM Bukit Raya",
                "class": "Economy",
                "duration": "12h"
            }
        },
        {
            "schedule_id": "SCH-002",   # identik dengan SCH-001
            "origin": "Tanjung Priok",
            "destination": "Pontianak",
            "departure_time": "2025-09-10T08:00:00",
            "arrival_time": "2025-09-10T20:00:00",
            "operator": "Pelni",
            "base_price": 170000,
            "currency": "IDR",
            "available_seats": 120,
            "metadata": {
                "ship_name": "KM Bukit Raya",
                "class": "Economy",
                "duration": "12h"
            }
        },
        {
            "schedule_id": "SCH-003",
            "origin": "Surabaya",
            "destination": "Makassar",
            "departure_time": "2025-09-11T09:00:00",
            "arrival_time": "2025-09-11T19:00:00",
            "operator": "Pelni",
            "base_price": 200000,
            "currency": "IDR",
            "available_seats": 100,
            "metadata": {
                "ship_name": "KM Labobar",
                "class": "Business",
                "duration": "10h"
            }
        },
        {
            "schedule_id": "SCH-004",
            "origin": "Batam",
            "destination": "Singapore",
            "departure_time": "2025-09-12T07:00:00",
            "arrival_time": "2025-09-12T09:00:00",
            "operator": "Batam Fast",
            "base_price": 300000,
            "currency": "IDR",
            "available_seats": 50,
            "metadata": {
                "ship_name": "Batam Fast 8",
                "class": "VIP",
                "duration": "2h"
            }
        },
        {
            "schedule_id": "SCH-005",
            "origin": "Medan",
            "destination": "Penang",
            "departure_time": "2025-09-15T06:30:00",
            "arrival_time": "2025-09-15T11:30:00",
            "operator": "Pelni",
            "base_price": 250000,
            "currency": "IDR",
            "available_seats": 75,
            "metadata": {
                "ship_name": "KM Kelud",
                "class": "Economy",
                "duration": "5h"
            }
        }
    ]


def calculate_price(passengers: list[Passenger]) -> float:
    """
    Mock pricing rules:
    Adult = Rp170.000
    Child = Rp70.000
    """
    total = 0
    for p in passengers:
        if p.type.lower() == "adult":
            total += 170_000
        elif p.type.lower() == "child":
            total += 70_000
        else:
            total += 100_000  # default price jika tidak dikenali
    return total


def create_ferry_booking(schedule_id: str, passengers: list[Passenger]):
    booking_id = str(uuid.uuid4())
    subtotal = calculate_price(passengers)
    tax = 0
    discount = 0
    total = subtotal + tax - discount

    items = []
    for p in passengers:
        items.append({
            "name": f"Ferry {schedule_id}",
            "price": 170_000 if p.type.lower() == "adult" else 70_000,
            "quantity": 1,
            "description": f"{p.type} Passenger - {p.name}",
            "metadata": {
                "dob": str(p.dob),
                "passport_no": p.passport_no,
                "nationality": p.nationality,
            }
        })

    booking = {
        "booking_id": booking_id,
        "status": "incomplete",
        "subtotal": subtotal,
        "tax": tax,
        "discount": discount,
        "total": total,
        "items": items,
        "metadata": {
            "schedule_id": schedule_id,
            "passenger_count": len(passengers)
        }
    }

    mock_bookings.append(booking)
    return booking


def list_bookings():
    return mock_bookings