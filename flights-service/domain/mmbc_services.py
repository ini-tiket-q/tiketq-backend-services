import httpx
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path('.') / ".env")
MOCK_REMOTE = os.getenv("MOCK_REMOTE", "false").lower() == "true"
MMBC_BASE_URL = os.getenv("MMBC_BASE_URL")
print(f"MMBC_BASE_URL = {MMBC_BASE_URL}")
MMBC_USER_ID = os.getenv("MMBC_USER_ID")
MMBC_PASSWORD = os.getenv("MMBC_PASSWORD")
MMBC_AGENT_CODE = os.getenv("MMBC_AGENT_CODE")
MMBC_TIMEOUT = int(os.getenv("MMBC_TIMEOUT_SECONDS", 15))



class MMBCService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=MMBC_TIMEOUT)

    async def get_price(self, **payload):
        url = f"{MMBC_BASE_URL}/post"
        return await self._post(url, payload)

    async def post_booking(self, **payload):
        url = f"{MMBC_BASE_URL}/post"
        return await self._post(url, payload)

    async def get_issued(self, kodebooking: str):
        url = f"{MMBC_BASE_URL}/post"
        return await self._post(url, {"kodebooking": kodebooking})

    async def get_status_booking(self, kodebooking: str):
        url = f"{MMBC_BASE_URL}/post"
        return await self._post(url, {"kodebooking": kodebooking})

    async def reset_password(self, username, email, phone, agencode, newpassword):
        url = f"{MMBC_BASE_URL}/post"
        return await self._post(url, {
            "username": username,
            "email": email,
            "phone": phone,
            "agencode": agencode,
            "newpassword": newpassword
        })

    async def _post(self, url, data):
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"result": "no", "reason": str(e)}

    async def get_eticket(self, kodebooking: str):
        url = f"{MMBC_BASE_URL}/getetiket-json"
        payload = {
            "username": MMBC_USER_ID,
            "password": MMBC_PASSWORD,
            "kodebooking": kodebooking
        }
        return await self._post(url, payload)
    


# export
if MOCK_REMOTE:
    from adapters.fake_mmbc_bookings import FakeMMBCClient
    mmbc = FakeMMBCClient()
else:
    mmbc = MMBCService()



print("MMBC_BASE_URL =", MMBC_BASE_URL)
