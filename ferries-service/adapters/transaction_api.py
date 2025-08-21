# import os
# import requests

# TRANSACTION_URL = os.getenv("TRANSACTION_SERVICE_URL", "http://transaction-service:8000")

# def create_transaction(booking_id: str, amount: float):
#     """
#     Create transaction record in transaction-service
#     """
#     url = f"{TRANSACTION_URL}/transactions"
#     payload = {
#         "booking_id": booking_id,
#         "amount": amount,
#         "status": "pending"
#     }
#     res = requests.post(url, json=payload)
#     res.raise_for_status()
#     return res.json()

import uuid

def create_transaction(booking_id: str, amount: float):
    """
    Mock transaction-service
    """
    transaction_id = str(uuid.uuid4())
    return {
        "transaction_id": transaction_id,
        "booking_id": booking_id,
        "amount": amount,
        "status": "pending"
    }
