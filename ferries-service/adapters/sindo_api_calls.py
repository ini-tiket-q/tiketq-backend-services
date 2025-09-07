# Only responsible for raw HTTP calls
import json
import requests
from config.settings import settings

_access_token = None  # cache sementara

class SindoClient:
    def __init__(self):
        self.agent_url = settings.SINDO_AGENT_URL
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
        url = f"{self.agent_url}/Agent/Login"
        payload = {
            "agentCode": self.agent_code,
            "username": self.username,
            "password": self.password,
        }
        resp = self.session.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        print(f"Login response: {data}")  # Debug print
        print(f"Token received: {self._access_token}")
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
    
    
    def test_login(self):
        try:
            token = self._login()
            print(f"Login successful, token: {token}")
            return True
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False
    
    
    def _request(self, method, url, **kwargs):
        """Wrapper request dengan auto relogin jika 401"""
        try:    
            self._ensure_token()
            resp = self.session.request(method, url, **kwargs)
            
            # If unauthorized, try to refresh token once
            if resp.status_code == 401:
                print("Token expired, attempting to refresh...")
                # token expired → login ulang sekali
                self.login()  
                # ulang request
                resp = self.session.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Request failed: {str(e)}")
            print(f"URL: {url}")
            print(f"Method: {method}")
            if 'resp' in locals():
                print(f"Status Code: {resp.status_code}")
                print(f"Response Text: {resp.text}")
            raise
      
      
        

    # ---------------------------
    # Public API methods
    # ---------------------------

    def get_sindo_routes(self, search: str = None, page_index=0, page_size=0):
        """Get list of Sindo routes"""
        params = {}
        #     "filter": (
        #         f'{{"searchString":"{search}"}}' if search else '{"searchString":null}'
        #     ),
        #     "pagination": f'{{"pageIndex":{page_index},"pageSize":{page_size}}}'
        # }
        if search:
            params["searchString"] = search
        if page_index:
            params["pageIndex"] = page_index
        if page_size:
            params["pageSize"] = page_size
        
        url = f"{self.agent_url}/Agent/Master/Routes"
        print(f"Making request to: {url} with params: {params}")  # Debug
        return self._request("GET", url, params=params)


    #oneway
    def get_sindo_trips(self, origin: str, destination: str, date: str):
        """Get trips/schedules (general API)"""
        self._ensure_token()
        url = f"{self.core_url}/api/Trips/GetTripWeb"

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


