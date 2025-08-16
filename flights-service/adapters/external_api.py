import os, json, httpx
import requests
from typing import Any, Dict, List

BASE    = os.getenv("MMBC_BASE_URL", "")
USER    = os.getenv("MMBC_USER_ID", "")
PWD     = os.getenv("MMBC_PASSWORD", "")
AGENT   = os.getenv("MMBC_AGENT_CODE", "")
TIMEOUT = float(os.getenv("MMBC_TIMEOUT_SECONDS", "15"))

class MmbcClient:
    def __init__(self, user: str | None = None, pwd: str | None = None):
        self.user = user or os.getenv("MMBC_USER", "")
        self.pwd = pwd or os.getenv("MMBC_PASSWORD", "")
        self.base = os.getenv("MMBC_BASE_URL", "http://mmbc.local")
        self._http = requests.Session()

    def search_schedules(self, frm: str, to: str, date_: str, pax: int, cabin: str | None) -> List[Dict[str, Any]]:
        payload = {
            "username": self.user,
            "password": self.pwd,
            "from": frm,
            "to": to,
            "date": date_,
            "adult": pax,
            "child": 0,
            "infant": 0,
        }
        r = self._http.post(f"{self.base}/json/getschedule-json", data=payload)
        r.raise_for_status()
        return r.json()

    def post_booking(self, form: dict):
        if os.getenv("MOCK_REMOTE", "false").lower() == "true":
            return {"status": "ok", "message": "Simulated MMBC booking", "booking_code": "MOCK123456"}

        payload = {
            "username": self.user,
            "password": self.pwd,
            **form
        }
        r = self._http.post(f"{self.base}/getbooking-json", data=payload)
        r.raise_for_status()
        return r.json()


    def _auth_payload(self) -> Dict[str, str]:
        return {"userId": self.user, "password": self.pwd, "agentCode": self.agent}

    # fallback airports and airlines
    def _fallback_airports(self):
        return {"status": "ok", "data": [
            {"code": "CGK", "city": "Jakarta"},
            {"code": "DPS", "city": "Denpasar"},
            {"code": "SUB", "city": "Surabaya"},
        ]}

    def _fallback_airlines(self):
        return {"status": "ok", "data": [
            {"flight_code": "QG", "flight_name": "Citilink", "flight_image": None},
            {"flight_code": "SJ", "flight_name": "Sriwijaya Air", "flight_image": None},
            {"flight_code": "IU", "flight_name": "Super Air Jet", "flight_image": None},
        ]}

    def get_code_area(self):
        try:
            r = self._http.get(f"{self.base}/json/getcodearea-json")
            r.raise_for_status()
            return r.json()
        except httpx.RequestError:
            return self._fallback_airports()

    def get_code_flights(self):
        try:
            r = self._http.get(f"{self.base}/json/getcodeflights-json")
            r.raise_for_status()
            return r.json()
        except httpx.RequestError:
            return self._fallback_airlines()

    def get_price(self, frm: str, to: str, date_ddmmyyyy: str, flight_code: str,
                  adult: int, child: int, infant: int):
        payload = {
            "username": self.user, "password": self.pwd,
            "from": frm, "to": to, "date": date_ddmmyyyy,
            "flight": flight_code, "adult": adult, "child": child, "infant": infant
        }
        r = self._http.post(f"{self.base}/json/getprice-json", data=payload)
        r.raise_for_status()
        return r.json()

    def issue(self, kodebooking: str):
        if os.getenv("MOCK_REMOTE", "false").lower() == "true":
            return {
                "status": "ok",
                "message": "Simulated issue success",
                "booking_code": kodebooking
            }

        payload = {
            "username": self.user,
            "password": self.pwd,
            "kodebooking": kodebooking
        }
        r = self._http.post(f"{self.base}/json/getissued-json", data=payload)
        r.raise_for_status()
        return r.json()

    def status_booking(self, kodebooking: str):
        payload = {"username": self.user, "password": self.pwd, "kodebooking": kodebooking}
        r = self._http.post(f"{self.base}/json/getstatusbooking-json", data=payload)
        r.raise_for_status()
        return r.json()

    def eticket_link(self, kodebooking: str):
        payload = {"username": self.user, "password": self.pwd, "kodebooking": kodebooking}
        r = self._http.post(f"{self.base}/json/getetiket-json", data=payload)
        r.raise_for_status()
        return r.json()
