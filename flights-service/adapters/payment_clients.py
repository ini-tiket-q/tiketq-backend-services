# adapters/payment_client.py

import httpx

PAYMENT_SERVICE_URL = "http://payment-service:8000/payments/"

async def create_payment(payment_payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            PAYMENT_SERVICE_URL,
            json=payment_payload,
            timeout=10
        )
        response.raise_for_status()  # raises exception on 4xx/5xx
        return response.json()
