from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class PaymentMethod(str, Enum):
    """Supported payment methods"""
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    E_WALLET = "e_wallet"
    QRIS = "qris"
    RETAIL = "retail"


class PaymentStatus(str, Enum):
    """Payment status enum for tracking payment lifecycle"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentRequest(BaseModel):
    """Payment request model for initiating a payment"""
    order_id: str
    amount: float
    payment_method: PaymentMethod
    customer_details: Dict[str, Any]
    item_details: List[Dict[str, Any]]
    description: Optional[str] = None
    expiry_duration: int = 24  # hours


class PaymentResponse(BaseModel):
    """Payment response model after payment initiation"""
    id: str
    order_id: str
    transaction_id: str
    amount: float
    status: PaymentStatus
    payment_method: PaymentMethod
    payment_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class PaymentStatusRequest(BaseModel):
    """Request model for checking payment status"""
    transaction_id: str


class PaymentCancellationRequest(BaseModel):
    """Request model for canceling a payment"""
    reason: Optional[str] = None


class PaymentRefundRequest(BaseModel):
    """Request model for refunding a payment"""
    amount: Optional[float] = None
    reason: str


class WebhookNotification(BaseModel):
    """Payment notification model for webhook handling"""
    transaction_id: str
    order_id: str
    transaction_status: str
    gross_amount: str
    payment_type: str
    fraud_status: Optional[str] = None
    signature_key: Optional[str] = None
    transaction_time: Optional[str] = None


class PaymentNotification(BaseModel):
    """Processed payment notification"""
    transaction_id: str
    order_id: str
    status: PaymentStatus
    amount: float
    payment_type: str
    processed_at: datetime
