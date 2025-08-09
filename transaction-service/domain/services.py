from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone
import logging

from .models import (
    TransactionInDB, TransactionCreate, TransactionUpdate, TransactionStatus, TransactionType,
    OrderInDB, OrderCreate, OrderUpdate, OrderStatus, ServiceType,
    PaymentInDB, PaymentCreate, PaymentStatus, PaymentMethod, PaymentGateway,
    RefundInDB, RefundCreate, RefundStatus, Currency
)

from ..adapters.db import (
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
    
    def create_transaction(self, transaction_data: Dict[str, Any], user_id: int) -> Optional[TransactionInDB]:
        """Create a new transaction with associated order.
        
        Args:
            transaction_data: Dictionary containing transaction details
            user_id: ID of the user creating the transaction
            
        Returns:
            TransactionInDB if successful, None otherwise
        """
        try:
            # Generate order number if not provided
            order_number = transaction_data.get('order_number') or f"ORD-{str(uuid4())[:8].upper()}"
            
            # Calculate totals if not provided
            subtotal = float(transaction_data.get('subtotal', transaction_data['amount']))
            tax = float(transaction_data.get('tax', 0.0))
            discount = float(transaction_data.get('discount', 0.0))
            total = float(transaction_data.get('total', subtotal + tax - discount))
            
            # Create order first
            order_data = {
                'user_id': user_id,
                'order_number': order_number,
                'service_type': ServiceType(transaction_data['service_type']),
                'items': transaction_data['items'],
                'subtotal': subtotal,
                'tax': tax,
                'discount': discount,
                'total': total,
                'status': OrderStatus.DRAFT,
                'metadata': transaction_data.get('metadata', {})
            }
            
            order = self.order_repo.create_order(OrderCreate(**order_data))
            if not order:
                logger.error("Failed to create order")
                return None
            
            # Create transaction
            transaction = TransactionCreate(
                user_id=user_id,
                order_id=order.order_number,
                transaction_type=TransactionType(transaction_data.get('transaction_type', 'BOOKING')),
                amount=total,
                currency=Currency(transaction_data.get('currency', 'IDR')),
                status=TransactionStatus.PENDING,
                payment_method=PaymentMethod(transaction_data['payment_method']) if 'payment_method' in transaction_data else None,
                payment_gateway=PaymentGateway(transaction_data['payment_gateway']) if 'payment_gateway' in transaction_data else None,
                gateway_transaction_id=transaction_data.get('gateway_transaction_id', None),
                metadata=transaction_data.get('metadata', {})
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
    
    def update_transaction(
        self, 
        transaction_id: int, 
        transaction: Dict[str, Any],
        user_id: int,  
    ) -> Optional[TransactionInDB]:
        """Update transaction status with authorization check and additional data.
        
        Args:
            transaction_id: ID of the transaction to update
            status: New status for the transaction
            user_id: Optional user ID for authorization
            **update_data: Additional fields to update
            
        Returns:
            Updated TransactionInDB if successful, None otherwise
        """
        try:
            transaction_check = self.transaction_repo.get_transaction(transaction_id)
            if not transaction_check or transaction_check.user_id != user_id:
                return None

            transaction_update = TransactionUpdate(**transaction)
                
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
    
    def update_order_status(
        self, 
        order_id: int, 
        order: Dict[str, Any],
        user_id: int
    ) -> Optional[OrderInDB]:
        """Update order status with optional authorization check.
        
        Args:
            order_id: ID of the order to update
            status: New status for the order
            user_id: Optional user ID for authorization
            **update_data: Additional fields to update
            
        Returns:
            Updated OrderInDB if successful, None otherwise
        """
        try:
            order_check = self.order_repo.get_order(order_id)
            if not order_check or order_check.user_id != user_id:
                return None
                
            # Create update data
            update_order = OrderUpdate(**order)
            
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
        """
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
            
            # Create payment record
            payment = PaymentCreate(
                transaction_id=transaction_id,
                amount=float(payment_data.get('amount', transaction.amount)),
                currency=Currency(payment_data.get('currency', transaction.currency)),
                payment_method=PaymentMethod(payment_data['payment_method']),
                payment_gateway=PaymentGateway(payment_data['payment_gateway']),
                gateway_transaction_id=payment_data.get('gateway_transaction_id'),
                status=PaymentStatus.PENDING,
                metadata=payment_data.get('metadata', {})
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
        """
        try:
            # Get payment with transaction
            payment = self.payment_repo.get_payment(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return None
                
            # Update payment status
            status = PaymentStatus.COMPLETED if gateway_response.get('success', False) else PaymentStatus.FAILED
            
            # Update payment record
            updated_payment = self.payment_repo.update_payment_status(
                payment_id=payment_id,
                status=status,
                gateway_transaction_id=gateway_response.get('transaction_id')
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
                    gateway_transaction_id=gateway_response.get('transaction_id'),
                    metadata={
                        **payment.transaction.metadata,
                        'gateway_response': gateway_response,
                        'confirmed_by': confirmed_by,
                        'confirmed_at': datetime.utcnow().isoformat()
                    }
                )
            )
            
            return updated_payment
            
        except Exception as e:
            logger.error(f"Error confirming payment {payment_id}: {str(e)}", exc_info=True)
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