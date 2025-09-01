import os
import requests
from typing import Dict, List, Any


class ExternalFlightAPI:
    def __init__(self):
        self.base_url = os.getenv("MMBC_BASE_URL")
        self.user_id = os.getenv("MMBC_USER_ID")
        self.password = os.getenv("MMBC_PASSWORD")
        self.agent_code = os.getenv("MMBC_AGENT_CODE")
        self.timeout = int(os.getenv("MMBC_TIMEOUT_SECONDS", 15))

        self.default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/116.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/html",
            "Referer": "http://klikmbc.co.id/",
        }

    def check_balance(self, username: str, password: str) -> Dict[str, Any]:
        """
        Mengambil saldo user dari external API.
        """
        try:
            url = f"{self.base_url}/ceksaldo"
            payload = {
                "username": username,
                "password": password,
                "agent": self.agent_code,
                "userid": self.user_id,
                "pin": self.password,
            }

            print(f"🔁 [MMBC] POST {url} | payload={payload}")
            response = requests.post(
                url,
                data=payload,
                headers={
                    **self.default_headers,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=self.timeout,
            )

            print(f"🔎 [MMBC] Status Code: {response.status_code}")
            print(f"📄 [MMBC] Raw Response: {response.text}")

            response.raise_for_status()

            try:
                data = response.json()
                print(f"✅ [MMBC] Parsed JSON: {data}")
            except ValueError as json_error:
                print(f"❌ [MMBC] Failed to parse JSON: {json_error}")
                return {"balance": 0, "currency": "IDR"}

            if data.get("result") == "ok":
                balance = int(data.get("saldo", "0").replace(",", "").replace(".", ""))
                return {"balance": balance, "currency": "IDR"}
            else:
                return {"balance": 0, "currency": "IDR"}

        except Exception as e:
            print(f"❌ [MMBC] Error during check_balance: {e}")
            return {"balance": 0, "currency": "IDR"}

    def get_code_area(self) -> List[Dict[str, str]]:
        try:
            url = f"{self.base_url}/getcodearea-json"
            print(f"🌍 [MMBC] GET {url}")
            response = requests.get(
                url, headers=self.default_headers, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ [MMBC] Error in get_code_area: {e}")
            return []

    def get_code_flights(self) -> List[Dict[str, str]]:
        try:
            url = f"{self.base_url}/getcodeflights-json"
            print(f"✈️ [MMBC] GET {url}")

            response = requests.get(
                url, headers=self.default_headers, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            # print(f"✅ [MMBC] Flights JSON received: {data}")
            print(f"✅ [MMBC] Flights JSON received: OK")
            return data
        except Exception as e:
            print(f"❌ [MMBC] Error in get_code_flights: {e}")
            return []

    def search_flights(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Panggil POST /getflights-json dengan form data:
        username, password, from, to, date (dd-mm-yyyy)

        params harus minimal punya key:
            - username
            - password
            - from
            - to
            - date (format dd-mm-yyyy)

        Return list of flights dict atau list kosong jika gagal.
        """
        url = f"{self.base_url}/getflights-json"

        required_keys = ["username", "password", "from", "to", "date"]
        if not all(k in params for k in required_keys):
            print(
                f"❌ [MMBC] Missing required params for search_flights. Got: {params}"
            )
            return []

        payload = {
            "username": params["username"],
            "password": params["password"],
            "from": params["from"],
            "to": params["to"],
            "date": params["date"],
        }

        try:
            print(f"✈️ [MMBC] POST {url} with data {payload}")
            response = requests.post(
                url,
                data=payload,
                headers={
                    **self.default_headers,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            # print(f"✅ [MMBC] Response data: {data}")

            if isinstance(data, dict) and data.get("result") == "no":
                print(f"⚠️ [MMBC] Search flights failed: {data.get('reason')}")
                return []

            if isinstance(data, list):
                return data

            print(f"⚠️ [MMBC] Unexpected response format: {data}")
            return []

        except Exception as e:
            print(f"❌ [MMBC] Exception in search_flights: {e}")
            return []
