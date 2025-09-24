import os
import httpx
import asyncio

class MMBCClient:
    def __init__(self, base_url=None, username=None, user=None, password=None, agent=None, timeout: float = 15.0):
        self.base = base_url or os.getenv("MMBC_BASE_URL", "http://klikmbc.co.id/json")
        self.username = username or os.getenv("MMBC_USERNAME")
        self.user = user or os.getenv("MMBC_USER_ID")
        self.password = password or os.getenv("MMBC_PASSWORD")
        self.agent = agent or os.getenv("MMBC_AGENT_CODE")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def _post(self, endpoint: str, payload: dict):
        # Default credentials from env
        base_payload = {
            "username": self.username,
            "password": self.password,
        }

        # Let incoming payload (e.g. from Postman) override defaults
        merged = {**base_payload, **payload}
        if "username" in payload:
            merged["username"] = payload["username"]
        if "password" in payload:
            merged["password"] = payload["password"]

        url = f"{self.base}/{endpoint}"
        print(f"[MMBC] POST {url} | payload={merged}")

        resp = await self._client.post(url, data=merged)

        print(f"[MMBC] Status Code: {resp.status_code}")
        print(f"[MMBC] Raw Response: {resp.text}")

        try:
            data = resp.json()
        except Exception:
            raise Exception(f"Non-JSON response from MMBC: {resp.text}")

        if data.get("result") == "ok":
            print(f"[MMBC] Parsed JSON: {data}")
            return data

        resp.raise_for_status()
        return data





    # === Example endpoints ===

    async def get_price(self, flight: str, from_: str, to: str, date: str, adult: int, child: int, infant: int):
        payload = {
            "flight": flight,
            "from": from_,
            "to": to,
            "date": date,
            "adult": str(adult),
            "child": str(child),
            "infant": str(infant),
        }
        return await self._post("getprice-json", payload)

    async def post_booking(self, **kwargs):
        return await self._post("postbooking-json", kwargs)

    async def get_status_booking(self, **kwargs):
        return await self._post("getstatusbooking-json", kwargs)

    async def get_issued(self, **kwargs):
        return await self._post("getissued-json", kwargs)

    async def get_eticket(self, **kwargs):
        return await self._post("getetiket-json", kwargs)

    async def reset_password(self, **kwargs):
        return await self._post("resetpassword", kwargs)

    async def close(self):
        await self._client.aclose()
