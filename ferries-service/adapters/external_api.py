import os
from typing import Optional
import requests
import json
from adapters.ext_api_config import settings

_access_token = None  # cache sementara


class SindoClient:
    def __init__(self):
        self.base_url = settings.SINDO_BASE_URL
        self.core_url = settings.SINDO_CORE_URL
        self.agent_url = settings.SINDO_AGENT_URL
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
    # def _build_url(self, endpoint: str) -> str:
    #     """Build full URL from endpoint using string formatting"""
    #     return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    def _build_filter_param(self, search: Optional[str] = None) -> str:
        """Build filter parameter using string formatting"""
        if search:
            return f'{{"searchString":"{search}"}}'
        return '{"searchString":null}'
    
    def _build_pagination_param(self, page_index: int = 0, page_size: int = 0) -> str:
        """Build pagination parameter using string formatting"""
        return f'{{"pageIndex":{page_index},"pageSize":{page_size}}}'


# Agen Login (Mandatory)
    def _login(self):
        url = f"{self.base_url}/Agent/Login"
        payload = {
            "agentCode": self.agent_code,
            "username": self.username,
            "password": self.password,
        }
        
        # Temporary session without auth token for login
        # Prevents infinite retry loops during failed login attempts
        with requests.Session() as temp_session:
            resp = temp_session.post(url, json=payload, timeout=10)
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

    def _request(self, method, endpoint, use_core_url=False, **kwargs):
        """Wrapper for requests with automatic token refresh"""
        
        base_url = self.core_url if use_core_url else self.base_url
                
        url = f"{base_url}{endpoint}"
            
        print(f"DEBUG: Making request to URL: {url}") 
        try:    
            self._ensure_token()
            resp = self.session.request(method, url, **kwargs)          
                
            if resp.status_code == 401:
                print("Token expired, attempting to refresh...")
                # token expired → login ulang sekali
                self._login()  
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


    def get_sindo_routes(self, search: str=None, page_index: int=0, page_size: int=0):
        """Get list of Sindo routes"""
        params = {
            "filter": self._build_filter_param(search),
            "pagination": self._build_pagination_param(page_index, page_size)
        }
        return self._request("GET", "/Master/Routes", params=params)


    def get_sindo_trips(self, origin: str, destination: str, date: str):
        """Get trips/schedules (general API)"""
        # formatted_date = date.replace("-", "")
        params = {
            "embarkation": origin,      # ex: BTC
            "destination": destination, # ex: HFC
            "tripdate": date   # format: YYYY-MM-DD
        }
        return self._request("GET", "/Trips/GetTripWeb", use_core_url=True, params=params) 

    
    def create_sindo_booking(self, booking_data: dict):
        """Create a new booking"""
        return self._request("POST", "/Booking/Bookings", json=booking_data)

   
    def add_sindo_booking_detail(self, booking_id: str, passenger_data: dict):
        """Add passenger details to a booking"""
        return self._request("POST", f"/Booking/Bookings/{booking_id}/Details", json=passenger_data)

    
    def get_sindo_booking_details(self, booking_id: str, search: str = None):
        """Get details of a specific booking"""
        params = {
            "filter": json.dumps({
                "searchString": search if search else None,
                "sort": 2  # Name ASC
            }),
            "pagination": json.dumps({
                "pageIndex": 0,
                "pageSize": 0
            })
        }
        return self._request("GET", f"/Booking/Bookings/{booking_id}/Details", params=params)
        
    
    def get_sindo_countries(self, search: str = None):
        """Get list of countries"""
        params = {
            "filter": json.dumps({
                "searchString": search if search else None,
                "sort": 0
            }),
            "pagination": json.dumps({
                "pageIndex": 0,
                "pageSize": 0
            })
        }
        return self._request("GET", "/Master/Countries", params=params)
    
    
    def delete_sindo_booking_detail(self, booking_id: str, booking_detail_id: str):
        """Delete a booking detail (passenger) from a booking"""
        return self._request("DELETE", f"/Booking/Bookings/{booking_id}/Details/{booking_detail_id}")


    def sindo_submit_booking(self, booking_id: str, email_confirmation: str, remarks: str):
        """Submit a booking for final processing"""
        payload = {
            "id": booking_id,
            "emailConfirmation": email_confirmation,
            "remarks": remarks
        }
        return self._request("POST", "/Booking/Bookings/Submit", json=payload)

    # get available sectors
    def get_sindo_available_sectors(self):
        """Get available ferry sectors"""
        return self._request("GET", "/Booking/Sectors/Available")
    
   
   
    def get_booking_type_pricings(self, search: str = None):
        """
        Ambil daftar Booking Type Pricings dari Sindo API.
        """
        params = {
            "filter": json.dumps({
                "searchString": search if search else None,
                "sort": 0,
                "currentActive": True
            }),
            "pagination": json.dumps({
                "pageIndex": 0,
                "pageSize": 0
            })
        }
        return self._request("GET", "/Booking/BookingTypePricings", params=params)
