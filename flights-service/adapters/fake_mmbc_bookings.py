from datetime import datetime
from adapters.store import BOOKING_STATUS

class FakeMMBCClient:
    async def reset_password(self, **kwargs):
        return {"result": "ok", "message": "Reset simulated"}

    async def get_price(self, **kwargs):
        return {
            "result": "ok",
            "flight_id": "01",  # add this
            "flight": "Citilink",
            "flight_code": "QG-724",
            "flight_image": "https://klikmbc.biz/v2/images/airlines/icon_citilink.png",  # add this
            "flight_from": "CGK",
            "flight_to": "SUB",
            "flight_route": "CGK-SUB",
            "flight_date": "2025-09-01",
            "flight_transit": "Nonstop",  # add this
            "flight_infotransit": "Jakarta(CGK) 18:40 - Surabaya(SUB) 20:20",  # add this
            "flight_time": "18:40 - 20:20",
            "flight_duration": "1j 40mnt",  # add this
            "flight_class": "O",
            "flight_availableseat": "5",
            "flight_baggage": "20kg",
            "publish": 425000,
            "tax": 112500,
            "totalfare": 537500,
            "adult": 1,
            "child": 0,
            "infant": 0,
            "flight_shownta": 524750,   # optional
            "flight_realnta": 516250    # optional
        }


    async def post_booking(self, **kwargs):
        kode = "BTK159"
        return {         
        "result": "ok",
        "tid": "777888999",
        "tanggal": "2025-09-12 10:15:00",
        "flight": "Batik Air",
        "flight_code": "ID-7159",
        "kodebooking": "BTK159",
        "flight_route": "CGK-SIN",
        "flight_departure": "12 Sep 2025 17:50",
        "flight_time": "17:50 - 20:35",
        "flight_transit": "Nonstop",
        "flight_infotransit": "Jakarta(CGK) 17:50 - Singapore(SIN) 20:35",
        "flight_class": "Y",
        "flight_totalpassenger": "1",
        "flight_datapassengers_json": "[{\"passenger_title\":\"Mr\",\"passenger_fullname\":\"Jonathan Pratama\",\"passenger_type\":\"Adult\",\"passenger_baggageintl\":\"20 Kg\",\"passenger_ffnumber\":\"ID123456\",\"passenger_dob\":\"1990-08-21\",\"passenger_passportnumber\":\"A12345678\",\"passenger_passportexpired\":\"2030-08-21\"}]",
        "flight_contactdetails_json": "{\"contact_title\":\"Mr\",\"contact_fullname\":\"Jonathan Pratama\",\"contact_email\":\"jonathan@example.com\",\"contact_phone\":\"+628123987654\"}",
        "flight_currency": "IDR",
        "flight_publishfare": "1325100",
        "flight_tax": "230000",
        "flight_totalfare": "1555100",
        "flight_realnta": "1500000",
        "flight_shownta": "1515000",
        "flight_bonus_agen": "45100",
        "flight_timelimit": "12 Sep 2025 15:00",
        "flight_bookingby": "agent789",
        "flight_bookingby_kodeagen": "AGT005",
        "flight_issued_date": "",
        "flight_issued_ticketnumber": "",
        "flight_issuedby": "",
        "flight_issuedby_kodeagen": "",
        "flight_statusbooking": "waiting",
        "reason": ""
        }


    async def get_status_booking(self, **kwargs):
   
        kode = kwargs.get("kodebooking")

        # Default to waiting if never updated
        status = BOOKING_STATUS.get(kode, "waiting")

        return {
            "result": "ok",
            "tid": "777888999",
            "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight": "Batik Air",
            "flight_code": "ID-7159",
            "kodebooking": kode,
            "flight_route": "CGK-SIN",
            "flight_departure": "12 Sep 2025 17:50",
            "flight_time": "17:50 - 20:35",
            "flight_transit": "Nonstop",
            "flight_infotransit": "Jakarta(CGK) 17:50 - Singapore(SIN) 20:35",
            "flight_class": "Y",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": (
                '[{"passenger_title":"Mr","passenger_fullname":"Jonathan Pratama","passenger_type":"Adult",'
                '"passenger_baggageintl":"20 Kg","passenger_ffnumber":"ID123456","passenger_dob":"1990-08-21",'
                '"passenger_passportnumber":"A12345678","passenger_passportexpired":"2030-08-21"}]'
            ),
            "flight_contactdetails_json": (
                '{"contact_title":"Mr","contact_fullname":"Jonathan Pratama","contact_email":"jonathan@example.com",'
                '"contact_phone":"+628123987654"}'
            ),
            "flight_currency": "IDR",
            "flight_publishfare": "1325100",
            "flight_tax": "230000",
            "flight_totalfare": "1555100",
            "flight_issued_date": None if status == "waiting" else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight_issued_ticketnumber": None if status == "waiting" else "ETKT987654321",
            "flight_issuedby": None if status == "waiting" else "MMBC System",
            "flight_issuedby_kodeagen": None if status == "waiting" else "AGT005",
            "flight_statusbooking": status,
            "reason": ""
        }


    async def get_issued(self, **kwargs):
    
        kode = kwargs.get("kodebooking")

        # After issuing, mark status as "issued" in mock store
        BOOKING_STATUS[kode] = "issued"

        return {
            "result": "ok",
            "tid": "777888999",
            "tanggal": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight": "Batik Air",
            "flight_code": "ID-7159",
            "kodebooking": kode,
            "flight_route": "CGK-SIN",
            "flight_departure": "12 Sep 2025 17:50",
            "flight_time": "17:50 - 20:35",
            "flight_transit": "Nonstop",
            "flight_infotransit": "Jakarta(CGK) 17:50 - Singapore(SIN) 20:35",
            "flight_class": "Y",
            "flight_totalpassenger": "1",
            "flight_datapassengers_json": (
                '[{"passenger_title":"Mr","passenger_fullname":"Jonathan Pratama","passenger_type":"Adult",'
                '"passenger_baggageintl":"20 Kg","passenger_ffnumber":"ID123456","passenger_dob":"1990-08-21",'
                '"passenger_passportnumber":"A12345678","passenger_passportexpired":"2030-08-21"}]'
            ),
            "flight_contactdetails_json": (
                '{"contact_title":"Mr","contact_fullname":"Jonathan Pratama","contact_email":"jonathan@example.com",'
                '"contact_phone":"+628123987654"}'
            ),
            "flight_currency": "IDR",
            "flight_publishfare": "1325100",
            "flight_tax": "230000",
            "flight_totalfare": "1555100",
            "flight_issued_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "flight_issued_ticketnumber": "ETKT987654321",
            "flight_issuedby": "MMBC System",
            "flight_issuedby_kodeagen": "AGT005",
            "flight_statusbooking": "issued",
            "reason": ""
        }




    async def get_eticket(self, **kwargs):
        kode = kwargs.get("kodebooking")
        return {
            "result": "ok",
            "reason": f"https://klikmbc.co.id/getbook/etiket/etiket-{kode}.pdf"
        }
