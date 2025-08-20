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

    def get_code_area(self) -> CodeAreaResponse:
        """
        Ambil daftar kode area bandara dan nama kota.
        """
        data = self.repo.get_code_area()
        return CodeAreaResponse(codes=data)

    def get_code_flights(self) -> List[AirlineSchema]:
        """
        Ambil daftar maskapai (kode, nama, logo).
        """
        data = self.repo.get_code_flights()
        return [AirlineSchema(**item) for item in data]

    def get_flights(self, params: FlightSearchParams) -> List[FlightResultSchema]:
        """
        Cari penerbangan berdasarkan parameter.
        """
        raw_flights = self.repo.get_flights(params.dict())
        return [FlightResultSchema(**flight) for flight in raw_flights]
