"""
Business-focused audit service for transaction operations.

This service provides high-level audit logging methods that understand
the business context of transactions, orders, payments, and refunds.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from domain.models import (
    TransactionInDB, OrderInDB, PaymentInDB, RefundInDB,
    UserResponse, TransactionStatus, OrderStatus, PaymentStatus, RefundStatus
)
from domain.audit_logger import get_audit_logger, AuditLogger, AuditLogEntry, AuditAction, AuditLevel


# Global audit service instance
_audit_service: Optional['AuditService'] = None


def initialize_audit_service(audit_logger: Optional[AuditLogger] = None) -> 'AuditService':
    """
    Initialize the global audit service instance.
    
    Args:
        audit_logger: Optional custom audit logger. If not provided, will use default.
    
    Returns:
        The initialized audit service instance.
    """
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService(audit_logger or get_audit_logger())
    return _audit_service


def get_audit_service() -> 'AuditService':
    """
    Get the global audit service instance.
    
    Returns:
        The audit service instance, creating it if it doesn't exist.
    """
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService(get_audit_logger())
    return _audit_service


class AuditService:
    """
    Business-focused audit service for transaction operations.
    
    This service provides high-level audit logging methods that understand
    the business context of transactions, orders, payments, and refunds.
    """
    
    def __init__(self, audit_logger: AuditLogger = None):
        self.audit_logger = audit_logger or get_audit_logger()
    
    # Transaction audit methods
    def log_transaction_created(
        self,
        transaction: TransactionInDB,
        user: Optional[UserResponse] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log transaction creation with business context"""
        metadata = {
            "business_context": "transaction_creation",
            "initial_status": transaction.status.value,
            "amount": float(transaction.amount),
            "currency": transaction.currency.value,
            **(context or {})
        }
        
        self.audit_logger.log_transaction_event(
            transaction=transaction,
            action=AuditAction.CREATE,
            level=AuditLevel.INFO,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            metadata=metadata
        )
    
    def log_transaction_updated(
        self,
        transaction: TransactionInDB,
        changes: Dict[str, Any],
        user: Optional[UserResponse] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log transaction updates with change tracking"""
        metadata = {
            "business_context": "transaction_update",
            "changes": changes,
            **(context or {})
        }
        
        self.audit_logger.log_transaction_event(
            transaction=transaction,
            action=AuditAction.UPDATE,
            level=AuditLevel.INFO,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            changes=changes,
            metadata=metadata
        )
    
    def log_transaction_status_change(
        self,
        transaction: TransactionInDB,
        old_status: TransactionStatus,
        new_status: TransactionStatus,
        user: Optional[UserResponse] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log transaction status changes with business significance"""
        status_change = {
            "old_status": old_status.value,
            "new_status": new_status.value
        }
        
        metadata = {
            "business_context": "transaction_status_change",
            "status_change": status_change,
            "reason": reason,
            **(context or {})
        }
        
        # Use different log levels based on status change significance
        level = AuditLevel.WARNING if new_status in [
            TransactionStatus.FAILED, TransactionStatus.CANCELLED, TransactionStatus.REFUNDED
        ] else AuditLevel.INFO
        
        self.audit_logger.log_transaction_event(
            transaction=transaction,
            action=AuditAction.UPDATE,
            level=level,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            changes=status_change,
            metadata=metadata
        )
    
    # Order audit methods
    def log_order_created(
        self,
        order: OrderInDB,
        user: Optional[UserResponse] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log order creation"""
        metadata = {
            "business_context": "order_creation",
            "order_number": order.order_number,
            "service_type": order.service_type.value,
            "total_amount": float(order.total),
            **(context or {})
        }
        
        self.audit_logger.log_order_event(
            order=order,
            action=AuditAction.CREATE,
            level=AuditLevel.INFO,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            metadata=metadata
        )
    
    def log_order_status_change(
        self,
        order: OrderInDB,
        old_status: OrderStatus,
        new_status: OrderStatus,
        user: Optional[UserResponse] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log order status changes"""
        status_change = {
            "old_status": old_status.value,
            "new_status": new_status.value
        }
        
        metadata = {
            "business_context": "order_status_change",
            "status_change": status_change,
            **(context or {})
        }
        
        self.audit_logger.log_order_event(
            order=order,
            action=AuditAction.UPDATE,
            level=AuditLevel.INFO,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            changes=status_change,
            metadata=metadata
        )
    
    # Payment audit methods
    def log_payment_initiated(
        self,
        payment: PaymentInDB,
        user: Optional[UserResponse] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log payment initiation"""
        metadata = {
            "business_context": "payment_initiation",
            "payment_method": payment.payment_method.value,
            "payment_gateway": payment.payment_gateway.value,
            "amount": float(payment.amount),
            **(context or {})
        }
        
        self.audit_logger.log_payment_event(
            payment=payment,
            action=AuditAction.CREATE,
            level=AuditLevel.INFO,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            metadata=metadata
        )
    
    def log_payment_status_change(
        self,
        payment: PaymentInDB,
        old_status: PaymentStatus,
        new_status: PaymentStatus,
        user: Optional[UserResponse] = None,
        gateway_response: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log payment status changes with gateway response"""
        status_change = {
            "old_status": old_status.value,
            "new_status": new_status.value
        }
        
        metadata = {
            "business_context": "payment_status_change",
            "status_change": status_change,
            "gateway_response": gateway_response,
            **(context or {})
        }
        
        # Use warning level for failed payments
        level = AuditLevel.WARNING if new_status == PaymentStatus.FAILED else AuditLevel.INFO
        
        self.audit_logger.log_payment_event(
            payment=payment,
            action=AuditAction.UPDATE,
            level=level,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            changes=status_change,
            metadata=metadata
        )
    
    # Refund audit methods
    def log_refund_requested(
        self,
        refund: RefundInDB,
        requester: Optional[UserResponse] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log refund request with business justification"""
        metadata = {
            "business_context": "refund_request",
            "refund_reason": reason,
            "refund_amount": float(refund.amount),
            **(context or {})
        }
        
        self.audit_logger.log_refund_event(
            refund=refund,
            action=AuditAction.CREATE,
            level=AuditLevel.WARNING,  # Refunds are always noteworthy
            user_id=requester.id if requester else None,
            user_role=requester.role if requester else None,
            metadata=metadata
        )
    
    def log_refund_processed(
        self,
        refund: RefundInDB,
        processor: Optional[UserResponse] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log refund processing completion"""
        metadata = {
            "business_context": "refund_processing",
            "processing_successful": success,
            "error_message": error_message,
            **(context or {})
        }
        
        level = AuditLevel.ERROR if not success else AuditLevel.INFO
        
        self.audit_logger.log_refund_event(
            refund=refund,
            action=AuditAction.UPDATE,
            level=level,
            user_id=processor.id if processor else None,
            user_role=processor.role if processor else None,
            metadata=metadata
        )
    
    # Security and compliance audit methods
    def log_suspicious_activity(
        self,
        entity_type: str,
        entity_id: int,
        activity_description: str,
        user: Optional[UserResponse] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log suspicious or potentially fraudulent activity"""
        metadata = {
            "business_context": "security_alert",
            "activity_description": activity_description,
            "entity_type": entity_type,
            "entity_id": entity_id,
            **(context or {})
        }
        
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.UPDATE,  # Generic action for security events
            level=AuditLevel.ERROR,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            changes={},
            metadata=metadata
        )
        
        if hasattr(self.audit_logger, '_log_entry'):
            self.audit_logger._log_entry(entry)
