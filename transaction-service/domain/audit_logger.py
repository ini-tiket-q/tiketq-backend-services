"""
Transaction Audit Logger

This module provides comprehensive transaction logging functionality that follows
the existing hexagonal architecture pattern and integrates with the business logic
to track all transaction-related activities.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
import logging
import json
from dataclasses import dataclass, asdict

from domain.models import (
    TransactionInDB, TransactionStatus, TransactionType,
    OrderInDB, OrderStatus,
    PaymentInDB, PaymentStatus,
    RefundInDB, RefundStatus,
    UserRole
)


class AuditAction(str, Enum):
    """Enumeration of auditable actions"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    PAYMENT_ATTEMPT = "PAYMENT_ATTEMPT"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUND_PROCESSED = "REFUND_PROCESSED"


class AuditLevel(str, Enum):
    """Audit logging levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AuditLogEntry:
    """Data structure for audit log entries"""
    timestamp: datetime
    entity_type: str  # "transaction", "order", "payment", "refund"
    entity_id: int
    action: AuditAction
    level: AuditLevel
    user_id: Optional[int]
    user_role: Optional[UserRole]
    changes: Dict[str, Any]
    metadata: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit entry to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action.value,
            "level": self.level.value,
            "user_id": self.user_id,
            "user_role": self.user_role.value if self.user_role else None,
            "changes": self.changes,
            "metadata": self.metadata,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id
        }


class AuditLogger(ABC):
    """Abstract base class for transaction audit logging"""
    
    @abstractmethod
    def log_transaction_event(
        self,
        transaction: TransactionInDB,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log a transaction-related event"""
        pass
    
    @abstractmethod
    def log_order_event(
        self,
        order: OrderInDB,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log an order-related event"""
        pass
    
    @abstractmethod
    def log_payment_event(
        self,
        payment: PaymentInDB,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log a payment-related event"""
        pass
    
    @abstractmethod
    def log_refund_event(
        self,
        refund: RefundInDB,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log a refund-related event"""
        pass
    
    @abstractmethod
    def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Retrieve audit logs with filters"""
        pass


class DefaultAuditLogger(AuditLogger):
    """
    Default implementation of AuditLogger that logs to Python logging system
    and maintains in-memory audit trail for retrieval.
    
    In production, this could be extended to write to databases, external
    logging systems, or message queues.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TransactionAudit")
        self.audit_entries: List[AuditLogEntry] = []
        # Set up structured logging
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - AUDIT - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _create_audit_entry(
        self,
        entity_type: str,
        entity_id: int,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AuditLogEntry:
        """Create an audit log entry"""
        return AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            level=level,
            user_id=user_id,
            user_role=user_role,
            changes=changes or {},
            metadata=metadata or {},
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            session_id=kwargs.get('session_id')
        )
    
    def _log_entry(self, entry: AuditLogEntry) -> None:
        """Log an audit entry to the logging system and store in memory"""
        # Store in memory for retrieval
        self.audit_entries.append(entry)
        
        # Keep only last 10000 entries in memory to prevent memory leaks
        if len(self.audit_entries) > 10000:
            self.audit_entries = self.audit_entries[-5000:]
        
        # Log to Python logging system
        log_message = json.dumps(entry.to_dict())
        
        if entry.level == AuditLevel.CRITICAL:
            self.logger.critical(log_message)
        elif entry.level == AuditLevel.ERROR:
            self.logger.error(log_message)
        elif entry.level == AuditLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def log_transaction_event(
        self,
        transaction: TransactionInDB,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log a transaction-related event"""
        # Enhanced metadata with transaction details
        enhanced_metadata = {
            "transaction_type": transaction.transaction_type.value,
            "amount": float(transaction.amount),
            "currency": transaction.currency.value,
            "status": transaction.status.value,
            "order_id": transaction.order_id,
            "payment_method": transaction.payment_method.value if transaction.payment_method else None,
            "payment_gateway": transaction.payment_gateway.value if transaction.payment_gateway else None,
            **(metadata or {})
        }
        
        entry = self._create_audit_entry(
            entity_type="transaction",
            entity_id=transaction.id,
            action=action,
            level=level,
            user_id=user_id or transaction.user_id,
            user_role=user_role,
            changes=changes,
            metadata=enhanced_metadata,
            **kwargs
        )
        
        self._log_entry(entry)
    
    def log_order_event(
        self,
        order: OrderInDB,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log an order-related event"""
        # Enhanced metadata with order details
        enhanced_metadata = {
            "order_number": order.order_number,
            "service_type": order.service_type.value,
            "total": float(order.total),
            "status": order.status.value,
            "items_count": len(order.items) if order.items else 0,
            **(metadata or {})
        }
        
        entry = self._create_audit_entry(
            entity_type="order",
            entity_id=order.id,
            action=action,
            level=level,
            user_id=user_id or order.user_id,
            user_role=user_role,
            changes=changes,
            metadata=enhanced_metadata,
            **kwargs
        )
        
        self._log_entry(entry)
    
    def log_payment_event(
        self,
        payment: PaymentInDB,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log a payment-related event"""
        # Enhanced metadata with payment details
        enhanced_metadata = {
            "transaction_id": payment.transaction_id,
            "amount": float(payment.amount),
            "currency": payment.currency.value,
            "payment_method": payment.payment_method.value,
            "payment_gateway": payment.payment_gateway.value,
            "status": payment.status.value,
            "gateway_transaction_id": payment.gateway_transaction_id,
            **(metadata or {})
        }
        
        entry = self._create_audit_entry(
            entity_type="payment",
            entity_id=payment.id,
            action=action,
            level=level,
            user_id=user_id,
            user_role=user_role,
            changes=changes,
            metadata=enhanced_metadata,
            **kwargs
        )
        
        self._log_entry(entry)
    
    def log_refund_event(
        self,
        refund: RefundInDB,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log a refund-related event"""
        # Enhanced metadata with refund details
        enhanced_metadata = {
            "transaction_id": refund.transaction_id,
            "amount": float(refund.amount),
            "reason": refund.reason,
            "status": refund.status.value,
            "processed_by": refund.processed_by,
            **(metadata or {})
        }
        
        entry = self._create_audit_entry(
            entity_type="refund",
            entity_id=refund.id,
            action=action,
            level=level,
            user_id=user_id or refund.processed_by,
            user_role=user_role,
            changes=changes,
            metadata=enhanced_metadata,
            **kwargs
        )
        
        self._log_entry(entry)
    
    def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Retrieve audit logs with filters"""
        filtered_entries = []
        
        for entry in reversed(self.audit_entries):  # Most recent first
            # Apply filters
            if entity_type and entry.entity_type != entity_type:
                continue
            if entity_id and entry.entity_id != entity_id:
                continue
            if action and entry.action != action:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if start_date and entry.timestamp < start_date:
                continue
            if end_date and entry.timestamp > end_date:
                continue
            
            filtered_entries.append(entry)
            
            # Apply limit
            if len(filtered_entries) >= limit:
                break
        
        return filtered_entries


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = DefaultAuditLogger()
    return _audit_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """Set a custom audit logger implementation"""
    global _audit_logger
    _audit_logger = logger


# Helper functions for common audit scenarios
def audit_transaction_created(
    transaction: TransactionInDB,
    user_id: Optional[int] = None,
    user_role: Optional[UserRole] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log transaction creation event"""
    logger = get_audit_logger()
    logger.log_transaction_event(
        transaction=transaction,
        action=AuditAction.CREATE,
        level=AuditLevel.INFO,
        user_id=user_id,
        user_role=user_role,
        metadata=metadata
    )


def audit_transaction_updated(
    transaction: TransactionInDB,
    old_values: Dict[str, Any],
    new_values: Dict[str, Any],
    user_id: Optional[int] = None,
    user_role: Optional[UserRole] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log transaction update event"""
    logger = get_audit_logger()
    changes = {
        "old_values": old_values,
        "new_values": new_values
    }
    
    # Check for critical status changes
    level = AuditLevel.INFO
    if (old_values.get("status") != new_values.get("status") and 
        new_values.get("status") in [TransactionStatus.FAILED.value, TransactionStatus.REFUNDED.value]):
        level = AuditLevel.WARNING
    
    logger.log_transaction_event(
        transaction=transaction,
        action=AuditAction.UPDATE,
        level=level,
        user_id=user_id,
        user_role=user_role,
        changes=changes,
        metadata=metadata
    )


def audit_transaction_status_changed(
    transaction: TransactionInDB,
    old_status: TransactionStatus,
    new_status: TransactionStatus,
    user_id: Optional[int] = None,
    user_role: Optional[UserRole] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log transaction status change event"""
    logger = get_audit_logger()
    changes = {
        "old_status": old_status.value,
        "new_status": new_status.value
    }
    
    # Determine log level based on status change
    level = AuditLevel.INFO
    if new_status == TransactionStatus.FAILED:
        level = AuditLevel.ERROR
    elif new_status == TransactionStatus.REFUNDED:
        level = AuditLevel.WARNING
    elif new_status == TransactionStatus.COMPLETED:
        level = AuditLevel.INFO
    
    logger.log_transaction_event(
        transaction=transaction,
        action=AuditAction.STATUS_CHANGE,
        level=level,
        user_id=user_id,
        user_role=user_role,
        changes=changes,
        metadata=metadata
    )


def audit_payment_attempt(
    payment: PaymentInDB,
    user_id: Optional[int] = None,
    user_role: Optional[UserRole] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log payment attempt event"""
    logger = get_audit_logger()
    logger.log_payment_event(
        payment=payment,
        action=AuditAction.PAYMENT_ATTEMPT,
        level=AuditLevel.INFO,
        user_id=user_id,
        user_role=user_role,
        metadata=metadata
    )


def audit_payment_confirmed(
    payment: PaymentInDB,
    user_id: Optional[int] = None,
    user_role: Optional[UserRole] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log payment confirmation event"""
    logger = get_audit_logger()
    level = AuditLevel.INFO if payment.status == PaymentStatus.COMPLETED else AuditLevel.ERROR
    
    logger.log_payment_event(
        payment=payment,
        action=AuditAction.PAYMENT_CONFIRMED,
        level=level,
        user_id=user_id,
        user_role=user_role,
        metadata=metadata
    )


def audit_refund_requested(
    refund: RefundInDB,
    user_id: Optional[int] = None,
    user_role: Optional[UserRole] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log refund request event"""
    logger = get_audit_logger()
    logger.log_refund_event(
        refund=refund,
        action=AuditAction.REFUND_REQUESTED,
        level=AuditLevel.WARNING,  # Refund requests are noteworthy
        user_id=user_id,
        user_role=user_role,
        metadata=metadata
    )


def audit_refund_processed(
    refund: RefundInDB,
    user_id: Optional[int] = None,
    user_role: Optional[UserRole] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log refund processing completion event"""
    logger = get_audit_logger()
    level = AuditLevel.INFO if refund.status == RefundStatus.COMPLETED else AuditLevel.ERROR
    
    logger.log_refund_event(
        refund=refund,
        action=AuditAction.REFUND_PROCESSED,
        level=level,
        user_id=user_id,
        user_role=user_role,
        metadata=metadata
    )
