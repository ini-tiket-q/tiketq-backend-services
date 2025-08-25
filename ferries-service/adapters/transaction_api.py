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
        "status": "incomplete"
    }
    mock_transactions.append(transaction)
    return transaction

def list_transactions():
    """
    Return all mock transactions
    """
    return mock_transactions

def update_transaction_status(transaction_id: str, status: str):
    """
    Update transaction status by ID
    """
    for tx in mock_transactions:
        if tx["transaction_id"] == transaction_id:
            if status not in ["incomplete", "paid", "failed", "cancelled"]:
                raise ValueError("Invalid transaction status")
            tx["status"] = status
            return tx
    return None