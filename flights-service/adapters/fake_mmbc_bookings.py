from datetime import datetime
from adapters.store import BOOKING_STATUS

class FakeMMBCClient:
    async def reset_password(self, **kwargs):
        return {"result": "ok", "message": "Reset simulated"}

    async def get_price(self, **kwargs):
        return {
            "result": "ok",
            "flight_id": "02",
            "flight": "Singapore Airlines",
            "flight_code": "SQ-953",
            "flight_image": "https://klikmbc.biz/v2/images/airlines/singapore.png",
            "flight_from": "CGK",
            "flight_to": "SIN",
            "flight_route": "CGK-SIN",
            "flight_date": "2025-09-15",
            "flight_transit": "Nonstop",
            "flight_infotransit": "Jakarta(CGK) 11:00 - Singapore(SIN) 13:45",
            "flight_time": "11:00 - 13:45",
            "flight_duration": "2j 45mnt",
            "flight_class": "M",
            "flight_availableseat": "7",
            "flight_baggage": "25kg",
            "publish": 2250000,
            "tax": 350000,
            "totalfare": 2600000,
            "adult": 1,
            "child": 0,
            "infant": 0,
            "flight_shownta": 2570000,
            "flight_realnta": 2550000
        }


    async def post_booking(self, **kwargs):
        kode = "SIA888"
        return {
            "result": "ok",
            "tid": "888777666",
            "tanggal": "2025-09-15 09:30:00",
            "flight": "Singapore Airlines",
            "flight_code": "SQ-953",
            "kodebooking": kode,
            "flight_route": "CGK-SIN",
            "flight_departure": "15 Sep 2025 11:00",
            "flight_time": "11:00 - 13:45",
            "flight_transit": "Nonstop",
            "flight_infotransit": "Jakarta(CGK) 11:00 - Singapore(SIN) 13:45",
            "flight_class": "M",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": (
                '[{"passenger_title":"Ms","passenger_fullname":"Alicia Tan","passenger_type":"Adult",'
                '"passenger_baggageintl":"25 Kg","passenger_ffnumber":"SQ998877","passenger_dob":"1995-03-14",'
                '"passenger_passportnumber":"E98765432","passenger_passportexpired":"2031-03-14"}]'
            ),
            "flight_contactdetails_json": (
                '{"contact_title":"Ms","contact_fullname":"Alicia Tan","contact_email":"alicia@example.com",'
                '"contact_phone":"+628129998877"}'
            ),
            "flight_currency": "IDR",
            "flight_publishfare": "2250000",
            "flight_tax": "350000",
            "flight_totalfare": "2600000",
            "flight_realnta": "2550000",
            "flight_shownta": "2570000",
            "flight_bonus_agen": "50000",
            "flight_timelimit": "15 Sep 2025 09:45",
            "flight_bookingby": "agent123",
            "flight_bookingby_kodeagen": "AGT009",
            "flight_issued_date": "",
            "flight_issued_ticketnumber": "",
            "flight_issuedby": "",
            "flight_issuedby_kodeagen": "",
            "flight_statusbooking": "waiting",
            "reason": ""
        }


    async def get_status_booking(self, **kwargs):
        from datetime import datetime
        kode = kwargs.get("kodebooking")

        # Default to waiting if never updated
        status = BOOKING_STATUS.get(kode, "waiting")

        return {
            "result": "ok",
            "tid": "888777666",
            "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight": "Singapore Airlines",
            "flight_code": "SQ-953",
            "kodebooking": kode,
            "flight_route": "CGK-SIN",
            "flight_departure": "15 Sep 2025 11:00",
            "flight_time": "11:00 - 13:45",
            "flight_transit": "Nonstop",
            "flight_infotransit": "Jakarta(CGK) 11:00 - Singapore(SIN) 13:45",
            "flight_class": "M",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": (
                '[{"passenger_title":"Ms","passenger_fullname":"Alicia Tan","passenger_type":"Adult",'
                '"passenger_baggageintl":"25 Kg","passenger_ffnumber":"SQ998877","passenger_dob":"1995-03-14",'
                '"passenger_passportnumber":"E98765432","passenger_passportexpired":"2031-03-14"}]'
            ),
            "flight_contactdetails_json": (
                '{"contact_title":"Ms","contact_fullname":"Alicia Tan","contact_email":"alicia@example.com",'
                '"contact_phone":"+628129998877"}'
            ),
            "flight_currency": "IDR",
            "flight_publishfare": "2250000",
            "flight_tax": "350000",
            "flight_totalfare": "2600000",
            "flight_issued_date": None if status == "waiting" else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight_issued_ticketnumber": None if status == "waiting" else "ETKT123456789",
            "flight_issuedby": None if status == "waiting" else "MMBC System",
            "flight_issuedby_kodeagen": None if status == "waiting" else "AGT009",
            "flight_statusbooking": status,
            "reason": ""
        }


    async def get_issued(self, **kwargs):
        from datetime import datetime
        kode = kwargs.get("kodebooking")

        # After issuing, mark status as "issued" in mock store
        BOOKING_STATUS[kode] = "issued"

        return {
            "result": "ok",
            "tid": "888777666",
            "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight": "Singapore Airlines",
            "flight_code": "SQ-953",
            "kodebooking": kode,
            "flight_route": "CGK-SIN",
            "flight_departure": "15 Sep 2025 11:00",
            "flight_time": "11:00 - 13:45",
            "flight_transit": "Nonstop",
            "flight_infotransit": "Jakarta(CGK) 11:00 - Singapore(SIN) 13:45",
            "flight_class": "M",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": (
                '[{"passenger_title":"Ms","passenger_fullname":"Alicia Tan","passenger_type":"Adult",'
                '"passenger_baggageintl":"25 Kg","passenger_ffnumber":"SQ998877","passenger_dob":"1995-03-14",'
                '"passenger_passportnumber":"E98765432","passenger_passportexpired":"2031-03-14"}]'
            ),
            "flight_contactdetails_json": (
                '{"contact_title":"Ms","contact_fullname":"Alicia Tan","contact_email":"alicia@example.com",'
                '"contact_phone":"+628129998877"}'
            ),
            "flight_currency": "IDR",
            "flight_publishfare": "2250000",
            "flight_tax": "350000",
            "flight_totalfare": "2600000",
            "flight_issued_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight_issued_ticketnumber": "ETKT123456789",
            "flight_issuedby": "MMBC System",
            "flight_issuedby_kodeagen": "AGT009",
            "flight_statusbooking": "issued",
            "reason": ""
        }




    async def get_eticket(self, **kwargs):
            kode = kwargs.get("kodebooking")
            return {
                "result": "ok",
                "reason": f"https://klikmbc.co.id/getbook/etiket/etiket-{kode}.pdf"
            }
