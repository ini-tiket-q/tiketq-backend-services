import asyncio
from typing import List, Dict, Any
from adapters.external_api import MMBCClient


class FlightRepository:
    def __init__(self, api: MMBCClient):
        self.api = api

    def check_balance(self, username: str, password: str) -> Dict[str, Any]:
        """
        Mengambil saldo user dari external API.
        """
        return self.api.check_balance(username, password)

    async def get_code_area(self) -> List[Dict[str, str]]:
        """
        Mengambil daftar kode area bandara dan kota.
        """
        return await self.api.get_code_area()

    async def get_code_flights(self) -> List[Dict[str, str]]:
        """
        Mengambil daftar maskapai.
        """
        return await self.api.get_code_flights()

    async def get_flights(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Mencari penerbangan berdasarkan parameter yang diberikan.
        """
        return await self.api.get_flights(
            from_=params["origin"],
            to=params["destination"],
            date=params["date"],
        )