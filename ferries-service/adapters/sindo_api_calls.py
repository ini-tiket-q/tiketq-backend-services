# Only responsible for raw HTTP calls
import json
import requests
from config import settings

_access_token = None  # cache sementara

class SindoClient:
    def __init__(self):
        self.base_url = settings.SINDO_BASE_URL
        self.core_url = settings.SINDO_CORE_URL
        self.agent_code = settings.SINDO_AGENT_CODE
        self.username = settings.SINDO_USERNAME
        self.password = settings.SINDO_PASSWORD
        self._access_token = None

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    # ---------------------------
    # Internal methods
    # ---------------------------
        
    def _login(self):
        url = f"{self.base_url}/Agent/Login"
        payload = {
            "agentCode": self.agent_code,
            "username": self.username,
            "password": self.password,
        }
        resp = self.session.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "Ok":
            self._access_token = data["data"]["access_token"]
            # update session headers dengan token
            self.session.headers.update({
                "Authorization": f"Bearer {self._access_token}"
                })
            return self._access_token
        raise Exception(f"Login gagal: {data}")


    def _ensure_token(self):
        if not self._access_token:
            self._login()
    
    
    def _request(self, method, url, **kwargs):
        """Wrapper request dengan auto relogin jika 401"""
        self._ensure_token()
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == 401:
            # token expired → login ulang sekali
            self.login()  
            # ulang request
            resp = self.session.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # ---------------------------
    # Public API methods
    # ---------------------------

    def get_sindo_routes(self, search: str = None, page_index=0, page_size=0):
        """Get list of Sindo routes"""
        params = {
            "filter": (
                f'{{"searchString":"{search}"}}' if search else '{"searchString":null}'
            ),
            "pagination": f'{{"pageIndex":{page_index},"pageSize":{page_size}}}'
        }
        url = f"{self.base_url}/Route"
        return self._request("GET", url, params=params)

    #oneway
    def get_sindo_trips(self, origin: str, destination: str, date: str):
        """Get trips/schedules (general API)"""
        self._ensure_token()
        url = f"{self.core_url}/Trips/GetTripWeb"

        params = {
            "embarkation": origin,      # ex: BTC
            "destination": destination, # ex: HFC
            "tripdate": date            # format: YYYY-MM-DD
        }

        resp = self.session.get(url, params=params, timeout=15)
        if resp.status_code == 401:
            self._login()
            resp = self.session.get(url, params=params, timeout=15)

        resp.raise_for_status()
        return resp.json()

    #roundtrip
    def get_sindo_roundtrip(
        self, 
        origin: str, 
        destination: str, 
        depart_date: str, 
        return_date: str, 
        pax: int=1
    ):
        self._ensure_token()
        url = f"{self.base_url}/Trips/GetRoundTripWeb"
        resp = self.session.get(url, params=params, timeout=15)
        if resp.status_code == 401:
            self._login()
            resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
