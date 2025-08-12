from datetime import datetime, timedelta
from adapters.persistence import get_session, SqlAlchemyFlightRepo
from domain.models import Flight
from domain.services import create_flight

def main():
    # open a session and repo
    session = get_session()
    repo = SqlAlchemyFlightRepo(session)

    base = datetime(2025, 8, 15, 9, 0)
    seeds = []
    for i in range(1, 26):  # 25 flights
        dep = base + timedelta(hours=i)
        arr = dep + timedelta(hours=2)
        seeds.append(
            Flight(
                id=None,
                flight_number=f"TQ {100 + i}",
                from_airport="CGK",
                to_airport=("SIN" if i % 2 == 0 else "KUL"),
                departure_time=dep,
                arrival_time=arr,
                aircraft_type=("A320" if i % 3 else "B737"),
                gate=None, terminal=None,
                status="SCHEDULED",
                notes=None,
            )
        )

    created, skipped = 0, 0
    for f in seeds:
        try:
            create_flight(repo, f)  # your service enforces the duplicate rule
            created += 1
        except ValueError:
            # "Duplicate flight for number+departure_time" -> skip
            skipped += 1

    print(f"Seed complete. Created={created}, Skipped(existing)={skipped}")

if __name__ == "__main__":
    main()
