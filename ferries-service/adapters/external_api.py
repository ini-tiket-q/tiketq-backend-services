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
    total_price = calculate_price(passengers)

    return {
        "booking_id": booking_id,
        "status": "incomplete",
        "total_price": total_price
    }
