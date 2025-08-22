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

# In-memory store
mock_transactions = []

def create_transaction(booking_id: str, amount: float):
    """
    Mock transaction-service
    """
    transaction_id = str(uuid.uuid4())
    transaction = {
        "transaction_id": transaction_id,
        "booking_id": booking_id,
        "amount": amount,
        "status": "pending"
    }
    mock_transactions.append(transaction)
    return transaction

def list_transactions():
    """
    Return all mock transactions
    """
    return mock_transactions

def update_transaction_status(transaction_id: str, new_status: str):
    """
    Update transaction status by ID
    """
    for tx in mock_transactions:
        if tx["transaction_id"] == transaction_id:
            tx["status"] = new_status
            return tx
    return None