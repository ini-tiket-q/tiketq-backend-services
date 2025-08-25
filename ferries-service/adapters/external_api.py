import uuid
from domain.models import Passenger

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

    return {
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
