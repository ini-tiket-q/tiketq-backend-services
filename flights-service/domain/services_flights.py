from typing import List, Optional
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

    def get_flights(
        self,
        params: FlightSearchParams,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> List[FlightResultSchema]:
        """
        Ambil data penerbangan dari MMBC jika username & password diberikan.
        Kalau tidak ada kredensial, return list kosong.
        """
        flights_data = []

        if username and password:
            raw_data = self.repo.get_flights(
                origin=params.origin,
                destination=params.destination,
                date=params.date.strftime("%d-%m-%Y"),
                username=username,
                password=password,
            )
            flights_data = raw_data or []
        else:
            print("⚠️ Username/password not provided. Skipping MMBC fetch.")

        # Filter dan paginate
        filtered = self.filter_flights(flights_data, params)
        start = (params.page - 1) * params.per_page
        end = start + params.per_page
        paginated = filtered[start:end]

        return [FlightResultSchema(**f) for f in paginated]

    def filter_flights(
        self, flights: List[dict], params: FlightSearchParams
    ) -> List[dict]:
        result = flights

        if params.airline:
            result = [
                f
                for f in result
                if f.get("flight", "").lower() == params.airline.lower()
            ]

        if params.transit:
            result = [
                f
                for f in result
                if f.get("flight_transit", "").lower() == params.transit.lower()
            ]

        if params.baggage:
            result = [
                f
                for f in result
                if f.get("flight_baggage", "").lower() == params.baggage.lower()
            ]

        if params.flight_class:
            result = [
                f
                for f in result
                if f.get("class", "").lower() == params.flight_class.lower()
            ]

        if params.sort_by == "harga_tertinggi":
            result.sort(key=lambda x: int(x.get("flight_price", "0")), reverse=True)
        elif params.sort_by == "harga_terendah":
            result.sort(key=lambda x: int(x.get("flight_price", "0")))
        elif params.sort_by == "waktu_terbaik":
            result.sort(key=lambda x: x.get("score", 0), reverse=True)

        return result
