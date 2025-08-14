import hashlib
import json
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from datetime import datetime

from domain.models import WebhookNotification, PaymentStatus
from domain.repository import PaymentStorageRepository

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Webhook handler for processing payment notifications from Midtrans.
    """

    def __init__(self, server_key: str):
        self.server_key = server_key

    def verify_signature(self, notification_data: Dict[str, Any]) -> bool:
        """Verify Midtrans webhook signature"""
        try:
            order_id = notification_data.get('order_id')
            status_code = notification_data.get('status_code')
            gross_amount = notification_data.get('gross_amount')
            signature_key = notification_data.get('signature_key')

            # Create signature string
            signature_string = f"{order_id}{status_code}{gross_amount}{self.server_key}"

            # Generate hash
            calculated_signature = hashlib.sha512(signature_string.encode()).hexdigest()

            return calculated_signature == signature_key

        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

    def parse_notification(self, notification_data: Dict[str, Any]) -> WebhookNotification:
        """Parse webhook notification"""
        required_fields = ['transaction_id', 'order_id', 'transaction_status', 'gross_amount', 'payment_type']

        for field in required_fields:
            if field not in notification_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )

        return WebhookNotification(**notification_data)

    def map_status_to_payment_status(self, transaction_status: str, fraud_status: Optional[str] = None) -> PaymentStatus:
        """Map Midtrans status to internal PaymentStatus"""
        # Handle fraud status first
        if fraud_status == "deny":
            return PaymentStatus.FAILED

        # Map transaction status
        status_mapping = {
            "capture": PaymentStatus.SUCCESS,
            "settlement": PaymentStatus.SUCCESS,
            "pending": PaymentStatus.PENDING,
            "deny": PaymentStatus.FAILED,
            "cancel": PaymentStatus.CANCELED,
            "expire": PaymentStatus.EXPIRED,
            "refund": PaymentStatus.REFUNDED,
            "partial_refund": PaymentStatus.REFUNDED,
        }

        return status_mapping.get(transaction_status.lower(), PaymentStatus.PENDING)

    async def process_webhook(
        self,
        notification_data: Dict[str, Any],
        payment_repository: PaymentStorageRepository,
        verify_signature: bool = True
    ) -> Dict[str, Any]:
        """Process webhook notification and update payment status"""

        try:
            # Verify signature if required
            if verify_signature and not self.verify_signature(notification_data):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature"
                )

            # Parse notification
            notification = self.parse_notification(notification_data)

            # Map status
            new_status = self.map_status_to_payment_status(
                notification.transaction_status,
                notification.fraud_status
            )

            # Find payment by order_id (since Midtrans uses order_id as reference)
            payments = await payment_repository.get_payments_by_order(notification.order_id)

            if not payments:
                logger.warning(f"No payment found for order_id: {notification.order_id}")
                return {"status": "warning", "message": "Payment not found"}

            # Update the latest payment for this order
            payment = payments[0]  # Get the most recent payment

            # Only update if status has changed
            if payment.status != new_status:
                await payment_repository.update_payment_status(payment.id, new_status)
                logger.info(f"Payment status updated: {payment.id} -> {new_status}")

            return {
                "status": "success",
                "message": "Notification processed successfully",
                "payment_id": payment.id,
                "old_status": payment.status.value,
                "new_status": new_status.value
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process webhook: {str(e)}"
            )
