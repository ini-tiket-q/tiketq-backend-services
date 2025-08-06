from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Payment status enum for tracking payment lifecycle"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class PaymentMethod(str, Enum):
    """Supported payment methods"""
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    E_WALLET = "e_wallet"
    QRIS = "qris"
    RETAIL = "retail"


class PaymentRequest(BaseModel):
    """Payment request model for initiating a payment"""
    order_id: str
    amount: float
    payment_method: PaymentMethod
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[dict]] = None
    callback_url: Optional[str] = None
    expiry_duration: Optional[int] = 24  # Hours


class PaymentResponse(BaseModel):
    """Payment response model after payment initiation"""
    payment_id: str
    order_id: str
    status: PaymentStatus
    amount: float
    payment_method: PaymentMethod
    transaction_time: datetime
    expiry_time: Optional[datetime] = None
    payment_url: Optional[str] = None
    token: Optional[str] = None
    redirect_url: Optional[str] = None
    qr_code_url: Optional[str] = None
    virtual_account_number: Optional[str] = None
    bank_code: Optional[str] = None


class PaymentNotification(BaseModel):
    """Payment notification model for webhook handling"""
    transaction_id: str
    order_id: str
    status_code: str
    status_message: str
    gross_amount: float
    payment_type: str
    transaction_time: datetime
    signature_key: str
    fraud_status: Optional[str] = None
    settlement_time: Optional[datetime] = None
    bank: Optional[str] = None
    va_number: Optional[str] = None
    masked_card: Optional[str] = None
