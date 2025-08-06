from typing import Optional, List
from .models import PaymentRequest, PaymentResponse, PaymentStatus, PaymentNotification
from .repository import PaymentRepository, PaymentStorageRepository


class PaymentService:
    """
    Payment service that implements business logic for payment processing.
    This service uses the repository interfaces (ports) to interact with
    external payment gateways and storage.
    """
    
    def __init__(
        self, 
        payment_repository: PaymentRepository,
        storage_repository: PaymentStorageRepository
    ):
        """
        Initialize the payment service with required repositories
        
        Args:
            payment_repository: Repository for payment gateway operations
            storage_repository: Repository for database storage operations
        """
        self.payment_repository = payment_repository
        self.storage_repository = storage_repository
    
    async def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Create a new payment transaction
        
        Args:
            payment_request: Payment request details
            
        Returns:
            PaymentResponse: Payment transaction details
        """
        # Create payment with payment gateway
        payment_response = await self.payment_repository.create_payment(payment_request)
        
        # Store payment record in database
        await self.storage_repository.save_payment(payment_response)
        
        return payment_response
    
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """
        Get current status of a payment
        
        Args:
            payment_id: ID of the payment
            
        Returns:
            PaymentStatus: Current payment status
        """
        # First check if we have the payment in our database
        payment = await self.storage_repository.get_payment(payment_id)
        
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")
        
        # Get latest status from payment gateway
        status = await self.payment_repository.get_payment_status(payment_id)
        
        # Update status in database if it has changed
        if status != payment.status:
            await self.storage_repository.update_payment_status(payment_id, status)
        
        return status
    
    async def cancel_payment(self, payment_id: str) -> PaymentResponse:
        """
        Cancel a pending payment
        
        Args:
            payment_id: ID of the payment to cancel
            
        Returns:
            PaymentResponse: Updated payment details
        """
        # Check if payment exists
        payment = await self.storage_repository.get_payment(payment_id)
        
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")
        
        # Only pending or processing payments can be canceled
        if payment.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise ValueError(f"Cannot cancel payment with status {payment.status}")
        
        # Cancel payment with payment gateway
        updated_payment = await self.payment_repository.cancel_payment(payment_id)
        
        # Update payment in database
        await self.storage_repository.update_payment_status(payment_id, updated_payment.status)
        
        return updated_payment
    
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """
        Refund a completed payment
        
        Args:
            payment_id: ID of the payment to refund
            amount: Amount to refund (if None, full refund)
            
        Returns:
            PaymentResponse: Updated payment details
        """
        # Check if payment exists
        payment = await self.storage_repository.get_payment(payment_id)
        
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")
        
        # Only successful payments can be refunded
        if payment.status != PaymentStatus.SUCCESS:
            raise ValueError(f"Cannot refund payment with status {payment.status}")
        
        # Refund payment with payment gateway
        updated_payment = await self.payment_repository.refund_payment(payment_id, amount)
        
        # Update payment in database
        await self.storage_repository.update_payment_status(payment_id, updated_payment.status)
        
        return updated_payment
    
    async def handle_notification(self, notification_data: dict) -> PaymentNotification:
        """
        Process payment notification from payment gateway
        
        Args:
            notification_data: Raw notification data from payment gateway
            
        Returns:
            PaymentNotification: Processed notification
        """
        # Process notification with payment gateway
        notification = await self.payment_repository.handle_notification(notification_data)
        
        # Update payment status in database
        payment = await self.storage_repository.get_payment(notification.transaction_id)
        
        if payment:
            # Map notification status to our PaymentStatus enum
            status_mapping = {
                "pending": PaymentStatus.PENDING,
                "capture": PaymentStatus.PROCESSING,
                "settlement": PaymentStatus.SUCCESS,
                "deny": PaymentStatus.FAILED,
                "cancel": PaymentStatus.CANCELED,
                "expire": PaymentStatus.EXPIRED,
                "refund": PaymentStatus.REFUNDED,
            }
            
            status = status_mapping.get(notification.status_code.lower(), PaymentStatus.PENDING)
            await self.storage_repository.update_payment_status(notification.transaction_id, status)
        
        return notification
    
    async def get_payments_by_order_id(self, order_id: str) -> List[PaymentResponse]:
        """
        Get all payments for an order
        
        Args:
            order_id: Order ID
            
        Returns:
            List[PaymentResponse]: List of payments for the order
        """
        return await self.storage_repository.get_payments_by_order_id(order_id)
