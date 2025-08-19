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
        return {"result": "ok", "kodebooking": "DEV123", "reason": ""}

    async def get_issued(self, kodebooking: str):
        return {
            "result": "no",
            "reason": "Payment not completed"
        }


    async def get_status_booking(self, kodebooking: str):
        return {
            "result": "ok",
            "flight_statusbooking": "PENDING",
            "reason": None
        }

    async def get_eticket(self, kodebooking: str):
        # Simulate a successful response with a fake PDF URL
        return {
            "result": "ok",
            "reason": "https://example.com/eticket/DEV123.pdf"
        }