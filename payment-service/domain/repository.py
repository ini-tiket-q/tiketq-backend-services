from abc import ABC, abstractmethod
from typing import Optional, List
from .models import PaymentRequest, PaymentResponse, PaymentNotification, PaymentStatus


class PaymentRepository(ABC):
    """
    Payment repository interface (port) for payment gateway operations.
    This defines the contract that any payment gateway adapter must implement.
    """
    
    @abstractmethod
    async def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Create a new payment transaction with the payment gateway
        
        Args:
            payment_request: Payment request details
            
        Returns:
            PaymentResponse: Response from payment gateway with transaction details
        """
        pass
    
    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """
        Get the current status of a payment
        
        Args:
            payment_id: ID of the payment to check
            
        Returns:
            PaymentStatus: Current status of the payment
        """
        pass
    
    @abstractmethod
    async def cancel_payment(self, payment_id: str) -> PaymentResponse:
        """
        Cancel a pending payment
        
        Args:
            payment_id: ID of the payment to cancel
            
        Returns:
            PaymentResponse: Updated payment response
        """
        pass
    
    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """
        Refund a completed payment, either fully or partially
        
        Args:
            payment_id: ID of the payment to refund
            amount: Amount to refund (if None, full refund)
            
        Returns:
            PaymentResponse: Updated payment response
        """
        pass
    
    @abstractmethod
    async def handle_notification(self, notification_data: dict) -> PaymentNotification:
        """
        Process a payment notification/webhook from the payment gateway
        
        Args:
            notification_data: Raw notification data from payment gateway
            
        Returns:
            PaymentNotification: Processed notification
        """
        pass


class PaymentStorageRepository(ABC):
    """
    Repository interface for storing payment records in the database
    """
    
    @abstractmethod
    async def save_payment(self, payment: PaymentResponse) -> None:
        """
        Save payment record to database
        
        Args:
            payment: Payment response to save
        """
        pass
    
    @abstractmethod
    async def get_payment(self, payment_id: str) -> Optional[PaymentResponse]:
        """
        Retrieve payment record from database
        
        Args:
            payment_id: ID of payment to retrieve
            
        Returns:
            Optional[PaymentResponse]: Payment record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update_payment_status(self, payment_id: str, status: PaymentStatus) -> None:
        """
        Update payment status in database
        
        Args:
            payment_id: ID of payment to update
            status: New payment status
        """
        pass
    
    @abstractmethod
    async def get_payments_by_order_id(self, order_id: str) -> List[PaymentResponse]:
        """
        Get all payments associated with an order
        
        Args:
            order_id: Order ID to search for
            
        Returns:
            List[PaymentResponse]: List of payments for the order
        """
        pass
