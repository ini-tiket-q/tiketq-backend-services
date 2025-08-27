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





# # ======================
# # BOOKING
# # ======================
# def create_sindo_booking(schedule_id: str, passengers: list[Passenger], requirements: dict):
#     """
#     Create booking ke Sindo Ferry
#     - passengers: list of Passenger (pydantic model)
#     - requirements: BookingRequirements dict
#     """
#     url = f"{SINDO_CORE_URL}/Order/Booking"

#     payload = {
#         "scheduleId": schedule_id,
#         "passengers": [p.dict() for p in passengers],
#         "contact": requirements
#     }

#     resp = requests.post(url, headers=_get_headers(), json=payload)
#     resp.raise_for_status()
#     return resp.json()


