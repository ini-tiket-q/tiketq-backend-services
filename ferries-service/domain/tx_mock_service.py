
import uuid
from datetime import datetime, timedelta

async def create_mock_transaction(transaction_data: dict) -> dict:
    """
    Mock implementation for transaction service
    """
    # Validate required fields (simulate what the real service would do)
    required_fields = ["order_id", "amount", "payment_method", "customer_details", "item_details"]
    for field in required_fields:
        if field not in transaction_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Return mock response in the format expected from the transaction service
    return {
        "transaction_id": str(uuid.uuid4()),
        "order_id": transaction_data["order_id"],
        "status": "PENDING",
        "payment_url": f"https://payment-gateway.com/pay/mock-{uuid.uuid4().hex[:8]}",
        "expiry_time": (datetime.now() + timedelta(hours=24)).isoformat()
    }