from typing import Dict, Any, Optional
from datetime import datetime
from domain.models import PaymentRequest
from .models import MidtransMapper


class PayloadBuilder:
    """Builds payloads for various Midtrans API requests"""

    @staticmethod
    def build_snap_transaction_payload(payment_request: PaymentRequest) -> Dict[str, Any]:
        """Build payload for Snap transaction creation"""
        # Basic transaction details
        payload = {
            "transaction_details": {
                "order_id": payment_request.order_id,
                "gross_amount": int(payment_request.amount)
            },
            "customer_details": payment_request.customer_details,
            "item_details": payment_request.item_details
        }

        # Add expiry if specified
        if payment_request.expiry_duration:
            payload["expiry"] = {
                "unit": "hour",
                "duration": payment_request.expiry_duration
            }

        # Add payment method configuration
        payment_config = MidtransMapper.map_payment_method_to_config(payment_request.payment_method)
        payload.update(payment_config)

        return payload

    @staticmethod
    def build_refund_payload(transaction_id: str, amount: float, reason: Optional[str] = None) -> Dict[str, Any]:
        """Build payload for refund request"""
        return {
            "refund_key": f"refund-{transaction_id}-{int(datetime.now().timestamp())}",
            "amount": int(amount),
            "reason": reason or "Customer requested refund"
        }

    @staticmethod
    def validate_payment_request(payment_request: PaymentRequest) -> None:
        """Validate payment request before processing"""
        if not payment_request.order_id:
            raise ValueError("Order ID is required")
        if not payment_request.amount or payment_request.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        if not payment_request.customer_details:
            raise ValueError("Customer details are required")
        if not payment_request.item_details:
            raise ValueError("Item details are required")