import os
import requests
from dotenv import load_dotenv

load_dotenv()

SINDO_BASE_URL = "https://api.test.sindoferry.com.sg/agent"
# SINDO_CORE_URL = "https://core.test.sindoferry.com.sg/api"
SINDO_CORE_URL = "https://api.test.sindoferry.com.sg/Agent"

AGENT_CODE = os.getenv("SINDO_AGENT_CODE", "T900T63")
USERNAME = os.getenv("SINDO_USERNAME", "testparistvl")
PASSWORD = os.getenv("SINDO_PASSWORD", "j&o99?Pm2#Uj")

_access_token = None  # cache sementara


def sindo_login():
    global _access_token
    url = f"{SINDO_BASE_URL}/Agent/Login"
    payload = {
        "agentCode": AGENT_CODE,   # lowercase seperti test_sindo
        "username": USERNAME,
        "password": PASSWORD
    }
    headers = {"Content-Type": "application/json"}

    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") == "Ok":
        _access_token = data["data"]["access_token"]
        return _access_token
    raise Exception(f"Login gagal: {data}")


def get_sindo_routes(search: str = None):
    global _access_token
    if not _access_token:
        sindo_login()

    # url = f"{SINDO_CORE_URL}/Master/Routes"
    url = f"https://api.test.sindoferry.com.sg/Agent/Master/Routes"
    params = {
        "filter": f'{{"searchString":"{search}"}}' if search else '{"searchString":null}',
        "pagination": '{"pageIndex":0,"pageSize":0}'
    }
    headers = {
        "Authorization": f"Bearer {_access_token}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers, params=params, timeout=10)

    if resp.status_code == 401:
        # token expired → relogin
        sindo_login()
        headers["Authorization"] = f"Bearer {_access_token}"
        resp = requests.get(url, headers=headers, params=params, timeout=10)

    resp.raise_for_status()
    return resp.json()


def get_sindo_trips(origin: str, destination: str, date: str):
    

    # url = f"{SINDO_CORE_URL}/Trips/GetTripWeb"
    url = "https://core.test.sindoferry.com.sg/api/Trips/GetTripWeb"

    params = {
        "embarkation": origin,      # ex: BTC
        "destination": destination, # ex: HFC
        "tripdate": date          # format: YYYY-MM-DD
    }

    headers = {
        
        "Content-Type": "application/json"
    }

    resp = requests.get(url, headers=headers, params=params, timeout=15)

    if resp.status_code == 401:
        sindo_login()
        
        resp = requests.get(url, headers=headers, params=params, timeout=15)

    resp.raise_for_status()
    return resp.json()


def create_sindo_booking(booking_data: dict):
    global _access_token
    if not _access_token:
        sindo_login()

    url = "https://api.test.sindoferry.com.sg/Agent/Booking/Bookings"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_access_token}"
    }

    resp = requests.post(url, headers=headers, json=booking_data, timeout=15)

    if resp.status_code == 401:
        sindo_login()
        headers["Authorization"] = f"Bearer {_access_token}"
        resp = requests.post(url, headers=headers, json=booking_data, timeout=15)

    resp.raise_for_status()
    return resp.json()


def add_sindo_booking_detail(booking_id: str, passenger_data: dict):
    global _access_token
    if not _access_token:
        sindo_login()

    url = f"https://api.test.sindoferry.com.sg/Agent/Booking/Bookings/{booking_id}/Details"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_access_token}"
    }

    resp = requests.post(url, headers=headers, json=passenger_data, timeout=15)

    if resp.status_code == 401:
        sindo_login()
        headers["Authorization"] = f"Bearer {_access_token}"
        resp = requests.post(url, headers=headers, json=passenger_data, timeout=15)

    resp.raise_for_status()
    return resp.json()

