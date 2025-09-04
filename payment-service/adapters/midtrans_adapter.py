from typing import Optional

from domain.models import (
    PaymentRequest, PaymentResponse, PaymentStatus, PaymentNotification
)
from domain.repository import PaymentRepository

from .midtrans import MidtransClient, MidtransServiceHandler

class MidtransAdapter(PaymentRepository):
    """
    Clean and simplified Midtrans adapter using service handler pattern
    """

    def __init__(self, server_key: str, client_key: str, is_production: bool = False):
        """Initialize Midtrans adapter"""
        self.client = MidtransClient(server_key, client_key, is_production)
        self.service_handler = MidtransServiceHandler(self.client)

    async def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Create a payment transaction"""
        return await self.service_handler.create_payment_transaction(payment_request)

    async def get_payment_status(self, transaction_id: str) -> PaymentStatus:
        """Get payment status"""
        return await self.service_handler.get_transaction_status(transaction_id)

    async def cancel_payment(self, transaction_id: str, reason: Optional[str] = None) -> PaymentResponse:
        """Cancel a payment"""
        return await self.service_handler.cancel_payment_transaction(transaction_id, reason)

    async def refund_payment(self, transaction_id: str, amount: Optional[float] = None, reason: str = None) -> PaymentResponse:
        """Refund a payment"""
        return await self.service_handler.refund_payment_transaction(transaction_id, amount, reason)

    async def handle_webhook(self, notification_data: dict) -> PaymentResponse:
        """Handle webhook notification"""
        return await self.service_handler.process_webhook_notification(notification_data)

    async def handle_notification(self, notification_data: dict) -> PaymentNotification:
        """Handle payment notification"""
        return await self.service_handler.process_payment_notification(notification_data)
