from abc import ABC, abstractmethod
from typing import List, Optional
from .models import PaymentRequest, PaymentResponse, PaymentStatus, PaymentNotification


class PaymentRepository(ABC):
    """Interface for payment gateway operations"""

    @abstractmethod
    async def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Create a new payment"""
        pass

    @abstractmethod
    async def get_payment_status(self, transaction_id: str) -> PaymentStatus:
        """Get the status of a payment"""
        pass

    @abstractmethod
    async def cancel_payment(self, transaction_id: str, reason: Optional[str] = None) -> PaymentResponse:
        """Cancel a payment"""
        pass

    @abstractmethod
    async def refund_payment(self, transaction_id: str, amount: Optional[float] = None, reason: str = None) -> PaymentResponse:
        """Refund a payment"""
        pass

    @abstractmethod
    async def handle_webhook(self, notification_data: dict) -> PaymentResponse:
        """Process payment notification from payment gateway"""
        pass

    @abstractmethod
    async def handle_notification(self, notification_data: dict) -> PaymentNotification:
        """Process payment notification and return PaymentNotification"""
        pass


class PaymentStorageRepository(ABC):
    """Interface for payment storage operations"""

    @abstractmethod
    async def save_payment(self, payment: PaymentResponse) -> PaymentResponse:
        """Save payment details"""
        pass

    @abstractmethod
    async def get_payment(self, payment_id: str) -> Optional[PaymentResponse]:
        """Get payment by ID"""
        pass

    @abstractmethod
    async def update_payment_status(self, payment_id: str, status: PaymentStatus) -> PaymentResponse:
        """Update payment status"""
        pass

    @abstractmethod
    async def get_payments_by_order(self, order_id: str) -> List[PaymentResponse]:
        """Get all payments for an order"""
        pass

    @abstractmethod
    async def get_payments_by_order_id(self, order_id: str) -> List[PaymentResponse]:
        """Get all payments for an order ID"""
        pass
