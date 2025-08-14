# adapters/external_api.py
from typing import List, Optional
from datetime import datetime, timedelta
from domain.models import FerryRoute, FerrySchedule

class ExternalFerryAPIClient:
    """
    Mock client untuk data ferry. Nanti bisa diganti real API.
    """
    def _mock_routes(self) -> List[FerryRoute]:
        return [
            FerryRoute(id="R1", origin="Tanjung Priok", destination="Pontianak", operator="Pelni"),
            FerryRoute(id="R2", origin="Surabaya", destination="Makassar", operator="Pelni"),
            FerryRoute(id="R3", origin="Batam", destination="Belawan", operator="ASDP"),
        ]

    def _mock_schedules(self, route_id: str, start: datetime) -> List[FerrySchedule]:
        base = start.replace(hour=8, minute=0, second=0, microsecond=0)
        schedules = []
        for i in range(3):
            depart = base + timedelta(days=i)
            arrive = depart + timedelta(hours=20)
            schedules.append(
                FerrySchedule(
                    id=f"S{route_id}{i+1}",
                    route_id=route_id,
                    vessel=f"Kapal {i+1}",
                    depart_time=depart,
                    arrive_time=arrive,
                    price=350_000 + (i * 25_000),
                )
            )
        return schedules

    def search_routes(self, origin: Optional[str], destination: Optional[str]) -> List[FerryRoute]:
        routes = self._mock_routes()
        if origin:
            routes = [r for r in routes if r.origin.lower().startswith(origin.lower())]
        if destination:
            routes = [r for r in routes if r.destination.lower().startswith(destination.lower())]
        return routes

    def get_schedules(self, route_id: str, when: datetime) -> List[FerrySchedule]:
        if not any(r.id == route_id for r in self._mock_routes()):
            return []
        return self._mock_schedules(route_id, when)
