"""
Comprehensive Audit Logging Module for Transaction Service

This module provides structured audit logging following business best practices:
- Security and compliance logging
- User activity tracking
- Business metrics and analytics
- Performance monitoring
- Error tracking with context
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
import traceback
import os
from functools import wraps
import time

from .audit_config import AuditConfig, evaluate_compliance_rules, EnvironmentConfig

# Configure structured JSON logging
class AuditLogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING" 
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"
    BUSINESS = "BUSINESS"
    PERFORMANCE = "PERFORMANCE"

class AuditEventType(str, Enum):
    # Transaction events
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_UPDATED = "transaction.updated"
    TRANSACTION_CANCELLED = "transaction.cancelled"
    TRANSACTION_REFUNDED = "transaction.refunded"
    TRANSACTION_COMPLETED = "transaction.completed"
    TRANSACTION_FAILED = "transaction.failed"
    
    # Payment events
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_CONFIRMED = "payment.confirmed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Security events
    UNAUTHORIZED_ACCESS = "security.unauthorized_access"
    AUTHENTICATION_SUCCESS = "security.auth.success"
    AUTHENTICATION_FAILURE = "security.auth.failure"
    PERMISSION_DENIED = "security.permission_denied"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    
    # Business events
    ORDER_CREATED = "business.order.created"
    ORDER_CANCELLED = "business.order.cancelled"
    REFUND_PROCESSED = "business.refund.processed"
    HIGH_VALUE_TRANSACTION = "business.high_value_transaction"
    REVENUE_MILESTONE = "business.revenue_milestone"
    
    # System events
    API_REQUEST = "system.api.request"
    API_RESPONSE = "system.api.response"
    ERROR_OCCURRED = "system.error"
    PERFORMANCE_SLOW = "system.performance.slow"

@dataclass
class AuditLogEntry:
    """Structured audit log entry following business standards"""
    
    # Core fields
    timestamp: str
    event_type: str
    level: str
    service: str = "transaction-service"
    version: str = "1.0.0"
    
    # User context
    email: Optional[str] = None
    user_role: Optional[str] = None
    session_id: Optional[str] = None
    
    # Request context
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    # Business context
    transaction_id: Optional[int] = None
    order_id: Optional[str] = None
    payment_id: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    
    # Event details
    message: str = ""
    details: Optional[Dict[str, Any]] = None
    
    # Performance metrics
    duration_ms: Optional[float] = None
    
    # Error context
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None

class AuditLogger:
    """Comprehensive audit logger for transaction service"""
    
    def __init__(self):
        # Configure logger with structured formatting
        self.logger = logging.getLogger("transaction.audit")
        self.logger.setLevel(getattr(logging, AuditConfig.LOG_LEVEL))
        
        # Remove existing handlers to avoid duplication
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create formatter for JSON structured logs
        formatter = logging.Formatter(
            '%(message)s'  # We'll handle JSON formatting in the log method
        )
        
        # Environment-specific configuration
        log_config = EnvironmentConfig.get_log_config()
        
        # Console handler for development
        if log_config["console_enabled"]:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler for audit logs (production)
        if log_config["file_enabled"] or AuditConfig.LOG_FILE:
            log_file = AuditConfig.LOG_FILE
            try:
                # Create log directory if it doesn't exist
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                # Fallback to console if file logging fails
                print(f"Failed to setup file logging: {e}")
        
        self.environment = EnvironmentConfig.ENVIRONMENT
        self.config = AuditConfig()
    
    def _log_entry(self, entry: AuditLogEntry):
        """Log structured audit entry with compliance evaluation"""
        try:
            log_dict = asdict(entry)
            # Remove None values to keep logs clean
            log_dict = {k: v for k, v in log_dict.items() if v is not None}
            
            # Add environment information
            log_dict["environment"] = self.environment
            
            # Sanitize sensitive data if GDPR compliance is enabled
            if AuditConfig.GDPR_ANONYMIZATION and log_dict.get("details"):
                log_dict["details"] = AuditConfig.sanitize_sensitive_data(log_dict["details"])
            
            # Evaluate compliance rules
            triggered_rules = evaluate_compliance_rules(log_dict)
            if triggered_rules:
                log_dict["compliance_alerts"] = [
                    {
                        "rule": rule.name,
                        "description": rule.description,
                        "severity": rule.severity.value
                    } for rule in triggered_rules
                ]
            
            # Add business context flags
            self._add_business_context(log_dict)
            
            # Convert to JSON string
            log_message = json.dumps(log_dict, ensure_ascii=False, default=str)
            
            # Map audit level to standard logging level
            level_mapping = {
                AuditLogLevel.INFO: logging.INFO,
                AuditLogLevel.WARNING: logging.WARNING,
                AuditLogLevel.ERROR: logging.ERROR,
                AuditLogLevel.CRITICAL: logging.CRITICAL,
                AuditLogLevel.SECURITY: logging.ERROR,  # Security events as ERROR level
                AuditLogLevel.BUSINESS: logging.INFO,
                AuditLogLevel.PERFORMANCE: logging.WARNING
            }
            
            self.logger.log(
                level_mapping.get(AuditLogLevel(entry.level), logging.INFO),
                log_message
            )
            
        except Exception as e:
            # Fallback logging if structured logging fails
            self.logger.error(f"Failed to log audit entry: {str(e)}")
    
    def _add_business_context(self, log_dict: Dict[str, Any]):
        """Add business context flags to log entry"""
        amount = log_dict.get("amount", 0)
        
        if amount and isinstance(amount, (int, float)):
            log_dict["business_flags"] = {
                "high_value": AuditConfig.is_high_value_transaction(amount),
                "compliance_review_required": AuditConfig.requires_compliance_review(amount),
                "alert_required": AuditConfig.should_alert_high_value(amount)
            }
        
        # Add performance flags
        duration_ms = log_dict.get("duration_ms", 0)
        if duration_ms:
            log_dict["performance_flags"] = {
                "slow_request": AuditConfig.is_slow_request(duration_ms),
                "very_slow_request": AuditConfig.is_very_slow_request(duration_ms)
            }
    
    def log_transaction_event(
        self,
        event_type: AuditEventType,
        transaction_id: int,
        email: str,
        user_role: str,
        amount: Optional[float] = None,
        currency: str = "IDR",
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, str]] = None
    ):
        """Log transaction-related events with full business context"""
        
        # Determine log level based on event type
        level = AuditLogLevel.BUSINESS
        if "failed" in event_type.value or "error" in event_type.value:
            level = AuditLogLevel.ERROR
        elif event_type in [AuditEventType.TRANSACTION_CREATED, AuditEventType.TRANSACTION_COMPLETED]:
            level = AuditLogLevel.INFO
        
        # Build message
        messages = {
            AuditEventType.TRANSACTION_CREATED: f"Transaction {transaction_id} created by {email}",
            AuditEventType.TRANSACTION_UPDATED: f"Transaction {transaction_id} updated by {email}",
            AuditEventType.TRANSACTION_CANCELLED: f"Transaction {transaction_id} cancelled by {email}",
            AuditEventType.TRANSACTION_REFUNDED: f"Transaction {transaction_id} refunded",
            AuditEventType.TRANSACTION_COMPLETED: f"Transaction {transaction_id} completed successfully",
            AuditEventType.TRANSACTION_FAILED: f"Transaction {transaction_id} failed"
        }
        
        message = messages.get(event_type, f"Transaction event: {event_type.value}")
        
        # Add business context to details
        business_details = {
            **(details or {}),
            "transaction_status": status,
            "service_type": details.get("service_type") if details else None,
            "payment_method": details.get("payment_method") if details else None
        }
        
        # Check for high-value transaction
        if amount and amount >= AuditConfig.HIGH_VALUE_THRESHOLD:
            self._log_high_value_transaction(transaction_id, email, amount, currency)
        
        # Check for compliance requirements
        if amount and AuditConfig.requires_compliance_review(amount):
            self._log_compliance_alert(transaction_id, email, amount, currency, "HIGH_VALUE_COMPLIANCE")
        
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.value,
            level=level.value,
            email=email,
            user_role=user_role,
            transaction_id=transaction_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            message=message,
            details=business_details,
            ip_address=request_context.get("ip_address") if request_context else None,
            user_agent=request_context.get("user_agent") if request_context else None,
            endpoint=request_context.get("endpoint") if request_context else None,
            method=request_context.get("method") if request_context else None
        )
        
        self._log_entry(entry)
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        email: Optional[str] = None,
        user_role: Optional[str] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, str]] = None
    ):
        """Log security-related events"""
        
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.value,
            level=AuditLogLevel.SECURITY.value,
            email=email,
            user_role=user_role,
            message=message,
            details=details,
            ip_address=request_context.get("ip_address") if request_context else None,
            user_agent=request_context.get("user_agent") if request_context else None,
            endpoint=request_context.get("endpoint") if request_context else None,
            method=request_context.get("method") if request_context else None
        )
        
        self._log_entry(entry)
    
    def log_api_request(
        self,
        method: str,
        endpoint: str,
        email: Optional[str] = None,
        user_role: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log API request/response for monitoring and analytics"""
        
        level = AuditLogLevel.INFO
        if duration_ms and duration_ms > 5000:  # Slow requests > 5 seconds
            level = AuditLogLevel.PERFORMANCE
        elif status_code and status_code >= 400:
            level = AuditLogLevel.WARNING if status_code < 500 else AuditLogLevel.ERROR
        
        details = {
            "status_code": status_code,
            "request_size_bytes": request_size,
            "response_size_bytes": response_size
        }
        
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.API_REQUEST.value,
            level=level.value,
            email=email,
            user_role=user_role,
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
            message=f"{method} {endpoint} - {status_code}",
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self._log_entry(entry)
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        email: Optional[str] = None,
        transaction_id: Optional[int] = None,
        endpoint: Optional[str] = None
    ):
        """Log errors with full context and stack trace"""
        
        details = {
            **(context or {}),
            "error_type": type(error).__name__,
            "error_args": str(error.args) if error.args else None
        }
        
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.ERROR_OCCURRED.value,
            level=AuditLogLevel.ERROR.value,
            email=email,
            transaction_id=transaction_id,
            endpoint=endpoint,
            message=str(error),
            details=details,
            error_code=getattr(error, 'code', None),
            stack_trace=traceback.format_exc()
        )
        
        self._log_entry(entry)
    
    def _log_high_value_transaction(
        self,
        transaction_id: int,
        email: str,
        amount: float,
        currency: str
    ):
        """Log high-value transactions for compliance monitoring"""
        
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.HIGH_VALUE_TRANSACTION.value,
            level=AuditLogLevel.BUSINESS.value,
            email=email,
            transaction_id=transaction_id,
            amount=amount,
            currency=currency,
            message=f"High-value transaction alert: {amount:,.2f} {currency}",
            details={
                "threshold_exceeded": True,
                "compliance_flag": True,
                "requires_review": AuditConfig.requires_compliance_review(amount),
                "threshold_amount": AuditConfig.HIGH_VALUE_THRESHOLD,
                "compliance_threshold": AuditConfig.COMPLIANCE_THRESHOLD
            }
        )
        
        self._log_entry(entry)
    
    def _log_compliance_alert(
        self,
        transaction_id: int,
        email: str,
        amount: float,
        currency: str,
        alert_type: str
    ):
        """Log compliance alerts for regulatory requirements"""
        
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.HIGH_VALUE_TRANSACTION.value,  # Reuse existing event type
            level=AuditLogLevel.CRITICAL.value,
            email=email,
            transaction_id=transaction_id,
            amount=amount,
            currency=currency,
            message=f"Compliance alert: {alert_type} for transaction {transaction_id}",
            details={
                "alert_type": alert_type,
                "compliance_required": True,
                "regulatory_reporting": True,
                "threshold_amount": AuditConfig.COMPLIANCE_THRESHOLD,
                "requires_manual_review": True
            }
        )
        
        self._log_entry(entry)

