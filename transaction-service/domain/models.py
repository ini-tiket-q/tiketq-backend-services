from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4

class TransactionType(str, Enum):
    BOOKING = "BOOKING"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    CANCELLATION = "CANCELLATION"

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    E_WALLET = "E_WALLET"
    VIRTUAL_ACCOUNT = "VIRTUAL_ACCOUNT"
    CASH = "CASH"

class PaymentGateway(str, Enum):
    MIDTRANS = "MIDTRANS"
    XENDIT = "XENDIT"
    GOPAY = "GOPAY"
    OVO = "OVO"
    DANA = "DANA"

class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class RefundStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class ServiceType(str, Enum):
    FLIGHTS = "FLIGHTS"
    HOTELS = "HOTELS"
    FERRIES = "FERRIES"
    PPOB = "PPOB"

class Currency(str, Enum):
    IDR = "IDR"
    # USD = "USD"
    # EUR = "EUR"
    # SGD = "SGD"

class TransactionBase(BaseModel):
    user_id: int
    order_id: str = Field(default_factory=lambda: f"ORD-{uuid4().hex[:8].upper()}")
    transaction_type: TransactionType
    amount: float
    currency: Currency = Currency.IDR
    status: TransactionStatus = TransactionStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    payment_gateway: Optional[PaymentGateway] = None
    gateway_transaction_id: Optional[str] = None
    meta_data: Dict[str, Any] = {}

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    payment_method: Optional[PaymentMethod] = None
    payment_gateway: Optional[PaymentGateway] = None
    gateway_transaction_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

class TransactionInDB(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    user_id: int
    order_number: str = Field(default_factory=lambda: f"ORD-{uuid4().hex[:8].upper()}")
    service_type: ServiceType 
    items: List[Dict[str, Any]]
    subtotal: float
    tax: float = 0.0
    discount: float = 0.0
    total: float
    status: OrderStatus = OrderStatus.DRAFT

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    meta_data: Optional[Dict[str, Any]] = None

class OrderInDB(OrderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PaymentBase(BaseModel):
    transaction_id: int
    amount: float
    currency: Currency = Currency.IDR
    payment_method: PaymentMethod
    payment_gateway: PaymentGateway
    gateway_transaction_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    meta_data: Optional[Dict[str, Any]] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    gateway_transaction_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

class PaymentInDB(PaymentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RefundBase(BaseModel):
    transaction_id: int
    amount: float
    reason: str
    status: RefundStatus = RefundStatus.PENDING
    processed_by: Optional[int] = None
    processed_at: Optional[datetime] = None
    notes: Optional[str] = None

class RefundCreate(RefundBase):
    pass

class RefundUpdate(BaseModel):
    status: Optional[RefundStatus] = None
    processed_by: Optional[int] = None
    notes: Optional[str] = None

class RefundInDB(RefundBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True