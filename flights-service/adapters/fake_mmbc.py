from datetime import datetime
from adapters.store import BOOKING_STATUS


from datetime import datetime

class FakeMMBCClient:
    async def reset_password(self, **kwargs):
        return {"result": "ok", "message": "Reset simulated"}

    async def get_price(self, **kwargs):
        return {
            "result": "ok",
            "flight": "Citilink",
            "flight_code": "QG-724",
            "flight_from": "CGK",
            "flight_to": "SUB",
            "flight_route": "CGK-SUB",
            "flight_date": "2025-09-01",
            "flight_departure": "01 Sep 2025 18:40",
            "flight_time": "18:40 - 20:20",
            "flight_class": "O",
            "flight_availableseat": "5",
            "flight_baggage": "20kg",
            "publish": 425000,
            "tax": 112500,
            "totalfare": 537500,
            "adult": "1",
            "child": "0",
            "infant": "0"
        }

    async def post_booking(self, **kwargs):
        kode = "CLNK456"
        return {
            "result": "ok",
            "tid": "555666777",
            "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight": "Citilink",
            "flight_code": "QG-890",
            "kodebooking": kode,
            "flight_route": "SUB-UPG",
            "flight_departure": "20 Feb 2026 14:30",
            "flight_time": "14:30 - 17:30",
            "flight_transit": "Nonstop",
            "flight_class": "M",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": (
                '[{"passenger_title":"Mr","passenger_fullname":"Adi Nugroho","passenger_type":"Adult"}]'
            ),
            "flight_contactdetails_json": (
                '{"contact_title":"Mr","contact_fullname":"Adi Nugroho","contact_email":"adi@example.com","contact_phone":"+628112223334"}'
            ),
            "flight_currency": "IDR",
            "flight_publishfare": "850000",
            "flight_tax": "150000",
            "flight_totalfare": "1000000",
            "flight_timelimit": "19 Feb 2026 23:59",
            "flight_bookingby": "agent789",
            "flight_bookingby_kodeagen": "AGT003",
            "flight_statusbooking": "waiting"
        }

    async def get_status_booking(self, **kwargs):
        kode = kwargs.get("kodebooking")
        return {
            "result": "ok",
            "tid": "555666777",
            "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight": "Citilink",
            "flight_code": "QG-890",
            "kodebooking": kode,
            "flight_route": "SUB-UPG",
            "flight_departure": "20 Feb 2026 14:30",
            "flight_time": "14:30 - 17:30",
            "flight_transit": "Nonstop",
            "flight_class": "M",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": (
                '[{"passenger_title":"Mr","passenger_fullname":"Adi Nugroho","passenger_type":"Adult"}]'
            ),
            "flight_contactdetails_json": (
                '{"contact_title":"Mr","contact_fullname":"Adi Nugroho","contact_email":"adi@example.com","contact_phone":"+628112223334"}'
            ),
            "flight_currency": "IDR",
            "flight_publishfare": "850000",
            "flight_tax": "150000",
            "flight_totalfare": "1000000",
            "flight_statusbooking": "waiting",
            "reason": ""   # ← REQUIRED BY YOUR SCHEMA
        }


    async def get_issued(self, **kwargs):
        kode = kwargs.get("kodebooking")
        return {
            "result": "ok",
            "tid": "555666777",
            "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight": "Citilink",
            "flight_code": "QG-890",
            "kodebooking": kode,
            "flight_route": "SUB-UPG",
            "flight_departure": "20 Feb 2026 14:30",
            "flight_time": "14:30 - 17:30",
            "flight_transit": "Nonstop",
            "flight_class": "M",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": (
                '[{"passenger_title":"Mr","passenger_fullname":"Adi Nugroho","passenger_type":"Adult"}]'
            ),
            "flight_contactdetails_json": (
                '{"contact_title":"Mr","contact_fullname":"Adi Nugroho","contact_email":"adi@example.com","contact_phone":"+628112223334"}'
            ),
            "flight_currency": "IDR",
            "flight_publishfare": "850000",
            "flight_tax": "150000",
            "flight_totalfare": "1000000",
            "flight_issued_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight_issued_ticketnumber": "ETKT555666777",
            "flight_issuedby": "MMBC System",
            "flight_issuedby_kodeagen": "AGT003",
            "flight_statusbooking": "issued",
            "reason": ""
        }

    async def get_eticket(self, **kwargs):
        kode = kwargs.get("kodebooking")
        return {
            "result": "ok",
            "reason": f"https://klikmbc.co.id/getbook/etiket/etiket-{kode}.pdf"
        }
