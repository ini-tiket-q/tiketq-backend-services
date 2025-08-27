import requests
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

AGENT_CODE = os.getenv("SINDO_AGENT_CODE", "T900T63")
USERNAME = os.getenv("SINDO_USERNAME", "testparistvl")
PASSWORD = os.getenv("SINDO_PASSWORD", "j&o99?Pm2#Uj")

LOGIN_URL = "https://api.test.sindoferry.com.sg/agent/Agent/Login"
ROUTES_URL = "https://api.test.sindoferry.com.sg/Agent/Master/Routes"


def login():
    payload = {
        "agentCode": AGENT_CODE,
        "username": USERNAME,
        "password": PASSWORD,
    }
    headers = {"Content-Type": "application/json"}

    resp = requests.post(LOGIN_URL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") == "Ok":
        token = data["data"]["access_token"]
        print("✅ Login sukses, token didapat.")
        return token
    else:
        raise Exception(f"Login gagal: {data}")


def get_routes(token: str, search: str = None):
    params = {
        "filter": f'{{"searchString":"{search}"}}' if search else '{"searchString":null}',
        "pagination": '{"pageIndex":0,"pageSize":0}'
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    resp = requests.get(ROUTES_URL, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    records = data["data"]["records"]
    df = pd.DataFrame(records)
    if not df.empty:
        print("📍 Routes ditemukan:")
        print(df[["code", "name"]])
    else:
        print("⚠️ Tidak ada route ditemukan.")


if __name__ == "__main__":
    try:
        token = login()
        get_routes(token)
    except Exception as e:
        print("❌ Error:", e)
