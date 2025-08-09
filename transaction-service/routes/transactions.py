# routes/transactions.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

# Placeholder imports for models and authentication
from ..domain import models

router = APIRouter()

# Dummy user dependency
def get_current_user():
    # Replace with real authentication logic
    return {"id": 1, "role": "user"}  # or "admin"

# Dummy transaction model
class Transaction:
    def __init__(self, id, user_id, amount):
        self.id = id
        self.user_id = user_id
        self.amount = amount

# Dummy data
transactions_db = [
    Transaction(1, 1, 100),
    Transaction(2, 2, 200),
    Transaction(3, 1, 300),
]

@router.get("/transactions/", response_model=List[dict])
def get_transactions(user=Depends(get_current_user)):
    if user["role"] == "admin":
        # Admin sees all transactions
        return [t.__dict__ for t in transactions_db]
    else:
        # User sees only their own transactions
        return [t.__dict__ for t in transactions_db if t.user_id == user["id"]]
