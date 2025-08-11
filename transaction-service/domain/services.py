from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone
import logging

from domain.models import (
    TransactionInDB, TransactionCreate, TransactionUpdate, TransactionStatus, TransactionType,
    OrderInDB, OrderCreate, OrderUpdate, OrderStatus, ServiceType,
    PaymentInDB, PaymentCreate, PaymentStatus, PaymentMethod, PaymentGateway,
    RefundInDB, RefundCreate, RefundStatus, Currency,
    # Payment request models
    PaymentCreateRequest, PaymentConfirmRequest, PaymentRefundRequest, PaymentWebhookRequest,
    # Order request models
    OrderCreateRequest, OrderStatusUpdateRequest,
    # Transaction request models
    TransactionCreateRequest, TransactionUpdateRequest, TransactionRefundRequest
)

from adapters.db import (
    DBTransactionRepository, DBOrderRepository, 
    DBPaymentRepository, DBRefundRepository
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
            
            # Create order first
            order_data = {
                'user_id': user_id,
                'order_number': order_number,
                'service_type': transaction_request.service_type,
                'items': transaction_request.items,
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
        payment_data: Dict[str, Any],
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
        gateway_response: Dict[str, Any],
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


# class RefundService:
#     """Service for handling refund-related business logic.
    
#     This service manages the refund process including request, approval,
#     and processing while ensuring data consistency.
#     """
    
#     def __init__(
#         self, 
#         transaction_repo: DBTransactionRepository,
#         order_repo: DBOrderRepository,
#         refund_repo: DBRefundRepository,
#     ):
#         self.transaction_repo = transaction_repo
#         self.order_repo = order_repo
#         self.refund_repo = refund_repo
    
#     def request_refund(
#         self, 
#         transaction_id: int, 
#         amount: float,
#         reason: str,
#         user_id: int,
#         **metadata
#     ) -> Optional[RefundInDB]:
#         """Request a refund for a transaction.
        
#         Args:
#             transaction_id: ID of the transaction to refund
#             amount: Amount to refund (must be <= transaction amount)
#             reason: Reason for the refund
#             user_id: ID of the user requesting the refund
#             **metadata: Additional metadata for the refund
            
#         Returns:
#             RefundInDB if successful, None otherwise
#         """
#         try:
#             # Get and validate transaction
#             transaction = self.transaction_repo.get_transaction(transaction_id)
#             if not transaction or transaction.user_id != user_id:
#                 logger.error(f"Transaction {transaction_id} not found or unauthorized")
#                 return None
                
#             # Check if transaction is refundable
#             if transaction.status != TransactionStatus.COMPLETED:
#                 logger.error(f"Transaction {transaction_id} is not in a refundable state")
#                 return None
                
#             # Validate amount
#             if amount <= 0 or amount > transaction.amount:
#                 logger.error(f"Invalid refund amount {amount} for transaction {transaction_id}")
#                 return None
                
#             # Check for existing pending refunds
#             existing_refunds = self.refund_repo.get_refunds_by_transaction(transaction_id)
#             if any(refund.status == RefundStatus.PENDING for refund in existing_refunds):
#                 logger.warning(f"Transaction {transaction_id} already has a pending refund")
#                 return None
                
#             # Create refund request
#             refund = RefundCreate(
#                 transaction_id=transaction_id,
#                 amount=amount,
#                 reason=reason,
#                 status=RefundStatus.PENDING,
#                 metadata={
#                     'requested_by': user_id,
#                     'requested_at': datetime.utcnow().isoformat(),
#                     **metadata
#                 }
#             )
            
#             # Save refund to database
#             db_refund = self.refund_repo.create_refund(refund)
#             if not db_refund:
#                 logger.error(f"Failed to create refund for transaction {transaction_id}")
#                 return None
                
#             # Update transaction status
#             self.transaction_repo.update_transaction(
#                 transaction_id=transaction_id,
#                 transaction=TransactionUpdate(
#                     status=TransactionStatus.REFUND_PENDING,
#                     metadata={
#                         **transaction.metadata,
#                         'refund_requested_at': datetime.utcnow().isoformat(),
#                         'refund_requested_by': user_id,
#                         'refund_reason': reason
#                     }
#                 )
#             )
            
#             return db_refund
            
#         except Exception as e:
#             logger.error(f"Error requesting refund for transaction {transaction_id}: {str(e)}", exc_info=True)
#             return None
    
#     def process_refund(
#         self, 
#         refund_id: int, 
#         action: str, 
#         processed_by: int,
#         notes: Optional[str] = None,
#         **metadata
#     ) -> Optional[RefundInDB]:
#         """Process a refund request (approve/reject).
        
#         Args:
#             refund_id: ID of the refund to process
#             action: Action to take ('approve' or 'reject')
#             processed_by: ID of the user processing the refund
#             notes: Optional notes about the processing
#             **metadata: Additional metadata for the refund
            
#         Returns:
#             Updated RefundInDB if successful, None otherwise
#         """
#         try:
#             # Get and validate refund
#             refund = self.refund_repo.get_refund(refund_id)
#             if not refund:
#                 logger.error(f"Refund {refund_id} not found")
#                 return None
                
#             # Check if refund is in a processable state
#             if refund.status != RefundStatus.PENDING:
#                 logger.warning(f"Refund {refund_id} is not in a processable state")
#                 return None
                
#             # Get transaction
#             transaction = self.transaction_repo.get_transaction(refund.transaction_id)
#             if not transaction:
#                 logger.error(f"Transaction {refund.transaction_id} not found for refund {refund_id}")
#                 return None
                
#             # Determine new status based on action
#             action = action.lower()
#             if action == 'approve':
#                 new_status = RefundStatus.COMPLETED
#                 transaction_status = TransactionStatus.REFUNDED
#             elif action == 'reject':
#                 new_status = RefundStatus.REJECTED
#                 transaction_status = transaction.status
#             else:
#                 logger.error(f"Invalid action '{action}' for refund {refund_id}")
#                 return None
            
#             # Update refund record
#             updated_refund = self.refund_repo.update_refund_status(
#                 refund_id=refund_id,
#                 status=new_status,
#                 processed_by=processed_by,
#                 processed_at=datetime.utcnow(),
#                 notes=notes,
#                 metadata={
#                     **refund.metadata,
#                     'processed_at': datetime.utcnow().isoformat(),
#                     'processed_by': processed_by,
#                     'notes': notes,
#                     **metadata
#                 }
#             )
            
#             if not updated_refund:
#                 logger.error(f"Failed to update refund {refund_id}")
#                 return None
            
#             # Update transaction status if refund was approved
#             if new_status == RefundStatus.COMPLETED:
#                 self.transaction_repo.update_transaction(
#                     transaction_id=transaction.id,
#                     transaction=TransactionUpdate(
#                         status=transaction_status,
#                         metadata={
#                             **transaction.metadata,
#                             'refund_processed_at': datetime.utcnow().isoformat(),
#                             'refund_processed_by': processed_by,
#                             'refund_notes': notes
#                         }
#                     )
#                 )
            
#             return updated_refund
            
#         except Exception as e:
#             logger.error(f"Error processing refund {refund_id}: {str(e)}", exc_info=True)
#             return None


# =============================================================================
# Dependency Injection and Service Factories
# =============================================================================

from functools import lru_cache
from typing import Generator
from sqlalchemy.orm import Session

def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides database sessions.
    This is the only place where FastAPI directly interacts with the database.
    """
    from adapters.db import DatabaseSessionProvider
    
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
    from adapters.db import DBPaymentRepository, DBTransactionRepository
    
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
    from adapters.db import DBTransactionRepository, DBOrderRepository
    
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
    from adapters.db import DBOrderRepository
    
    # Infrastructure adapters
    order_repo = DBOrderRepository(db_session)
    
    # Domain service
    return OrderService(
        order_repo=order_repo
    )

# Authentication service placeholder
@lru_cache()
def get_auth_service():
    """
    TODO: Implement proper authentication service
    This should return the actual auth service that validates tokens
    """
    class MockAuthService:
        def get_current_user(self):
            return {"id": 1, "role": "admin"}
    
    return MockAuthService()