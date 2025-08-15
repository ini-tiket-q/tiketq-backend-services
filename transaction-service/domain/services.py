from typing import Optional, List, Dict, Any, Generator
from uuid import uuid4
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
import os
from fastapi import HTTPException, status, Depends, Header
from adapters.external_api import get_user_info

from domain.models import (
    TransactionInDB, TransactionCreate, TransactionUpdate, TransactionStatus,
    OrderInDB, OrderCreate, OrderUpdate, OrderStatus,
    PaymentInDB, PaymentCreate, PaymentStatus, Currency,
    # Payment request models
    PaymentCreateRequest, PaymentConfirmRequest, PaymentRefundRequest, PaymentWebhookRequest,
    # Order request models
    OrderCreateRequest, OrderStatusUpdateRequest,
    # Transaction request models
    TransactionCreateRequest, TransactionUpdateRequest, TransactionRefundRequest,
    # Report request and response models
    TransactionReportRequest, TransactionReportResponse, TransactionReportData,
    RevenueReportRequest, RevenueReportResponse, RevenueDataPoint,
    RefundReportRequest, RefundReportResponse, RefundReportData,
    # Refund models
    RefundCreate, RefundStatus,
    # Auth models
    UserRole, UserResponse
)

from adapters.db import (
    DBTransactionRepository,
    DBOrderRepository,
    DBPaymentRepository,
    DBRefundRepository,
    DatabaseSessionProvider,
)

# Configure logging
logger = logging.getLogger(__name__)

