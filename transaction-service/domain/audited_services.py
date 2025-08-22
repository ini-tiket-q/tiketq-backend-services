"""
Enhanced Transaction Services with Audit Logging

This module extends the existing transaction services to include comprehensive
audit logging for all database operations, following the established business
logic patterns and architecture.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from domain.models import (
    TransactionInDB, TransactionCreate, TransactionUpdate, TransactionStatus,
    OrderInDB, OrderCreate, OrderUpdate, OrderStatus,
    PaymentInDB, PaymentCreate, PaymentStatus,
    RefundInDB, RefundCreate, RefundStatus,
    UserResponse,
    # Request models
    TransactionCreateRequest, TransactionUpdateRequest, TransactionRefundRequest,
    OrderCreateRequest, OrderStatusUpdateRequest,
    PaymentCreateRequest, PaymentConfirmRequest, PaymentRefundRequest,
)
from domain.repository import (
    TransactionRepository, OrderRepository, 
    PaymentRepository, RefundRepository
)
from domain.audit_service import get_audit_service, AuditService
from domain.services import logger


class AuditedTransactionService:
    """
    Enhanced TransactionService with comprehensive audit logging.
    
    This service wraps all transaction operations with audit logging while
    maintaining the same interface as the original TransactionService.
    """
    
    def __init__(
        self, 
        transaction_repo: TransactionRepository,
        order_repo: OrderRepository,
        audit_service: Optional[AuditService] = None
    ):
        self.transaction_repo = transaction_repo
        self.order_repo = order_repo
        self.audit_service = audit_service or get_audit_service()
    
    def create_transaction(
        self, 
        transaction_request: TransactionCreateRequest, 
        user: UserResponse
    ) -> Optional[TransactionInDB]:
        """Create a new transaction with comprehensive audit logging"""
        try:
            # Log the attempt
            logger.info(f"Creating transaction for user {user.id} with type {transaction_request.transaction_type}")
            
            # Generate order number
            from uuid import uuid4
            order_number = f"ORD-{str(uuid4())[:8].upper()}"
            
            # Convert TransactionItem objects to dictionaries
            items_as_dicts = [
                item.model_dump() if hasattr(item, 'model_dump') else dict(item)
                for item in transaction_request.items
            ]
            
            # Create order first with audit logging
            order_data = {
                'user_id': user.id,
                'order_number': order_number,
                'service_type': transaction_request.service_type,
                'items': items_as_dicts,
                'subtotal': transaction_request.subtotal or sum(
                    item.price * item.quantity for item in transaction_request.items
                ),
                'tax': transaction_request.tax,
                'discount': transaction_request.discount,
                'total': transaction_request.total,
                'status': OrderStatus.DRAFT,
                'metadata': transaction_request.metadata
            }
            
            order = self.order_repo.create_order(OrderCreate(**order_data))
            if not order:
                logger.error("Failed to create order")
                return None
            
            # Log order creation
            self.audit_service.log_order_created(
                order=order,
                user=user,
                context={
                    "creation_method": "transaction_creation",
                    "items_count": len(transaction_request.items)
                }
            )
            
            # Create transaction
            transaction = TransactionCreate(
                user_id=user.id,
                order_id=order.order_number,
                transaction_type=transaction_request.transaction_type,
                amount=transaction_request.amount,
                currency=transaction_request.currency,
                status=TransactionStatus.PENDING,
                payment_method=transaction_request.payment_method,
                payment_gateway=transaction_request.payment_gateway,
                gateway_transaction_id=None,
                metadata=transaction_request.metadata
            )
            
            db_transaction = self.transaction_repo.create_transaction(transaction)
            if not db_transaction:
                logger.error("Failed to create transaction")
                return None
            
            # Log transaction creation with business context
            self.audit_service.log_transaction_created(
                transaction=db_transaction,
                user=user,
                context={
                    "creation_method": "user_initiated",
                    "order_number": order.order_number,
                    "service_type": transaction_request.service_type.value,
                    "item_count": len(transaction_request.items)
                }
            )
            
            logger.info(f"Successfully created transaction {db_transaction.id} for user {user.id}")
            return db_transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}", exc_info=True)
            
            # Log the error as suspicious activity if it's unexpected
            self.audit_service.log_suspicious_activity(
                entity_type="transaction",
                entity_id=0,  # No transaction ID yet
                activity_description=f"Transaction creation failed: {str(e)}",
                user=user,
                context={"error_type": type(e).__name__}
            )
            return None
    
    def get_transaction(
        self, 
        transaction_id: int, 
        user: UserResponse
    ) -> Optional[TransactionInDB]:
        """Get a transaction with access logging"""
        try:
            transaction = self.transaction_repo.get_transaction(transaction_id)
            
            if not transaction:
                # Log access attempt to non-existent transaction
                self.audit_service.log_suspicious_activity(
                    entity_type="transaction",
                    entity_id=transaction_id,
                    activity_description="Attempted access to non-existent transaction",
                    user=user,
                    context={"access_denied": True}
                )
                return None
            
            # Check authorization
            if user.role.value != "admin" and transaction.user_id != user.id:
                # Log unauthorized access attempt
                self.audit_service.log_suspicious_activity(
                    entity_type="transaction",
                    entity_id=transaction_id,
                    activity_description="Unauthorized transaction access attempt",
                    user=user,
                    context={
                        "transaction_owner": transaction.user_id,
                        "access_denied": True
                    }
                )
                return None
            
            # Log successful access (only for admin or when accessing other user's data)
            if user.role.value == "admin" and transaction.user_id != user.id:
                metadata = {
                    "admin_access": True,
                    "transaction_owner": transaction.user_id,
                    "access_reason": "admin_review"
                }
                
                self.audit_service.audit_logger.log_transaction_event(
                    transaction=transaction,
                    action=self.audit_service.audit_logger.AuditAction.UPDATE,  # Using UPDATE as "ACCESS" action
                    level=self.audit_service.audit_logger.AuditLevel.INFO,
                    user_id=user.id,
                    user_role=user.role,
                    metadata=metadata
                )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            return None
    
    def update_transaction(
        self, 
        transaction_id: int, 
        update_request: TransactionUpdateRequest,
        user: UserResponse
    ) -> Optional[TransactionInDB]:
        """Update transaction with comprehensive change tracking"""
        try:
            # Get the current transaction for comparison
            current_transaction = self.transaction_repo.get_transaction(transaction_id)
            if not current_transaction:
                return None
            
            # Authorization check
            if user.role.value != "admin" and current_transaction.user_id != user.id:
                self.audit_service.log_suspicious_activity(
                    entity_type="transaction",
                    entity_id=transaction_id,
                    activity_description="Unauthorized transaction update attempt",
                    user=user,
                    context={
                        "transaction_owner": current_transaction.user_id,
                        "update_denied": True
                    }
                )
                return None
            
            # Capture old values for audit
            old_values = {
                "status": current_transaction.status.value,
                "payment_method": current_transaction.payment_method.value if current_transaction.payment_method else None,
                "payment_gateway": current_transaction.payment_gateway.value if current_transaction.payment_gateway else None,
                "gateway_transaction_id": current_transaction.gateway_transaction_id,
                "metadata": current_transaction.metadata
            }
            
            # Prepare update data
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
            
            # Perform the update
            updated_transaction = self.transaction_repo.update_transaction(
                transaction_id, transaction_update
            )
            
            if not updated_transaction:
                logger.error(f"Failed to update transaction {transaction_id}")
                return None
            
            # Prepare new values for audit
            new_values = {
                "status": updated_transaction.status.value,
                "payment_method": updated_transaction.payment_method.value if updated_transaction.payment_method else None,
                "payment_gateway": updated_transaction.payment_gateway.value if updated_transaction.payment_gateway else None,
                "gateway_transaction_id": updated_transaction.gateway_transaction_id,
                "metadata": updated_transaction.metadata
            }
            
            # Log the update with detailed change tracking
            changes = {
                "old_values": old_values,
                "new_values": new_values
            }
            
            self.audit_service.log_transaction_updated(
                transaction=updated_transaction,
                changes=changes,
                user=user,
                context={
                    "update_method": "user_initiated" if user.role.value != "admin" else "admin_update",
                    "fields_changed": list(update_data.keys())
                }
            )
            
            # Special logging for status changes
            if (old_values["status"] != new_values["status"] and 
                update_request.status is not None):
                self.audit_service.log_transaction_status_change(
                    transaction=updated_transaction,
                    old_status=current_transaction.status,
                    new_status=update_request.status,
                    user=user,
                    context={
                        "status_change_reason": update_request.metadata.get("status_change_reason") if update_request.metadata else None
                    }
                )
            
            logger.info(f"Successfully updated transaction {transaction_id}")
            return updated_transaction
            
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
            return None
    
    def get_transactions_by_user(
        self, 
        user: UserResponse, 
        status: Optional[TransactionStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionInDB]:
        """Get user transactions with access logging for admin queries"""
        try:
            # If admin is querying another user's transactions, log it
            if user.role.value == "admin":
                # This would need additional context to know if it's for another user
                # For now, we'll log admin list access
                metadata = {
                    "admin_list_access": True,
                    "query_parameters": {
                        "status": status.value if status else None,
                        "skip": skip,
                        "limit": limit
                    }
                }
                
                from domain.audit_logger import AuditLogEntry, AuditAction, AuditLevel
                entry = AuditLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    entity_type="transaction",
                    entity_id=0,  # Bulk query
                    action=AuditAction.UPDATE,  # Using UPDATE as "LIST" action
                    level=AuditLevel.INFO,
                    user_id=user.id,
                    user_role=user.role,
                    changes={},
                    metadata=metadata
                )
                
                if hasattr(self.audit_service.audit_logger, '_log_entry'):
                    self.audit_service.audit_logger._log_entry(entry)
            
            return self.transaction_repo.get_transactions_by_user(
                user_id=user.id,
                status=status,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error retrieving transactions for user {user.id}: {str(e)}")
            return []
    
    def cancel_transaction(
        self, 
        transaction_id: int, 
        user: UserResponse,
        reason: Optional[str] = None
    ) -> Optional[TransactionInDB]:
        """Cancel a transaction with audit logging"""
        try:
            # Get current transaction
            current_transaction = self.transaction_repo.get_transaction(transaction_id)
            if not current_transaction:
                return None
            
            # Authorization check
            if user.role.value != "admin" and current_transaction.user_id != user.id:
                self.audit_service.log_suspicious_activity(
                    entity_type="transaction",
                    entity_id=transaction_id,
                    activity_description="Unauthorized transaction cancellation attempt",
                    user=user,
                    context={
                        "transaction_owner": current_transaction.user_id,
                        "cancellation_denied": True
                    }
                )
                return None
            
            # Check if transaction can be cancelled
            if current_transaction.status not in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]:
                logger.warning(f"Cannot cancel transaction {transaction_id} with status {current_transaction.status}")
                return None
            
            # Cancel the transaction
            cancel_request = TransactionUpdateRequest(
                status=TransactionStatus.CANCELLED,
                metadata={
                    **(current_transaction.metadata or {}),
                    "cancellation_reason": reason,
                    "cancelled_by": user.id,
                    "cancelled_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            cancelled_transaction = self.update_transaction(
                transaction_id, cancel_request, user
            )
            
            if cancelled_transaction:
                # Log the cancellation as a business event
                self.audit_service.log_transaction_status_change(
                    transaction=cancelled_transaction,
                    old_status=current_transaction.status,
                    new_status=TransactionStatus.CANCELLED,
                    user=user,
                    reason=reason,
                    context={
                        "cancellation_method": "user_requested" if user.id == current_transaction.user_id else "admin_cancelled"
                    }
                )
                
                logger.info(f"Transaction {transaction_id} cancelled by user {user.id}")
            
            return cancelled_transaction
            
        except Exception as e:
            logger.error(f"Error cancelling transaction {transaction_id}: {str(e)}")
            return None


class AuditedOrderService:
    """
    Enhanced OrderService with comprehensive audit logging.
    """
    
    def __init__(
        self, 
        order_repo: OrderRepository,
        audit_service: Optional[AuditService] = None
    ):
        self.order_repo = order_repo
        self.audit_service = audit_service or get_audit_service()
    
    def update_order_status(
        self, 
        order_id: int, 
        status_request: OrderStatusUpdateRequest,
        user: UserResponse
    ) -> Optional[OrderInDB]:
        """Update order status with comprehensive audit logging"""
        try:
            # Get current order
            current_order = self.order_repo.get_order(order_id)
            if not current_order:
                return None
            
            # Authorization check
            if user.role.value != "admin" and current_order.user_id != user.id:
                self.audit_service.log_suspicious_activity(
                    entity_type="order",
                    entity_id=order_id,
                    activity_description="Unauthorized order status update attempt",
                    user=user,
                    context={
                        "order_owner": current_order.user_id,
                        "update_denied": True
                    }
                )
                return None
            
            old_status = current_order.status
            
            # Perform the update
            update_data = {
                "status": status_request.status
            }
            
            if status_request.metadata is not None:
                update_data["metadata"] = status_request.metadata
            
            updated_order = self.order_repo.update_order(
                order_id, OrderUpdate(**update_data)
            )
            
            if not updated_order:
                logger.error(f"Failed to update order {order_id}")
                return None
            
            # Log the status change
            self.audit_service.log_order_status_change(
                order=updated_order,
                old_status=old_status,
                new_status=status_request.status,
                user=user,
                context={
                    "update_method": "status_update_request",
                    "metadata_updated": status_request.metadata is not None
                }
            )
            
            logger.info(f"Successfully updated order {order_id} status to {status_request.status}")
            return updated_order
            
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
            return None


class AuditedPaymentService:
    """
    Enhanced PaymentService with comprehensive audit logging.
    """
    
    def __init__(
        self, 
        transaction_repo: TransactionRepository,
        payment_repo: PaymentRepository,
        audit_service: Optional[AuditService] = None
    ):
        self.transaction_repo = transaction_repo
        self.payment_repo = payment_repo
        self.audit_service = audit_service or get_audit_service()
    
    def create_payment(
        self, 
        transaction_id: int,
        payment_data: PaymentCreateRequest,
        user: UserResponse
    ) -> Optional[PaymentInDB]:
        """Create payment with comprehensive audit logging"""
        try:
            # Get and validate transaction
            transaction = self.transaction_repo.get_transaction(transaction_id)
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return None
            
            # Authorization check
            if user.role.value != "admin" and transaction.user_id != user.id:
                self.audit_service.log_suspicious_activity(
                    entity_type="payment",
                    entity_id=0,  # No payment ID yet
                    activity_description="Unauthorized payment creation attempt",
                    user=user,
                    context={
                        "transaction_id": transaction_id,
                        "transaction_owner": transaction.user_id,
                        "payment_denied": True
                    }
                )
                return None
            
            # Create payment record
            payment = PaymentCreate(
                transaction_id=transaction_id,
                amount=payment_data.amount,
                currency=payment_data.currency,
                payment_method=payment_data.payment_method,
                payment_gateway=payment_data.payment_gateway,
                gateway_transaction_id=payment_data.gateway_transaction_id,
                status=PaymentStatus.PENDING,
                metadata=payment_data.metadata or {}
            )
            
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
            
            # Log payment initiation
            self.audit_service.log_payment_initiated(
                payment=db_payment,
                user=user,
                context={
                    "transaction_id": transaction_id,
                    "payment_amount": float(payment_data.amount),
                    "gateway": payment_data.payment_gateway.value,
                    "method": payment_data.payment_method.value
                }
            )
            
            logger.info(f"Successfully created payment {db_payment.id} for transaction {transaction_id}")
            return db_payment
            
        except Exception as e:
            logger.error(f"Error creating payment for transaction {transaction_id}: {str(e)}")
            return None
    
    def confirm_payment(
        self, 
        payment_id: int, 
        gateway_response: PaymentConfirmRequest,
        user: UserResponse
    ) -> Optional[PaymentInDB]:
        """Confirm payment with comprehensive audit logging"""
        try:
            payment = self.payment_repo.get_payment(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return None
            
            old_status = payment.status
            success = gateway_response.gateway_response.get('success', False)
            new_status = PaymentStatus.COMPLETED if success else PaymentStatus.FAILED
            
            # Update payment status
            updated_payment = self.payment_repo.update_payment_status(
                payment_id=payment_id,
                status=new_status,
                gateway_transaction_id=gateway_response.gateway_response.get('transaction_id')
            )
            
            if not updated_payment:
                logger.error(f"Failed to update payment {payment_id}")
                return None
            
            # Update transaction status
            transaction_status = (
                TransactionStatus.COMPLETED if success else TransactionStatus.FAILED
            )
            
            self.transaction_repo.update_transaction(
                transaction_id=payment.transaction_id,
                transaction=TransactionUpdate(
                    status=transaction_status,
                    gateway_transaction_id=gateway_response.gateway_response.get('transaction_id'),
                    metadata={
                        'gateway_response': gateway_response.gateway_response,
                        'confirmed_by': user.id,
                        'confirmed_at': datetime.now(timezone.utc).isoformat()
                    }
                )
            )
            
            # Log payment confirmation
            self.audit_service.log_payment_status_change(
                payment=updated_payment,
                old_status=old_status,
                new_status=new_status,
                user=user,
                gateway_response=gateway_response.gateway_response,
                context={
                    "confirmation_successful": success,
                    "gateway_transaction_id": gateway_response.gateway_response.get('transaction_id'),
                    "confirmation_method": "manual" if user else "automatic"
                }
            )
            
            logger.info(f"Payment {payment_id} confirmed with status {new_status}")
            return updated_payment
            
        except Exception as e:
            logger.error(f"Error confirming payment {payment_id}: {str(e)}")
            return None


class AuditedRefundService:
    """
    Enhanced RefundService with comprehensive audit logging.
    """
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        refund_repo: RefundRepository,
        payment_repo: PaymentRepository,
        audit_service: Optional[AuditService] = None
    ):
        self.transaction_repo = transaction_repo
        self.refund_repo = refund_repo
        self.payment_repo = payment_repo
        self.audit_service = audit_service or get_audit_service()
    
    def create_refund(
        self,
        transaction_id: int,
        refund_request: TransactionRefundRequest,
        user: UserResponse  # Must be admin for refunds
    ) -> Optional[Dict[str, Any]]:
        """Create refund with comprehensive audit logging"""
        try:
            # Only admins can process refunds
            if user.role.value != "admin":
                self.audit_service.log_suspicious_activity(
                    entity_type="refund",
                    entity_id=0,
                    activity_description="Unauthorized refund creation attempt by non-admin",
                    user=user,
                    context={
                        "transaction_id": transaction_id,
                        "refund_denied": True,
                        "required_role": "admin"
                    }
                )
                return None
            
            # Get the transaction
            transaction = self.transaction_repo.get_transaction(transaction_id)
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return None
            
            # Validate transaction status
            if transaction.status != TransactionStatus.COMPLETED:
                logger.warning(f"Cannot refund transaction {transaction_id} with status {transaction.status}")
                return None
            
            # Calculate refund amount
            refund_amount = refund_request.amount or transaction.amount
            
            if refund_amount <= 0 or refund_amount > transaction.amount:
                logger.error(f"Invalid refund amount {refund_amount} for transaction {transaction_id}")
                return None
            
            # Create refund record
            refund_data = {
                "transaction_id": transaction_id,
                "amount": refund_amount,
                "reason": refund_request.reason,
                "status": RefundStatus.PROCESSING,
                "processed_by": user.id,
                "processed_at": datetime.now(timezone.utc),
                "notes": refund_request.notes
            }
            
            refund = self.refund_repo.create_refund(RefundCreate(**refund_data))
            if not refund:
                logger.error(f"Failed to create refund for transaction {transaction_id}")
                return None
            
            # Log refund request
            self.audit_service.log_refund_requested(
                refund=refund,
                requester=user,
                reason=refund_request.reason,
                context={
                    "refund_amount": float(refund_amount),
                    "full_refund": refund_amount == transaction.amount,
                    "original_transaction_amount": float(transaction.amount)
                }
            )
            
            # Update transaction status
            self.transaction_repo.update_transaction(
                transaction_id,
                TransactionUpdate(status=TransactionStatus.REFUNDED)
            )
            
            # Process refund (simplified - in reality would integrate with payment gateway)
            success = True  # Simulate successful processing
            
            if success:
                # Update refund status to completed
                self.refund_repo.update_refund_status(
                    refund_id=refund.id,
                    status=RefundStatus.COMPLETED,
                    processed_by=user.id,
                    notes="Refund processed successfully"
                )
                
                # Log successful refund processing
                self.audit_service.log_refund_processed(
                    refund=refund,
                    processor=user,
                    success=True,
                    context={
                        "processing_time_seconds": 1,  # Simulated
                        "gateway_response": {"success": True, "refund_id": f"REF-{refund.id}"}
                    }
                )
            else:
                # Update refund status to failed
                self.refund_repo.update_refund_status(
                    refund_id=refund.id,
                    status=RefundStatus.FAILED,
                    processed_by=user.id,
                    notes="Refund processing failed"
                )
                
                # Log failed refund processing
                self.audit_service.log_refund_processed(
                    refund=refund,
                    processor=user,
                    success=False,
                    error_message="Gateway processing failed",
                    context={
                        "failure_reason": "gateway_error"
                    }
                )
            
            final_refund = self.refund_repo.get_refund(refund.id)
            
            return {
                "refund_id": final_refund.id,
                "transaction_id": final_refund.transaction_id,
                "amount": final_refund.amount,
                "status": final_refund.status,
                "reason": final_refund.reason,
                "processed_at": final_refund.processed_at
            }
            
        except Exception as e:
            logger.error(f"Error creating refund for transaction {transaction_id}: {str(e)}")
            
            # Log error as suspicious activity
            self.audit_service.log_suspicious_activity(
                entity_type="refund",
                entity_id=transaction_id,
                activity_description=f"Refund creation failed: {str(e)}",
                user=user,
                context={
                    "error_type": type(e).__name__,
                    "transaction_id": transaction_id
                }
            )
            return None
