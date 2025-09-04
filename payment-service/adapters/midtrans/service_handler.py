import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from domain.models import (
    PaymentRequest, PaymentResponse, PaymentStatus, PaymentMethod,
    PaymentNotification
)

from .client import MidtransClient
from .models import MidtransMapper
from .payloads import PayloadBuilder
from .exceptions import (
    MidtransAPIException, MidtransValidationException, MidtransTransactionException
)

logger = logging.getLogger(__name__)


class MidtransServiceHandler:
    """Handles all Midtrans operations in one place"""

    def __init__(self, client: MidtransClient):
        self.client = client
        self.mapper = MidtransMapper()
        self.payload_builder = PayloadBuilder()

    async def create_payment_transaction(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Create a new payment transaction"""
        try:
            # Validate request
            self.payload_builder.validate_payment_request(payment_request)

            # Build payload
            payload = self.payload_builder.build_snap_transaction_payload(payment_request)

            # Create transaction
            transaction_time = datetime.now()
            result = self.client.create_transaction(payload)

            # Calculate expiry time (now in minutes)
            expiry_time = None
            if payment_request.expiry_duration:
                expiry_time = transaction_time + timedelta(minutes=payment_request.expiry_duration)

            # Create metadata - only store additional info, not duplicates
            metadata = {
                "token": result.get("token"),
                "expiry_time": expiry_time.isoformat() if expiry_time else None,
                "expiry_duration": payment_request.expiry_duration,
                # "midtrans_transaction_time": result.get("transaction_t ime"),
                # "midtrans_status": result.get("status_message")
            }

            return PaymentResponse(
                id=f"payment-{payment_request.order_id}",
                order_id=payment_request.order_id,
                transaction_id=payment_request.order_id,
                amount=payment_request.amount,
                status=PaymentStatus.PENDING,
                payment_method=payment_request.payment_method,
                payment_url=result.get("redirect_url"),
                created_at=transaction_time,
                updated_at=transaction_time,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to create transaction: {e}")
            raise MidtransAPIException(0, f"Failed to create payment: {str(e)}")

    async def get_transaction_status(self, transaction_id: str) -> PaymentStatus:
        """Get payment status from Midtrans"""
        try:
            result = self.client.get_transaction_status(transaction_id)

            transaction_status = result.get("transaction_status", "")
            fraud_status = result.get("fraud_status", "")

            return self.mapper.map_status_from_midtrans(transaction_status, fraud_status)

        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return PaymentStatus.PENDING

    async def cancel_payment_transaction(self, transaction_id: str, reason: Optional[str] = None) -> PaymentResponse:
        """Cancel a payment transaction"""
        try:
            result = self.client.cancel_transaction(transaction_id)

            # Clean metadata - only store additional info
            metadata = {
                "midtrans_status_code": result.get("status_code"),
                "midtrans_status_message": result.get("status_message"),
                "midtrans_transaction_time": result.get("transaction_time"),
                "cancellation_reason": reason,
                "cancelled_at": datetime.now().isoformat()
            }

            return PaymentResponse(
                id=f"payment-{transaction_id}",
                order_id=result.get("order_id", transaction_id),
                transaction_id=transaction_id,
                amount=float(result.get("gross_amount", 0)),
                status=PaymentStatus.CANCELED,
                payment_method=PaymentMethod.CREDIT_CARD,  # Default
                payment_url=None,  # No payment URL for cancelled payments
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to cancel payment: {e}")
            raise MidtransTransactionException(f"Failed to cancel payment: {str(e)}")

    async def refund_payment_transaction(self, transaction_id: str, amount: Optional[float] = None, reason: str = None) -> PaymentResponse:
        """Refund a payment transaction"""
        try:
            # If no amount specified, get transaction details for full refund
            if amount is None:
                status_result = self.client.get_transaction_status(transaction_id)
                amount = float(status_result.get("gross_amount", 0))

            # Build refund payload
            payload = self.payload_builder.build_refund_payload(transaction_id, amount, reason)

            # Execute refund
            result = self.client.refund_transaction(transaction_id, payload)

            # Clean metadata - only store additional info
            metadata = {
                "refund_key": result.get("refund_key"),
                "refund_amount": amount,
                "refund_reason": reason,
                "midtrans_status_code": result.get("status_code"),
                "midtrans_status_message": result.get("status_message"),
                "refunded_at": datetime.now().isoformat()
            }

            return PaymentResponse(
                id=f"payment-{transaction_id}",
                order_id=result.get("order_id", transaction_id),
                transaction_id=transaction_id,
                amount=amount,
                status=PaymentStatus.REFUNDED,
                payment_method=PaymentMethod.CREDIT_CARD,  # Default
                payment_url=None,  # No payment URL for refunded payments
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to refund payment: {e}")
            raise MidtransTransactionException(f"Failed to refund payment: {str(e)}")

    async def process_webhook_notification(self, notification_data: Dict[str, Any]) -> PaymentResponse:
        """Process webhook notification and return PaymentResponse"""
        try:
            self._validate_notification_data(notification_data)

            transaction_id = notification_data.get("transaction_id", "")
            order_id = notification_data.get("order_id", "")
            transaction_status = notification_data.get("transaction_status", "")
            gross_amount = float(notification_data.get("gross_amount", 0))
            fraud_status = notification_data.get("fraud_status")

            # Map status
            status = self.mapper.map_status_from_midtrans(transaction_status, fraud_status)

            # Determine payment method
            payment_method = self.mapper.determine_payment_method_from_notification(notification_data)

            return PaymentResponse(
                id=f"payment-{transaction_id}",
                order_id=order_id,
                transaction_id=transaction_id,
                amount=gross_amount,
                status=status,
                payment_method=payment_method,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=notification_data
            )

        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            raise MidtransValidationException(f"Failed to process webhook: {str(e)}")

    async def process_payment_notification(self, notification_data: Dict[str, Any]) -> PaymentNotification:
        """Process notification and return PaymentNotification"""
        try:
            self._validate_notification_data(notification_data)

            transaction_id = notification_data.get("transaction_id", "")
            order_id = notification_data.get("order_id", "")
            transaction_status = notification_data.get("transaction_status", "")
            gross_amount = float(notification_data.get("gross_amount", 0))
            payment_type = notification_data.get("payment_type", "")
            fraud_status = notification_data.get("fraud_status")

            # Map status
            status = self.mapper.map_status_from_midtrans(transaction_status, fraud_status)

            return PaymentNotification(
                transaction_id=transaction_id,
                order_id=order_id,
                status=status,
                amount=gross_amount,
                payment_type=payment_type,
                processed_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to process notification: {e}")
            raise MidtransValidationException(f"Failed to process notification: {str(e)}")

    def _validate_notification_data(self, data: Dict[str, Any]) -> None:
        """Validate required notification fields"""
        required_fields = ["transaction_id", "order_id", "transaction_status", "gross_amount"]

        for field in required_fields:
            if field not in data:
                raise MidtransValidationException(f"Missing required field: {field}")
