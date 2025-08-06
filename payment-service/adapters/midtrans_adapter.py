import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from midtransclient import CoreApi, Snap
from ..domain.models import (
    PaymentRequest, 
    PaymentResponse, 
    PaymentStatus, 
    PaymentMethod,
    PaymentNotification
)
from ..domain.repository import PaymentRepository


class MidtransAdapter(PaymentRepository):
    """
    Adapter implementation for Midtrans payment gateway.
    Implements the PaymentRepository interface (port).
    """
    
    def __init__(
        self, 
        server_key: str, 
        client_key: str, 
        is_production: bool = False
    ):
        """
        Initialize Midtrans adapter with API keys
        
        Args:
            server_key: Midtrans server key
            client_key: Midtrans client key
            is_production: Whether to use production environment
        """
        self.server_key = server_key
        self.client_key = client_key
        self.is_production = is_production
        
        self.core_api = CoreApi(
            is_production=is_production,
            server_key=server_key,
            client_key=client_key
        )
        
        self.snap = Snap(
            is_production=is_production,
            server_key=server_key,
            client_key=client_key
        )
    
    def _map_payment_method(self, payment_method: PaymentMethod) -> Dict[str, Any]:
        """
        Map our payment method enum to Midtrans payment types
        
        Args:
            payment_method: Our payment method enum
            
        Returns:
            Dict: Midtrans payment type configuration
        """
        if payment_method == PaymentMethod.CREDIT_CARD:
            return {"payment_type": "credit_card"}
        
        elif payment_method == PaymentMethod.BANK_TRANSFER:
            return {
                "payment_type": "bank_transfer",
                "bank_transfer": {"bank": "bca"}
            }
        
        elif payment_method == PaymentMethod.E_WALLET:
            return {
                "payment_type": "gopay"
            }
        
        elif payment_method == PaymentMethod.QRIS:
            return {
                "payment_type": "qris"
            }
        
        elif payment_method == PaymentMethod.RETAIL:
            return {
                "payment_type": "cstore",
                "cstore": {"store": "indomaret"}
            }
        
        else:
            return {}
    
    async def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Create a payment transaction with Midtrans
        
        Args:
            payment_request: Payment request details
            
        Returns:
            PaymentResponse: Response with transaction details
        """
        transaction_time = datetime.now()
        expiry_time = transaction_time + timedelta(hours=payment_request.expiry_duration)
        
        transaction_details = {
            "order_id": payment_request.order_id,
            "gross_amount": payment_request.amount
        }
        
        customer_details = {
            "first_name": payment_request.customer_name,
            "email": payment_request.customer_email,
            "phone": payment_request.customer_phone or ""
        }
        
        item_details = payment_request.items or [{
            "id": "default",
            "price": payment_request.amount,
            "quantity": 1,
            "name": payment_request.description or "Payment"
        }]
        
        payment_type_config = self._map_payment_method(payment_request.payment_method)
        
        transaction_data = {
            "transaction_details": transaction_details,
            "customer_details": customer_details,
            "item_details": item_details,
            "expiry": {
                "unit": "hour",
                "duration": payment_request.expiry_duration
            }
        }
        
        if payment_type_config:
            transaction_data.update(payment_type_config)
        
        try:
            response = self.snap.create_transaction(transaction_data)
            
            payment_id = response.get("transaction_id", "")
            token = response.get("token", "")
            redirect_url = response.get("redirect_url", "")
            payment_response = PaymentResponse(
                payment_id=payment_id,
                order_id=payment_request.order_id,
                status=PaymentStatus.PENDING,
                amount=payment_request.amount,
                payment_method=payment_request.payment_method,
                transaction_time=transaction_time,
                expiry_time=expiry_time,
                payment_url=f"https://app.midtrans.com/snap/v2/vtweb/{token}",
                token=token,
                redirect_url=redirect_url
            )
            
            return payment_response
            
        except Exception as e:
            raise ValueError(f"Failed to create payment: {str(e)}")
    
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """
        Get payment status from Midtrans
        
        Args:
            payment_id: Midtrans transaction ID
            
        Returns:
            PaymentStatus: Current payment status
        """
        try:
            response = self.core_api.transactions.status(payment_id)
            
            status_mapping = {
                "pending": PaymentStatus.PENDING,
                "capture": PaymentStatus.PROCESSING,
                "settlement": PaymentStatus.SUCCESS,
                "deny": PaymentStatus.FAILED,
                "cancel": PaymentStatus.CANCELED,
                "expire": PaymentStatus.EXPIRED,
                "refund": PaymentStatus.REFUNDED,
            }
            
            midtrans_status = response.get("transaction_status", "").lower()
            return status_mapping.get(midtrans_status, PaymentStatus.PENDING)
            
        except Exception as e:
            raise ValueError(f"Failed to get payment status: {str(e)}")
    
    async def cancel_payment(self, payment_id: str) -> PaymentResponse:
        """
        Cancel a payment with Midtrans
        
        Args:
            payment_id: Midtrans transaction ID
            
        Returns:
            PaymentResponse: Updated payment details
        """
        try:
            response = self.core_api.transactions.cancel(payment_id)
            
            order_id = response.get("order_id", "")
            status = PaymentStatus.CANCELED
            amount = float(response.get("gross_amount", 0))
            transaction_time = datetime.fromisoformat(response.get("transaction_time", "").replace("Z", "+00:00"))
            
            payment_response = PaymentResponse(
                payment_id=payment_id,
                order_id=order_id,
                status=status,
                amount=amount,
                payment_method=PaymentMethod.CREDIT_CARD,
                transaction_time=transaction_time
            )
            
            return payment_response
            
        except Exception as e:
            raise ValueError(f"Failed to cancel payment: {str(e)}")
    
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """
        Refund a payment with Midtrans
        
        Args:
            payment_id: Midtrans transaction ID
            amount: Amount to refund (if None, full refund)
            
        Returns:
            PaymentResponse: Updated payment details
        """
        try:
            if amount is None:
                transaction = self.core_api.transactions.status(payment_id)
                amount = float(transaction.get("gross_amount", 0))
            
            refund_params = {
                "refund_key": f"refund-{payment_id}-{datetime.now().timestamp()}",
                "amount": amount,
                "reason": "Customer requested refund"
            }
            
            response = self.core_api.transactions.refund(payment_id, refund_params)
            
            order_id = response.get("order_id", "")
            status = PaymentStatus.REFUNDED
            transaction_time = datetime.fromisoformat(response.get("transaction_time", "").replace("Z", "+00:00"))
            
            payment_response = PaymentResponse(
                payment_id=payment_id,
                order_id=order_id,
                status=status,
                amount=amount,
                payment_method=PaymentMethod.CREDIT_CARD,
                transaction_time=transaction_time
            )
            
            return payment_response
            
        except Exception as e:
            raise ValueError(f"Failed to refund payment: {str(e)}")
    
    async def handle_notification(self, notification_data: dict) -> PaymentNotification:
        """
        Process payment notification from Midtrans
        
        Args:
            notification_data: Raw notification data from Midtrans
            
        Returns:
            PaymentNotification: Processed notification
        """
        try:
            transaction_id = notification_data.get("transaction_id", "")
            order_id = notification_data.get("order_id", "")
            status_code = notification_data.get("transaction_status", "")
            status_message = notification_data.get("status_message", "")
            gross_amount = float(notification_data.get("gross_amount", 0))
            payment_type = notification_data.get("payment_type", "")
            transaction_time_str = notification_data.get("transaction_time", "")
            signature_key = notification_data.get("signature_key", "")
            
            transaction_time = datetime.fromisoformat(transaction_time_str.replace("Z", "+00:00")) if transaction_time_str else datetime.now()
            
            settlement_time_str = notification_data.get("settlement_time", "")
            settlement_time = datetime.fromisoformat(settlement_time_str.replace("Z", "+00:00")) if settlement_time_str else None
            
            fraud_status = notification_data.get("fraud_status", None)
            bank = notification_data.get("va_numbers", [{}])[0].get("bank", "") if notification_data.get("va_numbers") else None
            va_number = notification_data.get("va_numbers", [{}])[0].get("va_number", "") if notification_data.get("va_numbers") else None
            masked_card = notification_data.get("masked_card", None)
            
            notification = PaymentNotification(
                transaction_id=transaction_id,
                order_id=order_id,
                status_code=status_code,
                status_message=status_message,
                gross_amount=gross_amount,
                payment_type=payment_type,
                transaction_time=transaction_time,
                signature_key=signature_key,
                fraud_status=fraud_status,
                settlement_time=settlement_time,
                bank=bank,
                va_number=va_number,
                masked_card=masked_card
            )
            
            return notification
            
        except Exception as e:
            raise ValueError(f"Failed to process notification: {str(e)}")
