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
        (Temporarily using mock data for filtering + pagination test)
        """

        mock_data = [
        {
            "flight_id": "1",
            "flight": "Lion Air",
            "flight_code": "JT-101",
            "flight_image": "https://example.com/logo.png",
            "flight_from": "CGK",
            "flight_to": "SUB",
            "flight_route": "CGK-SUB",
            "flight_date": "22-08-2025",
            "flight_transit": "Direct",
            "flight_infotransit": "-",
            "flight_datetime": "2025-08-22 06:00:00",
            "flight_price": "900000",
            "flight_publishfare": "1000000",
            "flight_seatavail": "10",
            "flight_baggage": "20kg",
            "flight_facilities": "Meal, Wifi",
            "airline": "Lion Air",
            "transit_type": "Direct",
            "baggage_option": "20kg",
            "class": "Economy",
            "price": 900000,
            "score": 80,
        },
        {
            "flight_id": "2",
            "flight": "Garuda",
            "flight_code": "GA-202",
            "flight_image": "https://example.com/logo2.png",
            "flight_from": "CGK",
            "flight_to": "SUB",
            "flight_route": "CGK-SUB",
            "flight_date": "22-08-2025",
            "flight_transit": "Transit",
            "flight_infotransit": "Transit in DPS",
            "flight_datetime": "2025-08-22 08:00:00",
            "flight_price": "1500000",
            "flight_publishfare": "1700000",
            "flight_seatavail": "5",
            "flight_baggage": "25kg",
            "flight_facilities": "Meal, Lounge",
            "airline": "Garuda",
            "transit_type": "Transit",
            "baggage_option": "25kg",
            "class": "Business",
            "price": 1500000,
            "score": 95,
        }
    ]


        #raw_flights = self.repo.get_flights(params.dict())


    # 🔍 Apply filters
        filtered = self.filter_flights(mock_data, params)

        # 📄 Apply pagination
        start = (params.page - 1) * params.per_page
        end = start + params.per_page
        paginated = filtered[start:end]

        # ✅ Return in schema
        return [FlightResultSchema(**flight) for flight in paginated]


    
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

