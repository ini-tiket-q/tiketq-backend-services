from typing import List, Dict, Any
from adapters.external_api_flights import ExternalFlightAPI


class FlightRepository:
    def __init__(self, api: ExternalFlightAPI):
        self.api = api

    def check_balance(self, username: str, password: str) -> Dict[str, Any]:
        """
        Mengambil saldo user dari external API.
        """
        return self.api.check_balance(username, password)

    def get_code_area(self) -> List[Dict[str, str]]:
        """
        Mengambil daftar kode area bandara dan kota.
        """
        return self.api.get_code_area()

    def get_code_flights(self) -> List[Dict[str, str]]:
        """
        Mengambil daftar maskapai.
        """
        return self.api.get_code_flights()

    def get_flights(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Mencari penerbangan berdasarkan parameter yang diberikan.
        """
        return self.api.search_flights(params)
