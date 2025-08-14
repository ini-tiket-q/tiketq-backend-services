import os, httpx
from typing import Any, Dict, List

BASE = os.getenv("MMBC_BASE_URL", "")
USER = os.getenv("MMBC_USER_ID", "")
PWD  = os.getenv("MMBC_PASSWORD", "")
AGENT= os.getenv("MMBC_AGENT_CODE", "")
TIMEOUT = float(os.getenv("MMBC_TIMEOUT_SECONDS", "15"))

class MmbcClient:
    def __init__(self):
        self._client = httpx.Client(timeout=TIMEOUT)

    def _auth_payload(self) -> Dict[str, str]:
        return {"userId": USER, "password": PWD, "agentCode": AGENT}

    def search_schedules(self, frm: str, to: str, date_: str, pax: int, cabin: str | None) -> List[Dict[str, Any]]:
        """
        Call provider search. For now return a stub so FE can integrate.
        Replace body with real HTTP call once the spec is finalized.
        """
        # Example real call (commented until spec is locked):
        # payload = {**self._auth_payload(), "from": frm, "to": to, "date": date_, "pax": pax, "cabin": cabin}
        # r = self._client.post(f"{BASE}/flights/search", json=payload)
        # r.raise_for_status()
        # raw = r.json()

        # ---- STUB result shaped like our FE needs ----
        return [{
            "provider": "MMBC",
            "flight_number": "TQ 123",
            "from_airport": frm.upper(),
            "to_airport": to.upper(),
            "departure_time": f"{date_}T09:00:00",
            "arrival_time":   f"{date_}T11:00:00",
            "airline": "Super Air Jet",
            "fare": {"currency": "IDR", "amount": 1050000},
            "class": cabin or "ECONOMY",
            "duration_minutes": 120,
            "direct": True,
        }]
