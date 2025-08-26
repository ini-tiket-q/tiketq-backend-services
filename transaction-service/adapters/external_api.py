# wrappers around 3rd-party APIs
import requests
from fastapi import HTTPException
import os

def get_user_info(user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    # Load auth service URL
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    response = requests.get(f"{AUTH_SERVICE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data
    else:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")