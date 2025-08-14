from typing import Optional, List
from .models import PaymentRequest, PaymentResponse, PaymentStatus, PaymentNotification
from .repository import PaymentRepository, PaymentStorageRepository
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Payment service that implements business logic for payment processing.
    """

    def __init__(
        self,
        payment_repository: PaymentRepository,
        storage_repository: PaymentStorageRepository
    ):
        self.payment_repository = payment_repository
        self.storage_repository = storage_repository

    async def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Create a new payment through the payment gateway and store it."""
        try:
            # Create payment through payment gateway (Midtrans)
            payment_response = await self.payment_repository.create_payment(payment_request)

            # Save to storage repository (Database)
            await self.storage_repository.save_payment(payment_response)

            logger.info(f"Payment created and saved: {payment_response.id}")
            return payment_response

        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            raise ValueError(f"Failed to create payment: {str(e)}")

    async def get_payment(self, payment_id: str) -> Optional[PaymentResponse]:
        """Get payment details with auto status update"""
        try:
            # Get payment from storage
            payment = await self.storage_repository.get_payment(payment_id)

            if not payment:
                logger.warning(f"Payment not found: {payment_id}")
                return None

            # Auto check and update status if payment is still pending
            if payment.status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
                try:
                    # Check latest status from Midtrans using order_id
                    latest_status = await self.payment_repository.get_payment_status(payment.order_id)

                    # Update status if it has changed
                    if latest_status != payment.status:
                        logger.info(f"Auto-updating payment status: {payment.id} from {payment.status} to {latest_status}")
                        await self.storage_repository.update_payment_status(payment.id, latest_status)

                        # Get updated payment
                        payment = await self.storage_repository.get_payment(payment.id)

                except Exception as e:
                    logger.warning(f"Failed to auto-update status for payment {payment_id}: {e}")
                    # Continue with existing status from database

            return payment

        except Exception as e:
            logger.error(f"Error getting payment: {str(e)}")
            raise ValueError(f"Failed to get payment: {str(e)}")

    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Get current status of a payment with auto-update"""
        # First check if we have the payment in our database
        payment = await self.storage_repository.get_payment(payment_id)

        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")

        # Get latest status from payment gateway using order_id
        try:
            latest_status = await self.payment_repository.get_payment_status(payment.order_id)

            # Update status in database if it has changed
            if latest_status != payment.status:
                logger.info(f"Updating payment status: {payment_id} from {payment.status} to {latest_status}")
                await self.storage_repository.update_payment_status(payment_id, latest_status)
                return latest_status

            return payment.status

        except Exception as e:
            logger.warning(f"Failed to get latest status from gateway: {e}")
            return payment.status

    async def cancel_payment(self, payment_id: str) -> PaymentResponse:
        """Cancel a pending payment"""
        # Check if payment exists
        payment = await self.storage_repository.get_payment(payment_id)

        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")

        # Only pending or processing payments can be canceled
        if payment.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise ValueError(f"Cannot cancel payment with status: {payment.status}")

        # Cancel payment with payment gateway
        updated_payment = await self.payment_repository.cancel_payment(payment.order_id)

        # Update payment in database
        await self.storage_repository.update_payment_status(payment_id, PaymentStatus.CANCELED)

        # Return updated payment
        return await self.storage_repository.get_payment(payment_id)

    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """Refund a completed payment"""
        # Check if payment exists
        payment = await self.storage_repository.get_payment(payment_id)

        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")

        # Only successful payments can be refunded
        if payment.status != PaymentStatus.SUCCESS:
            raise ValueError(f"Cannot refund payment with status: {payment.status}")

        # Refund payment with payment gateway
        updated_payment = await self.payment_repository.refund_payment(payment.order_id, amount)

        # Update payment in database
        await self.storage_repository.update_payment_status(payment_id, PaymentStatus.REFUNDED)

        # Return updated payment
        return await self.storage_repository.get_payment(payment_id)

    async def handle_notification(self, notification_data: dict) -> PaymentNotification:
        """Handle payment notification from gateway"""
        try:
            # Process notification through payment repository
            notification = await self.payment_repository.handle_notification(notification_data)

            # Find and update payment in storage
            payments = await self.storage_repository.get_payments_by_order(notification.order_id)

            if payments:
                payment = payments[0]  # Get the latest payment

                # Update status if changed
                if payment.status != notification.status:
                    await self.storage_repository.update_payment_status(payment.id, notification.status)
                    logger.info(f"Payment status updated via notification: {payment.id} -> {notification.status}")

            return notification

        except Exception as e:
            logger.error(f"Error handling notification: {e}")
            raise ValueError(f"Failed to handle notification: {str(e)}")

    async def get_payments_by_order_id(self, order_id: str) -> List[PaymentResponse]:
        """Get all payments for an order"""
        return await self.storage_repository.get_payments_by_order(order_id)
