from typing import Dict, Any, Optional
import hashlib
import hmac
import json
import logging

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Webhook handler for processing payment notifications from Midtrans.
    """

    def __init__(self, server_key: str):
        self.server_key = server_key

    def verify_signature(self, notification_data: Dict[str, Any], signature: str) -> bool:
        """Verify Midtrans signature"""
        try:
            # Create signature key for verification
            order_id = notification_data.get("order_id", "")
            status_code = notification_data.get("status_code", "")
            gross_amount = notification_data.get("gross_amount", "")

            signature_string = f"{order_id}{status_code}{gross_amount}{self.server_key}"
            calculated_signature = hashlib.sha512(signature_string.encode()).hexdigest()

            return hmac.compare_digest(calculated_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

    def map_transaction_status_to_payment_status(self, transaction_status: str) -> str:
        """Map Midtrans transaction status to internal payment status"""
        status_mapping = {
            "capture": "SUCCESS",      # ✅ Changed from "completed" to "SUCCESS"
            "settlement": "SUCCESS",   # ✅ Changed from "completed" to "SUCCESS"
            "pending": "PENDING",
            "deny": "FAILED",
            "cancel": "CANCELLED",
            "expire": "EXPIRED",
            "failure": "FAILED",
            "refund": "REFUNDED",
            "partial_refund": "REFUNDED"
        }

        mapped_status = status_mapping.get(transaction_status, "PENDING")
        logger.info(f"Mapped transaction_status '{transaction_status}' to '{mapped_status}'")
        return mapped_status

    async def process_webhook(self, notification_data: Dict[str, Any], payment_repository, verify_signature: bool = True) -> Dict[str, Any]:
        """Process webhook notification from Midtrans"""
        try:
            order_id = notification_data.get("order_id")
            transaction_status = notification_data.get("transaction_status")

            logger.info(f"Processing webhook for order: {order_id}, status: {transaction_status}")

            if not order_id:
                raise ValueError("order_id is required")

            # Get existing payment
            payment = None
            old_status = "not_found"

            try:
                payment = payment_repository.get_payment_by_order_id(order_id)
                if payment:
                    # Handle enum status safely
                    old_status = getattr(payment.status, 'value', str(payment.status))
                    logger.info(f"Found payment for order {order_id}, current status: {old_status}")
                else:
                    logger.warning(f"Payment not found for order_id: {order_id}")
            except Exception as get_error:
                logger.error(f"Error getting payment: {get_error}")

            new_status = self.map_transaction_status_to_payment_status(transaction_status)

            # Update payment status
            gateway_response = {
                "transaction_id": notification_data.get("transaction_id"),
                "transaction_status": transaction_status,
                "fraud_status": notification_data.get("fraud_status"),
                "status_code": notification_data.get("status_code"),
                "status_message": notification_data.get("status_message"),
                "payment_type": notification_data.get("payment_type"),
                "gross_amount": notification_data.get("gross_amount"),
                "currency": notification_data.get("currency", "IDR"),
                "settlement_time": notification_data.get("settlement_time"),
                "transaction_time": notification_data.get("transaction_time")
            }

            success = False
            if payment:  # Only update if payment exists
                try:
                    success = payment_repository.update_payment_status_by_order(
                        order_id=order_id,
                        status=new_status,
                        gateway_response=gateway_response
                    )

                    if success:
                        logger.info(f"Payment status updated for order {order_id}: {old_status} -> {new_status}")
                    else:
                        logger.error(f"Failed to update payment status for order {order_id}")

                except Exception as update_error:
                    logger.error(f"Error updating payment status: {update_error}")
                    success = False

            return {
                "order_id": order_id,
                "old_status": old_status,
                "new_status": new_status,
                "transaction_status": transaction_status,
                "updated": success,
                "payment_found": payment is not None
            }

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            logger.error(f"Notification data: {notification_data}")
            # Instead of re-raising, return error details
            raise Exception(f"Webhook processing failed for order {notification_data.get('order_id', 'unknown')}: {str(e)}")
