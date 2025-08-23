from datetime import datetime
from adapters.store import BOOKING_STATUS


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
            "flight_transit": "Nonstop",
            "flight_infotransit": "Jakarta(CGK) 18:40 - Surabaya(SUB) 20:20",
            "flight_time": "18:40 - 20:20",
            "flight_class": "O",
            "flight_availableseat": 5,
            "flight_baggage": "20kg",
            "flight_facilities": "-",
            "publish": 425000,
            "tax": 112500,
            "totalfare": 537500,
            "adult": "1",
            "child": "0",
            "infant": "0",
            "flight_shownta": 524750,
            "flight_realnta": 516250
        }

    async def post_booking(self, **kwargs):
        kode = "DEV123"
        BOOKING_STATUS[kode] = "INCOMPLETE"
        return {
            "result": "ok",
            "tid": "123456789",
            "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight": "Lion Air",
            "flight_code": "JT-792",
            "kodebooking": kode,
            "flight_route": "CGK-GTO",
            "flight_departure": "02 Jan 2026 01:00",
            "flight_time": "05:00 - 10:35",
            "flight_transit": "1 Stop",
            "flight_infotransit": "Jakarta(CGK) 05:00 - Gorontalo(GTO) 10:35",
            "flight_class": "Q",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": "[{\"passenger_title\":\"Mr\",\"passenger_fullname\":\"John Doe\",\"passenger_type\":\"Adult\"}]",
            "flight_contactdetails_json": "{\"contact_title\":\"Mr\",\"contact_fullname\":\"John Doe\",\"contact_email\":\"john@example.com\",\"contact_phone\":\"+628123456789\"}",
            "flight_currency": "IDR",
            "flight_publishfare": "960000",
            "flight_tax": "166000",
            "flight_totalfare": "1126000",
            "flight_realnta": "1097400",
            "flight_shownta": "1108840",
            "flight_bonus_agen": "17160",
            "flight_timelimit": "01 Jan 2026 10:00",
            "flight_bookingby": "agent123",
            "flight_bookingby_kodeagen": "AGT001",
            "flight_issued_date": "",
            "flight_issued_ticketnumber": "",
            "flight_issuedby": "",
            "flight_issuedby_kodeagen": "",
            "flight_statusbooking": "waiting",
            "reason":""
        }

    async def get_issued(self, **kwargs):
        kode = kwargs.get("kodebooking")
        if kode in BOOKING_STATUS:
            if BOOKING_STATUS[kode] == "PAID":
                return {
                    "result": "ok",
                    "tid": "123456789",
                    "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "flight": "Lion Air",
                    "flight_code": "JT-792",
                    "kodebooking": kode,
                    "flight_route": "CGK-GTO",
                    "flight_departure": "02 Jan 2026 01:00",
                    "flight_time": "05:00 - 10:35",
                    "flight_transit": "1 Stop",
                    "flight_infotransit": "Jakarta(CGK) 05:00 - Gorontalo(GTO) 10:35",
                    "flight_class": "Q",
                    "flight_totalpassenger": "1",
                    "flight_datapassengers_json": "[{\"passenger_title\":\"Mr\",\"passenger_fullname\":\"John Doe\",\"passenger_type\":\"Adult\"}]",
                    "flight_contactdetails_json": "{\"contact_title\":\"Mr\",\"contact_fullname\":\"John Doe\",\"contact_email\":\"john@example.com\",\"contact_phone\":\"+628123456789\"}",
                    "flight_currency": "IDR",
                    "flight_publishfare": "960000",
                    "flight_tax": "166000",
                    "flight_totalfare": "1126000",
                    "flight_realnta": "1097400",
                    "flight_shownta": "1108840",
                    "flight_bonus_agen": "17160",
                    "flight_timelimit": "01 Jan 2026 10:00",
                    "flight_bookingby": "agent123",
                    "flight_bookingby_kodeagen": "AGT001",
                    "flight_issued_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "flight_issued_ticketnumber": "ABC1234567",
                    "flight_issuedby": "MMBC System",
                    "flight_issuedby_kodeagen": "AGT001",
                    "flight_statusbooking": "issued",
                    "reason":""
                }
            else:
                return {"result": "no", "reason": "Sisa saldo tidak cukup untuk Issued tiket, sisa saldo anda adalah 0."}
        return {"result": "no", "reason": "Kode Booking tidak ditemukan, silakan periksa kembali kode bookingnya."}

    async def get_status_booking(self, **kwargs):
        kode = kwargs.get("kodebooking")
        if kode in BOOKING_STATUS:
            return {
                "result": "ok",
                "tid": "123456789",
                "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "flight": "Lion Air",
                "flight_code": "JT-792",
                "kodebooking": kode,
                "flight_route": "CGK-GTO",
                "flight_departure": "02 Jan 2026 01:00",
                "flight_time": "05:00 - 10:35",
                "flight_transit": "1 Stop",
                "flight_infotransit": "Jakarta(CGK) 05:00 - Gorontalo(GTO) 10:35",
                "flight_class": "Q",
                "flight_totalpassenger": "1",
                "flight_datapassengers_json": "[{\"passenger_title\":\"Mr\",\"passenger_fullname\":\"John Doe\",\"passenger_type\":\"Adult\"}]",
                "flight_contactdetails_json": "{\"contact_title\":\"Mr\",\"contact_fullname\":\"John Doe\",\"contact_email\":\"john@example.com\",\"contact_phone\":\"+628123456789\"}",
                "flight_currency": "IDR",
                "flight_publishfare": "960000",
                "flight_tax": "166000",
                "flight_totalfare": "1126000",
                "flight_realnta": "1097400",
                "flight_shownta": "1108840",
                "flight_bonus_agen": "17160",
                "flight_timelimit": "01 Jan 2026 10:00",
                "flight_bookingby": "agent123",
                "flight_bookingby_kodeagen": "AGT001",
                "flight_issued_date": "",
                "flight_issued_ticketnumber": "",
                "flight_issuedby": "",
                "flight_issuedby_kodeagen": "",
                "flight_statusbooking": "issued" if BOOKING_STATUS[kode] == "PAID" else "waiting",
                "reason":""
            }
        return {"result": "no", "reason": "Invalid Kode Booking XXXXX!"}

    async def get_eticket(self, **kwargs):
        kode = kwargs.get("kodebooking")
        if BOOKING_STATUS.get(kode) == "PAID":
            return {
                "result": "ok",
                "reason": "https://klikmbc.co.id/getbook/etiket/etiket-ABC1234567.pdf"
            }
        return {"result": "no", "reason": "Invalid Kode Booking XXXXX!"}

    async def simulate_payment(self, **kwargs):
        kode = kwargs.get("kodebooking") or kwargs.get("order_id")
        if kode in BOOKING_STATUS:
            BOOKING_STATUS[kode] = "PAID"
            return {"result": "ok", "message": "Payment simulated"}
        return {"result": "no", "reason": "Kode Booking tidak ditemukan"}
