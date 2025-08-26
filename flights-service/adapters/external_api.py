import httpx, json

class MMBCClient:
    def __init__(self, base_url: str, user: str, password: str, agent: str, timeout: float = 15.0):
        self.base = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.agent = agent
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "tiketq-flights-service/1.0",
        }

    async def _post(self, path: str, payload: dict) -> dict:
        body = {
            "username": self.user,
            "password": self.password,
            **payload
        }
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, verify=False) as client:
            r = await client.post(f"{self.base}{path}", data=body)
            text = r.text.strip()

            try:
                return r.json()
            except Exception:
                # 🔥 Detect 404 with HTML response from MMBC
                if r.status_code == 404 and "<html>" in text:
                    return {
                        "result": "no",
                        "reason": f"Invalid Kode Booking {payload.get('kodebooking', 'UNKNOWN')}!",
                    }

                raise RuntimeError(f"Upstream non-JSON (status {r.status_code}, len {len(text)}): {text[:200]}")



    async def reset_password(self, *, username, email, phone, agencode, newpassword):
        return await self._post("/json/resetpassword", {
            "username": username, "email": email, "phone": phone,
            "agencode": agencode, "newpassword": newpassword
        })

    async def get_price(self, *, flight, from_, to, date, adult, child, infant):
        return await self._post("/json/getprice-json", {
            "flight": flight, "from": from_, "to": to, "date": date,
            "adult": adult, "child": child, "infant": infant
        })

    async def post_booking(self, **body):
        return await self._post("/json/postbooking-json", body)

    async def get_issued(self, *, kodebooking):
        return await self._post("/json/getissued-json", {"kodebooking": kodebooking})

    async def get_status_booking(self, *, kodebooking):
        return await self._post("/json/getstatusbooking-json", {"kodebooking": kodebooking})
    
    async def get_eticket(self, *, kodebooking):
        return await self._post("/json/getetiket-json", {"kodebooking": kodebooking})

