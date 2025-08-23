from typing import List
from domain.schemas_flights import (
    BalanceResponse,
    CodeAreaResponse,
    AirlineSchema,
    FlightSearchParams,
    FlightResultSchema,
)
from domain.repository_flights import FlightRepository


class FlightService:
    def __init__(self, repository: FlightRepository):
        self.repo = repository

    def validate_login(self, username: str, password: str) -> bool:
        """
        Validasi kredensial user berdasarkan balance > 0.
        """
        try:
            raw_balance = self.repo.check_balance(username, password)
            return raw_balance.get("balance", 0) > 0
        except Exception as e:
            print(f"❌ Login validation error: {e}")
            return False

    def check_balance(self, username: str, password: str) -> BalanceResponse:
        """
        Ambil saldo akun berdasarkan kredensial user.
        """
        raw = self.repo.check_balance(username, password)
        return BalanceResponse(**raw)

    async def get_code_area(self) -> CodeAreaResponse:
        """
        Ambil daftar kode area bandara dan nama kota.
        """
        data = await self.repo.get_code_area()
        return CodeAreaResponse(codes=data)

    async def get_code_flights(self) -> List[AirlineSchema]:
        """
        Ambil daftar maskapai (kode, nama, logo).
        """
        data = await self.repo.get_code_flights()
        return [AirlineSchema(**item) for item in data]


    async def get_flights(self, params: FlightSearchParams) -> List[FlightResultSchema]:
        """
        Cari penerbangan berdasarkan parameter.
        """

        raw_flights = await self.repo.get_flights(params.dict())

        # 🔍 Filter logic (same as yours)
        filtered = self.filter_flights(raw_flights, params)

        # 📄 Pagination logic
        start = (params.page - 1) * params.per_page
        end = start + params.per_page
        paginated = filtered[start:end]

        # 🧾 Return as schema list
        return [FlightResultSchema(**f) for f in paginated]


    
    def filter_flights(self, flights: list[dict], params: FlightSearchParams) -> list[dict]:
        result = flights

        if params.airline:
            result = [f for f in result if f["airline"].lower() == params.airline.lower()]

        if params.transit:
            result = [f for f in result if f["transit_type"].lower() == params.transit.lower()]

        if params.baggage:
            result = [f for f in result if f["baggage_option"].lower() == params.baggage.lower()]

        if params.flight_class:
            result = [f for f in result if f["class"].lower() == params.flight_class.lower()]

        if params.sort_by == "harga_tertinggi":
            result.sort(key=lambda x: x["price"], reverse=True)
        elif params.sort_by == "harga_terendah":
            result.sort(key=lambda x: x["price"])
        elif params.sort_by == "waktu_terbaik":
            result.sort(key=lambda x: x.get("score", 0), reverse=True)

        return result