# Global audit logger instance
audit_logger = AuditLogger()

def audit_transaction_operation(event_type: AuditEventType):
    """Decorator for automatic transaction operation auditing"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract audit context from function arguments
                current_user = kwargs.get('current_user', {})
                email = getattr(current_user, 'email', None)
                user_role = getattr(current_user, 'role', None)
                transaction_id = kwargs.get('transaction_id')
                
                if hasattr(result, 'id'):
                    transaction_id = transaction_id or result.id
                
                audit_logger.log_transaction_event(
                    event_type=event_type,
                    transaction_id=transaction_id,
                    email=email,
                    user_role=user_role.value if user_role else None,
                    details={"operation_duration_ms": duration_ms}
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                current_user = kwargs.get('current_user', {})
                email = getattr(current_user, 'email', None)
                audit_logger.log_error(
                    error=e,
                    context={
                        "function": func.__name__,
                        "operation_duration_ms": duration_ms,
                        "event_type": event_type.value
                    },
                    email=email,
                    transaction_id=kwargs.get('transaction_id')
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract audit context from function arguments
                current_user = kwargs.get('current_user', {})
                email = getattr(current_user, 'email', None)
                user_role = getattr(current_user, 'role', None)
                transaction_id = kwargs.get('transaction_id')
                
                if hasattr(result, 'id'):
                    transaction_id = transaction_id or result.id
                
                audit_logger.log_transaction_event(
                    event_type=event_type,
                    transaction_id=transaction_id,
                    email=email,
                    user_role=user_role.value if user_role else None,
                    details={"operation_duration_ms": duration_ms}
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                current_user = kwargs.get('current_user', {})
                email = getattr(current_user, 'email', None)
                audit_logger.log_error(
                    error=e,
                    context={
                        "function": func.__name__,
                        "operation_duration_ms": duration_ms,
                        "event_type": event_type.value
                    },
                    email=email,
                    transaction_id=kwargs.get('transaction_id')
                )
                raise
        
        # Return the appropriate wrapper based on function type
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    
    return decorator

def extract_request_context(request = None) -> Dict[str, str]:
    """Extract request context for audit logging"""
    context = {}
    
    if request:
        context.update({
            "ip_address": getattr(request.client, 'host', None) if hasattr(request, 'client') else None,
            "user_agent": request.headers.get("user-agent") if hasattr(request, 'headers') else None,
            "endpoint": str(request.url.path) if hasattr(request, 'url') else None,
            "method": request.method if hasattr(request, 'method') else None
        })
    
    return context
