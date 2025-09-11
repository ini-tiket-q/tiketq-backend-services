import hashlib
import logging
from typing import Dict, Any, Optional
from domain.models import WebhookNotification, PaymentStatus
from adapters.midtrans.models import MidtransMapper

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
            order_id = notification_data.get('order_id', '')
            status_code = notification_data.get('status_code', '')
            gross_amount = notification_data.get('gross_amount', '')
            signature_key = notification_data.get('signature_key', '')

            # Create signature string
            signature_string = f"{order_id}{status_code}{gross_amount}{self.server_key}"

            # Generate hash
            generated_signature = hashlib.sha512(signature_string.encode()).hexdigest()

            return generated_signature == signature_key

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    async def process_webhook(
        self,
        notification_data: Dict[str, Any],
        payment_repository,
        verify_signature: bool = True
    ) -> Dict[str, Any]:
        """Process Midtrans webhook notification"""
        try:
            # Verify signature if required
            if verify_signature and not self.verify_signature(notification_data):
                raise ValueError("Invalid signature")

            # Parse notification
            webhook_notification = WebhookNotification(**notification_data)

            # Map status
            new_status = MidtransMapper.map_status_from_midtrans(
                webhook_notification.transaction_status,
                webhook_notification.fraud_status
            )

            # Get payment by order_id or transaction_id
            payment = await payment_repository.get_payment_by_order_id(webhook_notification.order_id)
            if not payment:
                logger.warning(f"Payment not found for order_id: {webhook_notification.order_id}")
                return {"status": "payment_not_found", "order_id": webhook_notification.order_id}

            # Update payment status if changed
            if payment.status != new_status:
                await payment_repository.update_payment_status(payment.id, new_status)
                logger.info(f"Payment status updated: {payment.id} -> {new_status}")

            return {
                "status": "success",
                "order_id": webhook_notification.order_id,
                "transaction_id": webhook_notification.transaction_id,
                "new_status": new_status.value,
                "processed_at": notification_data.get('transaction_time')
            }

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise
