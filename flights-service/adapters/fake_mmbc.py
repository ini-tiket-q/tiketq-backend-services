from datetime import datetime
from adapters.store import BOOKING_STATUS

# Simple in-memory store to track payment status per kodebooking


class FakeMMBCClient:
    async def reset_password(self, **kwargs):
        return {"result": "ok", "message": "Reset simulated"}

    async def get_price(self, **kwargs):
        return {
            "result": "ok",
            "flight": "JT-792",
            "publish": 1250000,
            "tax": 150000,
            "totalfare": 1400000,
            "flight_shownta": 1360000,
            "flight_realnta": 1350000,
            "flight_availableseat": 5
        }

    async def post_booking(self, **kwargs):
        kode = "DEV123"
        BOOKING_STATUS[kode] = False  # Mark as unpaid
        return {"result": "ok", "kodebooking": kode, "reason": ""}

    async def get_issued(self, **kwargs):
        kode = kwargs.get("kodebooking")

        if kode in BOOKING_STATUS:
            if BOOKING_STATUS[kode] == "PAID":
                return {
                        "result": "ok",
                        "kodebooking": kode,
                        "flight": "JT-792",
                        "ticket_number": "ABC1234567",
                        "flight_statusbooking": "issued",
                        "issued_date": datetime.utcnow().isoformat(),
                        "reason": "https://mock-dev.com/etiket-ABC1234567.pdf"
                    }

            else:
                return {"result": "no", "reason": "Payment not completed"}

        return {"result": "no", "reason": "Booking not found"}


    async def get_status_booking(self, **kwargs):
        kode = kwargs.get("kodebooking")
        if kode in BOOKING_STATUS:
            return {
                "result": "ok",
                "flight_statusbooking": "issued" if BOOKING_STATUS[kode] == "PAID" else "waiting",
                "reason": ""
            }
        return {"result": "no", "reason": "Booking not found"}


    async def get_eticket(self, **kwargs):
        kode = kwargs.get("kodebooking")
        if BOOKING_STATUS.get(kode):
            return {
                "result": "ok",
                "reason": "link download etiket https://klikmbc.co.id/getbook/etiket/etiket-ABC1234567.pdf"
            }
        return {"result": "no", "reason": "E-ticket not available"}


    async def simulate_payment(self, **kwargs):
        kode = kwargs.get("kodebooking") or kwargs.get("order_id")
        if kode in BOOKING_STATUS:
            BOOKING_STATUS[kode] = True
            return {"result": "ok", "message": "Payment simulated"}
        return {"result": "no", "reason": "Booking not found"}
