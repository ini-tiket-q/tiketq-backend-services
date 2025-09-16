from typing import List, Dict, Any, Optional
from adapters.external_api_flights import ExternalFlightAPI


class FlightRepository:
    def __init__(self, api: ExternalFlightAPI):
        self.api = api

    def check_balance(self, username: str, password: str) -> Dict[str, Any]:
        return self.api.check_balance(username, password)

    def get_code_area(self) -> List[Dict[str, str]]:
        return self.api.get_code_area()

    def get_code_flights(self) -> List[Dict[str, str]]:
        return self.api.get_code_flights()

    def get_flights(
        self,
        origin: str,
        destination: str,
        date: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        payload = {
            "from": origin,
            "to": destination,
            "date": date,
        }

        # Tambahkan username/password hanya jika tersedia
        if username and password:
            payload["username"] = username
            payload["password"] = password

        return self.api.search_flights(payload)
