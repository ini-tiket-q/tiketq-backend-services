from typing import Dict, List, Any


class ExternalFlightAPI:
    def check_balance(self, username: str, password: str) -> Dict[str, Any]:
        """
        Mock check balance.
        Gantikan dengan pemanggilan API eksternal atau DB sesungguhnya.
        """
        if username == "feri" and password == "password123":
            return {"balance": 99999, "currency": "IDR"}
        return {"balance": 0, "currency": "IDR"}

    def get_code_area(self) -> List[Dict[str, str]]:
        """
        Mock data kode bandara dan kota.
        """
        return [
            {"code": "CGK", "city": "Jakarta"},
            {"code": "SUB", "city": "Surabaya"},
            {"code": "DPS", "city": "Denpasar"},
        ]
    
    def get_code_flights(self) -> List[Dict[str, str]]:
        """
        Mock data kode dan nama maskapai serta logo.
        """
        return [
            {
                "flight_code": "A3",
                "flight_name": "Aegean Airlines",
                "flight_image": "https://da8hvrloj7e7d.cloudfront.net/imageResource/sample.png",
            },
            {
                "flight_code": "GA",
                "flight_name": "Garuda Indonesia",
                "flight_image": "https://example.com/garuda.png",
            },
        ]

    def search_flights(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Mock pencarian penerbangan.
        Param `params` bisa berisi origin, destination, date, dll.
        """
        # Contoh static hasil, sesuaikan dengan params jika perlu
        return [
            {
                "flight_id": "05",
                "flight": "Citilink",
                "flight_code": "QG-724",
                "flight_image": "https://.../citilink.png",
                "flight_from": "CGK",
                "flight_to": "SUB",
                "flight_route": "CGK-SUB",
                "flight_date": "2025-08-30",
                "flight_transit": "Nonstop",
                "flight_infotransit": "Jakarta(CGK) 18:40 - Surabaya(SUB) 20:20",
                "flight_datetime": "18:40 - 20:20",
                "flight_price": "537500",
                "flight_publishfare": "425000",
                "flight_seatavail": "7",
                "flight_baggage": "20 Kg",
                "flight_facilities": "Meal, In-flight entertainment",
            }
        ]
