import os
import requests


class MMBCClient:
    def __init__(self, base_url=None, user=None, password=None, agent=None, timeout: float = 15.0):
        self.base = base_url or os.getenv("MMBC_BASE_URL", "http://klikmbc.co.id/json")
        self.user = user or os.getenv("MMBC_USER_ID")
        self.password = password or os.getenv("MMBC_PASSWORD")
        self.agent = agent or os.getenv("MMBC_AGENT_CODE")
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "tiketq-flights-service/1.0",
        }

    def get_price(self, *, flight, from_, to, date, adult, child, infant):
        url = f"{self.base}/getprice-json"
        payload = {
            "username": "dummy",
            "password": "dummy123",
            "flight": flight,
            "from": from_,
            "to": to,
            "date": date,  # Must be dd-mm-yyyy
            "adult": str(adult),
            "child": str(child),
            "infant": str(infant),
        }

        print(f"📡 [MMBC] POST {url} | payload={payload}")

        try:
            r = requests.post(url, data=payload, headers=self.headers, timeout=self.timeout)
            print(f"🔁 Status: {r.status_code}")
            print(f"📄 Raw response: {r.text}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"❌ [MMBC] Error: {e}")
            return {"result": "no", "reason": "upstream error"}

    # The following endpoints still need async _post method, or migrate them to requests too
    def post_booking(self, **body: dict):
        url = f"{self.base}/postbooking-json"
        print(f"📡 [MMBC] POST {url} | payload={body}")

        try:
            r = requests.post(url, data=body, headers=self.headers, timeout=self.timeout)
            print(f"🔁 Status: {r.status_code}")
            print(f"📄 Raw response: {r.text}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"❌ [MMBC] Error: {e}")
            return {"result": "no", "reason": "upstream error"}



    def get_issued(self, *, kodebooking):
        return self._sync_post("/json/getissued-json", {"kodebooking": kodebooking})

    def get_status_booking(self, *, kodebooking):
        return self._sync_post("/json/getstatusbooking-json", {"kodebooking": kodebooking})

    def get_eticket(self, *, kodebooking):
        return self._sync_post("/json/getetiket-json", {"kodebooking": kodebooking})

    def _sync_post(self, path: str, payload: dict) -> dict:
        url = f"{self.base}{path}"
        try:
            r = requests.post(url, data=payload, headers=self.headers, timeout=self.timeout)
            print(f"📡 [MMBC] POST {url} | payload={payload}")
            print(f"🔁 Status: {r.status_code}")
            print(f"📄 Raw response: {r.text}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"❌ [MMBC] Error: {e}")
            return {"result": "no", "reason": "upstream error"}
