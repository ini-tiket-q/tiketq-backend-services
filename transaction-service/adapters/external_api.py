# wrappers around 3rd-party APIs
import requests
from fastapi import HTTPException
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

def get_user_info(user_token):
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        # Load auth service URL
        AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
        logger.info(f"Auth service URL: {AUTH_SERVICE_URL}")
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/me", headers=headers)
        logger.info(f"Auth response: {response.json()}")
        if response.status_code == 200:
            user_data = response.json()
            return user_data
        else:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    except Exception as e:
        logger.error(f"Error getting user info in external API: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user info")


def create_payment_url(payment_body):
    try:
        PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
        logger.info(f"Payment service URL: {PAYMENT_SERVICE_URL}")
        response = requests.post(f"{PAYMENT_SERVICE_URL}/payments", json=payment_body)
        logger.info(f"Payment response: {response.json()} and status code: {response.status_code}")
        if response.status_code == 201:
            payment_data = response.json()
            return payment_data
        else:
            raise HTTPException(status_code=500, detail="Failed to create payment")

    except Exception as e:
        logger.error(f"Error creating payment in external API: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create payment")