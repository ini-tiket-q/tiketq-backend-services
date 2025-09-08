"""
Audit Logging Configuration

This module contains configuration settings for the audit logging system
including thresholds, compliance rules, and security policies.
"""

import os
from typing import Dict, List, Set
from enum import Enum

class AuditConfig:
    """Configuration class for audit logging system"""
    
    # High-value transaction thresholds (in IDR)
    HIGH_VALUE_THRESHOLD = float(os.getenv("HIGH_VALUE_THRESHOLD", "5000000"))  # 5 million IDR
    COMPLIANCE_THRESHOLD = float(os.getenv("COMPLIANCE_THRESHOLD", "100000000"))  # 100 million IDR
    
    # Performance monitoring thresholds
    SLOW_REQUEST_THRESHOLD_MS = float(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "5000"))  # 5 seconds
    VERY_SLOW_REQUEST_THRESHOLD_MS = float(os.getenv("VERY_SLOW_REQUEST_THRESHOLD_MS", "10000"))  # 10 seconds
    
    # Security monitoring settings
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
    SUSPICIOUS_REQUEST_SIZE = int(os.getenv("SUSPICIOUS_REQUEST_SIZE", "10485760"))  # 10MB
    MAX_QUERY_PARAMS = int(os.getenv("MAX_QUERY_PARAMS", "50"))
    
    # Logging settings
    LOG_LEVEL = os.getenv("AUDIT_LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("AUDIT_LOG_FILE", "/tmp/transaction-audit.log")
    LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "90"))
    
    # Business rules
    REQUIRE_APPROVAL_AMOUNT = float(os.getenv("REQUIRE_APPROVAL_AMOUNT", "50000000"))  # 50 million IDR
    AUTO_REFUND_LIMIT = float(os.getenv("AUTO_REFUND_LIMIT", "1000000"))  # 1 million IDR
    
    # Compliance and reporting
    COMPLIANCE_REPORTING = os.getenv("COMPLIANCE_REPORTING", "true").lower() == "true"
    GDPR_ANONYMIZATION = os.getenv("GDPR_ANONYMIZATION", "true").lower() == "true"
    PCI_COMPLIANCE = os.getenv("PCI_COMPLIANCE", "true").lower() == "true"
    
    # Alert thresholds
    ALERT_ON_HIGH_VALUE = os.getenv("ALERT_ON_HIGH_VALUE", "true").lower() == "true"
    ALERT_ON_SUSPICIOUS = os.getenv("ALERT_ON_SUSPICIOUS", "true").lower() == "true"
    ALERT_ON_ERRORS = os.getenv("ALERT_ON_ERRORS", "true").lower() == "true"
    
    # Fields to exclude from logging for privacy
    SENSITIVE_FIELDS: Set[str] = {
        "password", "credit_card_number", "cvv", "pin", 
        "ssn", "tax_id", "bank_account", "routing_number",
        "passport_number", "id_number"
    }
    
    # Payment methods that require special logging
    HIGH_RISK_PAYMENT_METHODS: Set[str] = {
        "CASH", "CRYPTOCURRENCY", "WIRE_TRANSFER"
    }
    
    # Countries requiring enhanced monitoring
    HIGH_RISK_COUNTRIES: Set[str] = set(
        os.getenv("HIGH_RISK_COUNTRIES", "").split(",")
    ) if os.getenv("HIGH_RISK_COUNTRIES") else set()
    
    # IP ranges for internal monitoring
    INTERNAL_IP_RANGES: List[str] = [
        "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.1/32"
    ]
    
    @classmethod
    def is_high_value_transaction(cls, amount: float) -> bool:
        """Check if transaction amount exceeds high-value threshold"""
        return amount >= cls.HIGH_VALUE_THRESHOLD
    
    @classmethod
    def requires_compliance_review(cls, amount: float) -> bool:
        """Check if transaction requires compliance review"""
        return amount >= cls.COMPLIANCE_THRESHOLD
    
    @classmethod
    def is_slow_request(cls, duration_ms: float) -> bool:
        """Check if request is considered slow"""
        return duration_ms >= cls.SLOW_REQUEST_THRESHOLD_MS
    
    @classmethod
    def is_very_slow_request(cls, duration_ms: float) -> bool:
        """Check if request is considered very slow"""
        return duration_ms >= cls.VERY_SLOW_REQUEST_THRESHOLD_MS
    
    @classmethod
    def should_alert_high_value(cls, amount: float) -> bool:
        """Check if high-value transaction should trigger alert"""
        return cls.ALERT_ON_HIGH_VALUE and cls.is_high_value_transaction(amount)
    
    @classmethod
    def sanitize_sensitive_data(cls, data: Dict) -> Dict:
        """Remove or mask sensitive fields from data"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in cls.SENSITIVE_FIELDS):
                sanitized[key] = "*" * 8  # Mask sensitive data
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_sensitive_data(value)
            elif key_lower in ["email", "phone", "user_agent"]:
                # Partially mask identifiable information
                if key_lower == "email" and "@" in str(value):
                    username, domain = str(value).split("@", 1)
                    sanitized[key] = f"{username[:2]}***@{domain}"
                elif key_lower == "phone" and len(str(value)) > 4:
                    sanitized[key] = f"***{str(value)[-4:]}"
                else:
                    sanitized[key] = str(value)[:10] + "..." if len(str(value)) > 10 else str(value)
            else:
                sanitized[key] = value
        
        return sanitized


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceRule:
    """Compliance rule definition"""
    
    def __init__(
        self,
        name: str,
        description: str,
        condition: callable,
        severity: AlertSeverity = AlertSeverity.MEDIUM
    ):
        self.name = name
        self.description = description
        self.condition = condition
        self.severity = severity


# Define compliance rules
COMPLIANCE_RULES = [
    ComplianceRule(
        name="HIGH_VALUE_TRANSACTION",
        description="Transaction exceeds high-value threshold",
        condition=lambda data: data.get("amount", 0) >= AuditConfig.HIGH_VALUE_THRESHOLD,
        severity=AlertSeverity.HIGH
    ),
    ComplianceRule(
        name="SUSPICIOUS_TRANSACTION_PATTERN",
        description="Multiple large transactions from same user in short time",
        condition=lambda data: data.get("suspicious_pattern", False),
        severity=AlertSeverity.CRITICAL
    ),
    ComplianceRule(
        name="FAILED_AUTHENTICATION_ATTEMPTS",
        description="Multiple failed authentication attempts",
        condition=lambda data: data.get("failed_attempts", 0) >= AuditConfig.MAX_FAILED_ATTEMPTS,
        severity=AlertSeverity.HIGH
    ),
    ComplianceRule(
        name="HIGH_RISK_PAYMENT_METHOD",
        description="Transaction using high-risk payment method",
        condition=lambda data: data.get("payment_method") in AuditConfig.HIGH_RISK_PAYMENT_METHODS,
        severity=AlertSeverity.MEDIUM
    ),
    ComplianceRule(
        name="LARGE_REFUND_REQUEST",
        description="Large refund request requiring review",
        condition=lambda data: (
            data.get("operation") == "refund" and 
            data.get("amount", 0) >= AuditConfig.REQUIRE_APPROVAL_AMOUNT
        ),
        severity=AlertSeverity.HIGH
    )
]


def evaluate_compliance_rules(audit_data: Dict) -> List[ComplianceRule]:
    """Evaluate audit data against compliance rules"""
    triggered_rules = []
    
    for rule in COMPLIANCE_RULES:
        try:
            if rule.condition(audit_data):
                triggered_rules.append(rule)
        except Exception:
            # If rule evaluation fails, continue with other rules
            continue
    
    return triggered_rules


# Environment-specific settings
class EnvironmentConfig:
    """Environment-specific audit configuration"""
    
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def is_production(cls) -> bool:
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        return cls.ENVIRONMENT.lower() == "development"
    
    @classmethod
    def get_log_config(cls) -> Dict:
        """Get environment-appropriate logging configuration"""
        if cls.is_production():
            return {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": False,
                "structured_logging": True,
                "include_stack_trace": False
            }
        else:
            return {
                "level": "DEBUG",
                "file_enabled": False,
                "console_enabled": True,
                "structured_logging": True,
                "include_stack_trace": True
            }
