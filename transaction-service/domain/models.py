from sqlalchemy import Column, Integer, String, DateTime, Numeric, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from .enums import (
    TransactionStatus,
    OrderStatus,
    PaymentStatus,
    RefundStatus,
    Currency,
    ServiceType,
    TransactionType,
    PaymentMethod,
    PaymentGateway
)

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    order_id = Column(String(255), unique=True, nullable=False)
    transaction_type = Column(String(50), nullable=False, default=TransactionType.BOOKING.value)
    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(3), default=Currency.IDR.value)
    status = Column(String(50), nullable=False, default=TransactionStatus.PENDING.value)
    payment_method = Column(String(50), default=PaymentMethod.VIRTUAL_ACCOUNT.value)
    payment_gateway = Column(String(50), default=PaymentGateway.GOPAY.value)
    gateway_transaction_id = Column(String(255))
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    order_number = Column(String(255), unique=True, nullable=False)
    service_type = Column(String(50), nullable=False, default=ServiceType.FLIGHTS.value)
    service_id = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10,2), nullable=False)
    total_amount = Column(Numeric(10,2), nullable=False)
    status = Column(String(50), nullable=False, default=OrderStatus.DRAFT.value)
    booking_details = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, nullable=False)
    payment_method = Column(String(50), nullable=False, default=PaymentMethod.VIRTUAL_ACCOUNT.value)
    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(3), default=Currency.IDR.value)
    status = Column(String(50), nullable=False, default=PaymentStatus.PENDING.value)
    gateway_response = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    reason = Column(String(255))
    status = Column(String(50), nullable=False, default=RefundStatus.PENDING.value)
    processed_by = Column(Integer)
    processed_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))