class TransactionService:
    """Service for handling transaction-related business logic.
    
    This service manages the complete lifecycle of transactions including creation,
    status updates, and retrieval while ensuring data consistency and business rules.
    """
    
    def __init__(
        self, 
        transaction_repo: DBTransactionRepository,
        order_repo: DBOrderRepository,
    ):
        self.transaction_repo = transaction_repo
        self.order_repo = order_repo
    
    def create_transaction(self, transaction_request: TransactionCreateRequest, user_id: int) -> Optional[TransactionInDB]:
        """Create a new transaction with validated request model.
        
        Args:
            transaction_request: Validated TransactionCreateRequest model
            user_id: ID of the user creating the transaction
            
        Returns:
            TransactionInDB if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or required data is missing
        """
        try:
            # Generate order number
            order_number = f"ORD-{str(uuid4())[:8].upper()}"
            
            # Use validated amounts from request
            subtotal = transaction_request.subtotal
            tax = transaction_request.tax
            discount = transaction_request.discount
            total = transaction_request.total
            
            # Convert TransactionItem objects to dictionaries
            items_as_dicts = [
                item.model_dump() if hasattr(item, 'model_dump') else dict(item)
                for item in transaction_request.items
            ]
            
            # Create order first
            order_data = {
                'user_id': user_id,
                'order_number': order_number,
                'service_type': transaction_request.service_type,
                'items': items_as_dicts,
                'subtotal': subtotal,
                'tax': tax,
                'discount': discount,
                'total': total,
                'status': OrderStatus.DRAFT,
                'metadata': transaction_request.metadata
            }
            
            order = self.order_repo.create_order(OrderCreate(**order_data))
            if not order:
                logger.error("Failed to create order")
                return None
            
            # Create transaction using validated request data
            transaction = TransactionCreate(
                user_id=user_id,
                order_id=order.order_number,
                transaction_type=transaction_request.transaction_type,
                amount=transaction_request.amount,
                currency=transaction_request.currency,
                status=TransactionStatus.PENDING,
                payment_method=transaction_request.payment_method,
                payment_gateway=transaction_request.payment_gateway,
                gateway_transaction_id=None,  # Set later during payment processing
                metadata=transaction_request.metadata
            )
            
            db_transaction = self.transaction_repo.create_transaction(transaction)
            if not db_transaction:
                logger.error("Failed to create transaction")
                return None
                
            return db_transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}", exc_info=True)
            return None
    
    def get_transaction(self, transaction_id: int, user_id: int) -> Optional[TransactionInDB]:
        """Get a transaction by ID with authorization check.
        
        Args:
            transaction_id: ID of the transaction to retrieve
            user_id: ID of the user making the request
            
        Returns:
            TransactionInDB if found and authorized, None otherwise
        """
        try:
            transaction = self.transaction_repo.get_transaction(transaction_id)
            if not transaction or transaction.user_id != user_id:
                return None
            return transaction
        except Exception as e:
            logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            return None

    def get_transactions_by_user(
        self, 
        user_id: int, 
        status: Optional[TransactionStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionInDB]:
        """Get paginated list of transactions for a user.
        
        Args:
            user_id: ID of the user
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of TransactionInDB objects
        """
        try:
            return self.transaction_repo.get_transactions_by_user(
                user_id=user_id,
                status=status,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving transactions for user {user_id}: {str(e)}")
            return []
    
    def get_all_transactions(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionInDB]:
        """Get all transactions (admin function).
        
        Args:
            skip: Number of transactions to skip for pagination
            limit: Maximum number of transactions to return
            
        Returns:
            List of TransactionInDB objects
        """
        try:
            return self.transaction_repo.get_transactions(
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving all transactions: {str(e)}")
            return []
    
    def update_transaction(
        self, 
        transaction_id: int, 
        update_request: TransactionUpdateRequest,
        user_id: int,  
    ) -> Optional[TransactionInDB]:
        """Update transaction with validated request model.
        
        Args:
            transaction_id: ID of the transaction to update
            update_request: Validated TransactionUpdateRequest model
            user_id: User ID for authorization
            
        Returns:
            Updated TransactionInDB if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or unauthorized access
        """
        try:
            transaction_check = self.transaction_repo.get_transaction(transaction_id)
            if not transaction_check or transaction_check.user_id != user_id:
                raise ValueError("Transaction not found or access denied")

            # Create update data from validated request
            update_data = {}
            
            if update_request.status is not None:
                update_data["status"] = update_request.status
            if update_request.payment_method is not None:
                update_data["payment_method"] = update_request.payment_method
            if update_request.payment_gateway is not None:
                update_data["payment_gateway"] = update_request.payment_gateway
            if update_request.gateway_transaction_id is not None:
                update_data["gateway_transaction_id"] = update_request.gateway_transaction_id
            if update_request.metadata is not None:
                update_data["metadata"] = update_request.metadata

            transaction_update = TransactionUpdate(**update_data)
                
            return self.transaction_repo.update_transaction(
                transaction_id, 
                transaction_update
            )
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
            return None
    
    # Delete transaction with authorization check (should be admin)
    # def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
    #     """Delete a transaction with authorization check"""
    #     transaction = self.transaction_repo.get_transaction(transaction_id)
    #     if not transaction or transaction.user_id != user_id:
    #         return False
            
    #     return self.transaction_repo.delete_transaction(transaction_id)

class OrderService:
    """Service for handling order-related business logic.
    
    This service manages order creation, retrieval, and updates while enforcing
    business rules and data consistency.
    """
    
    def __init__(
        self, 
        order_repo: DBOrderRepository,
    ):
        self.order_repo = order_repo
    
    def get_order(self, order_id: int, user_id: int) -> Optional[OrderInDB]:
        """Get an order by ID with optional authorization check.
        
        Args:
            order_id: ID of the order to retrieve
            user_id: Optional user ID for authorization
            
        Returns:
            OrderInDB if found (and authorized if user_id provided), None otherwise
        """
        try:
            order = self.order_repo.get_order(order_id)
            if not order or order.user_id != user_id:
                return None
            return order
        except Exception as e:
            logger.error(f"Error retrieving order {order_id}: {str(e)}")
            return None
    
    def get_orders_by_user(
        self, 
        user_id: int, 
        status: Optional[OrderStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[OrderInDB]:
        """Get paginated list of orders for a user.
        
        Args:
            user_id: ID of the user
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of OrderInDB objects
        """
        try:
            return self.order_repo.get_orders_by_user(
                user_id=user_id,
                status=status,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving orders for user {user_id}: {str(e)}")
            return []
    
    def create_order(self, order_request: "OrderCreateRequest", user_id: int) -> Optional[OrderInDB]:
        """Create a new order with Pydantic validation.
        
        Args:
            order_request: Validated OrderCreateRequest model
            user_id: ID of the user creating the order
            
        Returns:
            OrderInDB if created successfully, None otherwise
            
        Raises:
            ValueError: If validation fails or required data is missing
        """
        try:
            # Calculate totals from validated items
            items = order_request.items
            subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
            total = subtotal + order_request.tax - order_request.discount
            
            # Prepare order data
            order_create_data = {
                "user_id": user_id,
                "service_type": order_request.service_type,
                "items": order_request.items,
                "subtotal": subtotal,
                "tax": order_request.tax,
                "discount": order_request.discount,
                "total": total,
                "status": OrderStatus.DRAFT,
                "metadata": order_request.metadata
            }
            
            order_create = OrderCreate(**order_create_data)
            return self.order_repo.create_order(order_create)
            
        except Exception as e:
            logger.error(f"Error creating order for user {user_id}: {str(e)}")
            return None
    
    def get_orders(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[OrderStatus] = None
    ) -> List[OrderInDB]:
        """Get all orders (admin function).
        
        Args:
            skip: Number of orders to skip for pagination
            limit: Maximum number of orders to return
            status: Optional status filter
            
        Returns:
            List of OrderInDB objects
        """
        try:
            return self.order_repo.get_orders(
                status=status,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving all orders: {str(e)}")
            return []
    
    def update_order_status(
        self, 
        order_id: int, 
        status_request: "OrderStatusUpdateRequest",
        user_id: int
    ) -> Optional[OrderInDB]:
        """Update order status with Pydantic validation.
        
        Args:
            order_id: ID of the order to update
            status_request: Validated OrderStatusUpdateRequest model
            user_id: User ID for authorization
            
        Returns:
            Updated OrderInDB if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or unauthorized access
        """
        try:
            order_check = self.order_repo.get_order(order_id)
            if not order_check or order_check.user_id != user_id:
                raise ValueError("Order not found or access denied")
                
            # Create update data from validated request
            update_data = {
                "status": status_request.status
            }
            
            # Add metadata if provided
            if status_request.metadata is not None:
                update_data["metadata"] = status_request.metadata
            
            update_order = OrderUpdate(**update_data)
            
            # If order is completed, set completed_at
            if update_order.status == OrderStatus.COMPLETED and 'completed_at' not in update_order:
                update_order.completed_at = datetime.now(timezone.utc)
                
            return self.order_repo.update_order(
                order_id, 
                update_order
            )
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
            return None

    # def delete_order(self, order_id: int, user_id: int) -> bool:
                

class PaymentService:
    """Service for handling payment-related business logic.
    
    This service manages payment processing, status updates, and validation
    while integrating with payment gateways.
    """
    
    def __init__(
        self, 
        transaction_repo: DBTransactionRepository,
        payment_repo: DBPaymentRepository,
    ):
        self.transaction_repo = transaction_repo
        self.payment_repo = payment_repo
    
    def create_payment(
        self, 
        transaction_id: int,
        payment_data: PaymentCreateRequest,
        user_id: int
    ) -> Optional[PaymentInDB]:
        """Create a new payment record for a transaction.
        
        Args:
            transaction_id: ID of the transaction to create payment for
            payment_data: Dictionary containing payment details
            user_id: ID of the user making the payment
            
        Returns:
            PaymentInDB if successful, None otherwise
            
        Raises:
            ValueError: If payment data validation fails
        """
        # Validate request data using Pydantic model
        request_dict = {
            "transaction_id": transaction_id,
            **payment_data
        }
        
        try:
            validated_request = PaymentCreateRequest(**request_dict)
        except Exception as e:
            logger.error(f"Payment validation failed: {str(e)}")
            raise ValueError(f"Payment validation failed: {str(e)}")
        
        try:
            # Get and validate transaction
            transaction = self.transaction_repo.get_transaction(transaction_id)
            if not transaction or transaction.user_id != user_id:
                logger.error(f"Transaction {transaction_id} not found or unauthorized")
                return None
                
            # Check if transaction is already completed
            if transaction.status == TransactionStatus.COMPLETED:
                logger.warning(f"Transaction {transaction_id} is already completed")
                payments = self.payment_repo.get_payments_by_transaction(transaction_id)
                return payments[0] if payments else None
            
            # Create payment record using validated data
            payment = PaymentCreate(
                transaction_id=validated_request.transaction_id,
                amount=validated_request.amount,
                currency=Currency(validated_request.currency) if validated_request.currency else transaction.currency,
                payment_method=validated_request.payment_method,
                payment_gateway=validated_request.gateway,
                gateway_transaction_id=validated_request.gateway_transaction_id,
                status=PaymentStatus.PENDING,
                metadata=validated_request.metadata or {}
            )
            
            # Save payment to database
            db_payment = self.payment_repo.create_payment(payment)
            if not db_payment:
                logger.error(f"Failed to create payment for transaction {transaction_id}")
                return None
                
            # Update transaction status
            self.transaction_repo.update_transaction(
                transaction_id,
                TransactionUpdate(
                    status=TransactionStatus.PROCESSING,
                    payment_method=payment.payment_method,
                    payment_gateway=payment.payment_gateway,
                    gateway_transaction_id=payment.gateway_transaction_id
                )
            )
            
            return db_payment
            
        except Exception as e:
            logger.error(f"Error creating payment for transaction {transaction_id}: {str(e)}", exc_info=True)
            return None
    
    def confirm_payment(
        self, 
        payment_id: int, 
        gateway_response: PaymentConfirmRequest,
        confirmed_by: Optional[int] = None
    ) -> Optional[PaymentInDB]:
        """Confirm a payment with gateway response data.
        
        Args:
            payment_id: ID of the payment to confirm
            gateway_response: Response data from payment gateway
            confirmed_by: Optional user ID who confirmed the payment
            
        Returns:
            Updated PaymentInDB if successful, None otherwise
            
        Raises:
            ValueError: If payment confirmation data validation fails
        """
        # Validate request data using Pydantic model
        request_dict = {
            "payment_id": payment_id,
            "gateway_response": gateway_response,
            "confirmed_by": confirmed_by
        }
        
        try:
            validated_request = PaymentConfirmRequest(**request_dict)
        except Exception as e:
            logger.error(f"Payment confirmation validation failed: {str(e)}")
            raise ValueError(f"Payment confirmation validation failed: {str(e)}")
        
        try:
            # Get payment with transaction
            payment = self.payment_repo.get_payment(validated_request.payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return None
                
            # Update payment status
            status = PaymentStatus.COMPLETED if validated_request.gateway_response.get('success', False) else PaymentStatus.FAILED
            
            # Update payment record
            updated_payment = self.payment_repo.update_payment_status(
                payment_id=validated_request.payment_id,
                status=status,
                gateway_transaction_id=validated_request.gateway_response.get('transaction_id')
            )
            
            if not updated_payment:
                logger.error(f"Failed to update payment {payment_id}")
                return None
                
            # Update transaction status based on payment status
            transaction_status = (
                TransactionStatus.COMPLETED 
                if status == PaymentStatus.COMPLETED 
                else TransactionStatus.FAILED
            )
            
            self.transaction_repo.update_transaction(
                transaction_id=payment.transaction_id,
                transaction=TransactionUpdate(
                    status=transaction_status,
                    gateway_transaction_id=validated_request.gateway_response.get('transaction_id'),
                    metadata={
                        **payment.transaction.metadata,
                        'gateway_response': validated_request.gateway_response,
                        'confirmed_by': validated_request.confirmed_by,
                        'confirmed_at': datetime.utcnow().isoformat()
                    }
                )
            )
            
            return updated_payment
            
        except Exception as e:
            logger.error(f"Error confirming payment {payment_id}: {str(e)}", exc_info=True)
            return None

    def process_refund(
        self,
        payment_id: int,
        refund_data: Dict[str, Any],
        refunded_by: int
    ) -> Optional[PaymentInDB]:
        """Process a payment refund with validation.
        
        Args:
            payment_id: ID of the payment to refund
            refund_data: Dictionary containing refund details
            refunded_by: ID of the user processing the refund
            
        Returns:
            Updated PaymentInDB if successful, None otherwise
            
        Raises:
            ValueError: If refund data validation fails
        """
        # Validate request data using Pydantic model
        request_dict = {
            "payment_id": payment_id,
            "refunded_by": refunded_by,
            **refund_data
        }
        
        try:
            validated_request = PaymentRefundRequest(**request_dict)
        except Exception as e:
            logger.error(f"Payment refund validation failed: {str(e)}")
            raise ValueError(f"Payment refund validation failed: {str(e)}")
        
        try:
            # Get the payment first
            payment = self.payment_repo.get_payment(validated_request.payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return None
            
            # Check if payment can be refunded
            if payment.status != PaymentStatus.COMPLETED:
                raise ValueError("Only completed payments can be refunded")
            
            # Update payment status to refunded
            # Note: This is a simplified implementation
            # In a real system, you'd integrate with payment gateway APIs
            updated_payment = self.payment_repo.update_payment(
                payment_id=validated_request.payment_id,
                payment_data={
                    "status": PaymentStatus.REFUNDED.value,
                    "metadata": {
                        **payment.metadata,
                        "refund_reason": validated_request.reason,
                        "refunded_by": validated_request.refunded_by,
                        "refund_amount": validated_request.amount or payment.amount
                    }
                }
            )
            
            return updated_payment
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error processing refund for payment {payment_id}: {str(e)}", exc_info=True)
            return None

    def process_webhook(
        self,
        webhook_data: Dict[str, Any]
    ) -> Optional[PaymentInDB]:
        """Process a payment webhook with validation.
        
        Args:
            webhook_data: Dictionary containing webhook data
            
        Returns:
            Updated PaymentInDB if successful, None otherwise
            
        Raises:
            ValueError: If webhook data validation fails
        """
        try:
            validated_request = PaymentWebhookRequest(**webhook_data)
        except Exception as e:
            logger.error(f"Payment webhook validation failed: {str(e)}")
            raise ValueError(f"Payment webhook validation failed: {str(e)}")
        
        try:
            # Update payment status based on webhook
            payment = self.payment_repo.update_payment(
                payment_id=validated_request.payment_id,
                payment_data={
                    "status": validated_request.status,
                    "gateway_response": validated_request.gateway_response
                }
            )
            
            if not payment:
                logger.error(f"Payment {validated_request.payment_id} not found for webhook processing")
                return None
            
            return payment
            
        except Exception as e:
            logger.error(f"Error processing webhook for payment {validated_request.payment_id}: {str(e)}", exc_info=True)
            return None


# =============================================================================
# Dependency Injection and Service Factories
# =============================================================================


def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides database sessions.
    This is the only place where FastAPI directly interacts with the database.
    """
    
    _session_provider = DatabaseSessionProvider()
    session = _session_provider.get_session()
    try:
        yield session
    finally:
        _session_provider.close_session(session)

# Application layer - service composition
def create_payment_service(db_session: Session) -> PaymentService:
    """
    Factory function to create PaymentService with all its dependencies.
    This is where we compose the hexagonal architecture.
    """
    
    # Infrastructure adapters (ports implementations)
    transaction_repo = DBTransactionRepository(db_session)
    payment_repo = DBPaymentRepository(db_session)
    
    # Domain service
    return PaymentService(
        transaction_repo=transaction_repo,
        payment_repo=payment_repo
    )

def create_transaction_service(db_session: Session) -> TransactionService:
    """
    Factory function to create TransactionService with all its dependencies.
    """
    
    # Infrastructure adapters
    transaction_repo = DBTransactionRepository(db_session)
    order_repo = DBOrderRepository(db_session)
    
    # Domain service
    return TransactionService(
        transaction_repo=transaction_repo,
        order_repo=order_repo
    )

def create_order_service(db_session: Session) -> OrderService:
    """
    Factory function to create OrderService with all its dependencies.
    """
    
    # Infrastructure adapters
    order_repo = DBOrderRepository(db_session)
    
    # Domain service
    return OrderService(
        order_repo=order_repo
    )




class RefundService:
    """Service for handling refund-related business logic.
    
    This service manages the refund process including validation, status updates,
    and integration with payment gateways.
    """
    
    def __init__(
        self,
        transaction_repo: DBTransactionRepository,
        refund_repo: DBRefundRepository,
        payment_repo: DBPaymentRepository
    ):
        self.transaction_repo = transaction_repo
        self.refund_repo = refund_repo
        self.payment_repo = payment_repo
    
    def create_refund(
        self,
        transaction_id: int,
        refund_request: "TransactionRefundRequest",
        processed_by: int
    ) -> Optional[Dict[str, Any]]:
        """Create a new refund for a transaction.
        
        Args:
            transaction_id: ID of the transaction to refund
            refund_request: Validated refund request data
            processed_by: ID of the admin processing the refund
            
        Returns:
            Dict containing refund details if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or refund cannot be processed
        """
        try:
            # Get the transaction
            transaction = self.transaction_repo.get_transaction(transaction_id)
            if not transaction:
                raise ValueError("Transaction not found")
                
            # Validate transaction status
            if transaction.status != TransactionStatus.COMPLETED:
                raise ValueError("Only completed transactions can be refunded")
                
            # Get the payment for this transaction
            payments = self.payment_repo.get_payments_by_transaction(transaction_id)
            if not payments:
                raise ValueError("No payment found for this transaction")
                
            payment = payments[0]  # Get the first payment (assuming one payment per transaction)
            
            # Calculate refund amount (default to full amount if not specified)
            refund_amount = refund_request.amount if refund_request.amount else transaction.amount
            
            if refund_amount <= 0:
                raise ValueError("Refund amount must be greater than 0")
                
            if refund_amount > transaction.amount:
                raise ValueError("Refund amount cannot exceed transaction amount")
                
            # Create refund record
            refund_data = {
                "transaction_id": transaction_id,
                "amount": refund_amount,
                "reason": refund_request.reason,
                "status": RefundStatus.PROCESSING,
                "processed_by": processed_by,
                "notes": refund_request.notes
            }
            
            refund = self.refund_repo.create_refund(RefundCreate(**refund_data))
            if not refund:
                raise ValueError("Failed to create refund record")
                
            # Update transaction status
            self.transaction_repo.update_transaction(
                transaction_id,
                TransactionUpdate(status=TransactionStatus.REFUNDED)
            )
            
            # Here you would typically integrate with payment gateway to process the refund
            # For example: payment_gateway.process_refund(payment.gateway_transaction_id, refund_amount)
            
            # Update refund status to completed
            refund = self.refund_repo.update_refund_status(
                refund_id=refund.id,
                status=RefundStatus.COMPLETED,
                processed_by=processed_by,
                notes="Refund processed successfully"
            )
            
            return {
                "refund_id": refund.id,
                "transaction_id": refund.transaction_id,
                "amount": refund.amount,
                "status": refund.status,
                "reason": refund.reason,
                "processed_at": refund.processed_at
            }
            
        except Exception as e:
            # Update refund status to failed if it was created
            if 'refund' in locals():
                self.refund_repo.update_refund_status(
                    refund_id=refund.id,
                    status=RefundStatus.FAILED,
                    processed_by=processed_by,
                    notes=f"Refund failed: {str(e)}"
                )
            raise ValueError(f"Failed to process refund: {str(e)}")
    
    def get_refund(self, refund_id: int) -> Optional[Dict[str, Any]]:
        """Get refund details by ID.
        
        Args:
            refund_id: ID of the refund to retrieve
            
        Returns:
            Dict containing refund details if found, None otherwise
        """
        refund = self.refund_repo.get_refund(refund_id)
        if not refund:
            return None
            
        return {
            "id": refund.id,
            "transaction_id": refund.transaction_id,
            "amount": refund.amount,
            "status": refund.status,
            "reason": refund.reason,
            "processed_by": refund.processed_by,
            "processed_at": refund.processed_at,
            "notes": refund.notes,
            "created_at": refund.created_at
        }
    
    def get_refunds_by_transaction(self, transaction_id: int) -> List[Dict[str, Any]]:
        """Get all refunds for a transaction.
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            List of refund details
        """
        refunds = self.refund_repo.get_refunds_by_transaction(transaction_id)
        return [
            {
                "id": refund.id,
                "amount": refund.amount,
                "status": refund.status,
                "reason": refund.reason,
                "processed_at": refund.processed_at,
                "created_at": refund.created_at
            }
            for refund in refunds
        ]

# =============================================================================
# REPORTS SERVICE
# =============================================================================
class ReportsService:
    """Service for handling reports and analytics operations"""
    
    def __init__(self, transaction_repo, refund_repo=None):
        self.transaction_repo = transaction_repo
        self.refund_repo = refund_repo
    
    def generate_transaction_report(self, report_request: "TransactionReportRequest") -> "TransactionReportResponse":
        """Generate transaction report with filters"""
        try:
            # Get transactions based on filters
            transactions = self.transaction_repo.get_transactions_for_report(
                start_date=report_request.date_range.start_date,
                end_date=report_request.date_range.end_date,
                status_filter=report_request.status_filter,
                transaction_type_filter=report_request.transaction_type,
                min_amount=report_request.min_amount,
                max_amount=report_request.max_amount,
                user_id=report_request.user_id,
                currency=report_request.currency
            )
            
            # Calculate summary statistics
            total_count = len(transactions)
            total_amount = sum(t.amount for t in transactions)
            status_breakdown = {}
            type_breakdown = {}
            
            for transaction in transactions:
                # Status breakdown
                status = transaction.status.value if hasattr(transaction.status, 'value') else str(transaction.status)
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                # Type breakdown
                trans_type = transaction.transaction_type.value if hasattr(transaction.transaction_type, 'value') else str(transaction.transaction_type)
                type_breakdown[trans_type] = type_breakdown.get(trans_type, 0) + 1
            
            summary = {
                "total_transactions": total_count,
                "total_amount": total_amount,
                "average_amount": total_amount / total_count if total_count > 0 else 0,
                "status_breakdown": status_breakdown,
                "type_breakdown": type_breakdown,
                "currency": report_request.currency
            }
            
            # Convert to response format
            transaction_data = [
                TransactionReportData(
                    transaction_id=t.id,
                    user_id=t.user_id,
                    order_id=t.order_id,
                    transaction_type=t.transaction_type,
                    amount=t.amount,
                    currency=t.currency,
                    status=t.status,
                    payment_method=t.payment_method,
                    payment_gateway=t.payment_gateway,
                    created_at=t.created_at,
                    updated_at=t.updated_at
                ) for t in transactions
            ]
            
            return TransactionReportResponse(
                summary=summary,
                transactions=transaction_data,
                total_count=total_count,
                total_amount=total_amount,
                date_range=report_request.date_range
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate transaction report: {str(e)}")
    
    def generate_revenue_report(self, report_request: "RevenueReportRequest") -> "RevenueReportResponse":
        """Generate revenue analytics report"""
        try:
            # Get revenue data grouped by period
            revenue_data = self.transaction_repo.get_revenue_data(
                start_date=report_request.date_range.start_date,
                end_date=report_request.date_range.end_date,
                group_by=report_request.group_by,
                currency=report_request.currency,
                service_type_filter=report_request.service_type_filter,
                include_refunds=report_request.include_refunds
            )
            
            # Calculate summary
            total_revenue = sum(point['revenue'] for point in revenue_data)
            total_transactions = sum(point['transaction_count'] for point in revenue_data)
            total_refunds = sum(point['refund_amount'] for point in revenue_data)
            
            summary = {
                "total_revenue": total_revenue,
                "total_transactions": total_transactions,
                "total_refunds": total_refunds,
                "net_revenue": total_revenue - total_refunds,
                "average_transaction_value": total_revenue / total_transactions if total_transactions > 0 else 0,
                "refund_rate": (total_refunds / total_revenue * 100) if total_revenue > 0 else 0,
                "currency": report_request.currency,
                "group_by": report_request.group_by
            }
            
            # Convert to response format
            data_points = [
                RevenueDataPoint(
                    period=point['period'],
                    revenue=point['revenue'],
                    transaction_count=point['transaction_count'],
                    refund_amount=point['refund_amount']
                ) for point in revenue_data
            ]
            
            return RevenueReportResponse(
                summary=summary,
                revenue_data=data_points,
                total_revenue=total_revenue,
                total_transactions=total_transactions,
                total_refunds=total_refunds,
                date_range=report_request.date_range
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate revenue report: {str(e)}")
    
    def generate_refund_report(self, report_request: "RefundReportRequest") -> "RefundReportResponse":
        """Generate refund report with filters"""
        try:
            # Get refunds based on filters
            refunds = self.refund_repo.get_refunds_for_report(
                start_date=report_request.date_range.start_date,
                end_date=report_request.date_range.end_date,
                status_filter=report_request.status_filter,
                min_amount=report_request.min_amount,
                max_amount=report_request.max_amount,
                reason_filter=report_request.reason_filter,
                processed_by=report_request.processed_by
            )
            
            # Calculate summary statistics
            total_count = len(refunds)
            total_amount = sum(r.amount for r in refunds)
            status_breakdown = {}
            reason_breakdown = {}
            
            for refund in refunds:
                # Status breakdown
                status = refund.status.value if hasattr(refund.status, 'value') else str(refund.status)
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                # Reason breakdown (extract main keyword)
                reason_key = refund.reason.split()[0].lower() if refund.reason else "unknown"
                reason_breakdown[reason_key] = reason_breakdown.get(reason_key, 0) + 1
            
            summary = {
                "total_refunds": total_count,
                "total_amount": total_amount,
                "average_amount": total_amount / total_count if total_count > 0 else 0,
                "status_breakdown": status_breakdown,
                "reason_breakdown": reason_breakdown
            }
            
            # Convert to response format
            refund_data = [
                RefundReportData(
                    refund_id=r.id,
                    transaction_id=r.transaction_id,
                    user_id=r.user_id if hasattr(r, 'user_id') else 0,  # Get from transaction if needed
                    amount=r.amount,
                    reason=r.reason,
                    status=r.status,
                    processed_by=r.processed_by,
                    processed_at=r.processed_at,
                    created_at=r.created_at
                ) for r in refunds
            ]
            
            return RefundReportResponse(
                summary=summary,
                refunds=refund_data,
                total_count=total_count,
                total_amount=total_amount,
                date_range=report_request.date_range
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate refund report: {str(e)}")


# Service factory for reports
def get_refund_service(db: Session = Depends(get_database_session)) -> RefundService:
    """Factory function to create RefundService with all its dependencies"""
    transaction_repo = DBTransactionRepository(db)
    refund_repo = DBRefundRepository(db)
    payment_repo = DBPaymentRepository(db)
    return RefundService(transaction_repo, refund_repo, payment_repo)


def get_reports_service(db: Session = Depends(get_database_session)) -> ReportsService:
    """Factory function to create ReportsService with proper dependencies"""
    transaction_repo = DBTransactionRepository(db)
    refund_repo = DBRefundRepository(db)
    return ReportsService(transaction_repo, refund_repo)


# AUTH SERVICE
SECRET_KEY = os.getenv("JWT_SECRET", "secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def get_current_user(authorization: Optional[str] = Header(None)) -> UserResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_info = get_user_info(authorization)
    return UserResponse(**user_info)


def require_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


def require_user_or_admin(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    if current_user.role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User or admin access required",
        )
    return current_user
