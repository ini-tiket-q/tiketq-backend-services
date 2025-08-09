from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Enum,
    JSON,
    ForeignKey,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

import os
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from typing import List, Optional
from datetime import datetime, timezone

from ..domain.models import (
    TransactionInDB,
    TransactionCreate,
    TransactionUpdate,
    TransactionStatus,
    TransactionType,
    OrderInDB,
    OrderCreate,
    OrderStatus,
    PaymentInDB,
    PaymentCreate,
    PaymentMethod,
    PaymentGateway,
    PaymentStatus,
    RefundInDB,
    RefundCreate,
    RefundStatus,
    ServiceType,
    Currency,
)
from ..domain.repository import (
    TransactionRepository,
    OrderRepository,
    PaymentRepository,
    RefundRepository,
)

# Load database URL from environment variable
DATABASE_URL = os.getenv("TRANSACTION_DB_URL")
if not DATABASE_URL:
    raise RuntimeError("TRANSACTION_DB_URL environment variable is required")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# SQLAlchemy models
class Transaction(Base):
    """SQLAlchemy model for transactions table"""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    order_id = Column(String(255), unique=True, nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(Enum(Currency), default=Currency.IDR, nullable=False)
    status = Column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False
    )
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_gateway = Column(Enum(PaymentGateway), nullable=True)
    gateway_transaction_id = Column(String(255), nullable=True, index=True)
    metadata = Column(JSON, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    payments = relationship("Payment", back_populates="transaction")
    refunds = relationship("Refund", back_populates="transaction")


class Order(Base):
    """SQLAlchemy model for orders table"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    order_number = Column(String(255), unique=True, nullable=False, index=True)
    service_type = Column(Enum(ServiceType), nullable=False)
    items = Column(JSON, nullable=False)
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    total = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False)
    metadata_ = Column("metadata", JSON, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Payment(Base):
    """SQLAlchemy model for payments table"""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(Enum(Currency), default=Currency.IDR, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_gateway = Column(Enum(PaymentGateway), nullable=False)
    gateway_transaction_id = Column(String(255), nullable=True, index=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    metadata_ = Column("metadata", JSON, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transaction = relationship("Transaction", back_populates="payments")


class Refund(Base):
    """SQLAlchemy model for refunds table"""

    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(RefundStatus), default=RefundStatus.REQUESTED, nullable=False)
    processed_by = Column(Integer, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transaction = relationship("Transaction", back_populates="refunds")


# Repositories
class DBTransactionRepository(TransactionRepository):
    """SQLAlchemy implementation of TransactionRepository"""

    def create_transaction(self, transaction: TransactionCreate) -> TransactionInDB:
        with SessionLocal() as db:
            db_transaction = Transaction(
                user_id=transaction.user_id,
                order_id=transaction.order_id,
                transaction_type=transaction.transaction_type.value,
                amount=float(transaction.amount),
                currency=transaction.currency,
                status=transaction.status.value,
                payment_method=transaction.payment_method.value
                if transaction.payment_method
                else None,
                payment_gateway=transaction.payment_gateway.value
                if transaction.payment_gateway
                else None,
                gateway_transaction_id=transaction.gateway_transaction_id,
                metadata=transaction.metadata,
            )
            db.add(db_transaction)
            db.commit()
            db.refresh(db_transaction)
            return self._to_domain_model(db_transaction)

    def get_transaction(self, transaction_id: int) -> Optional[TransactionInDB]:
        with SessionLocal() as db:
            db_transaction = (
                db.query(Transaction).filter(Transaction.id == transaction_id).first()
            )
            return self._to_domain_model(db_transaction) if db_transaction else None

    def get_transactions_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100, status: Optional[TransactionStatus] = None
    ) -> List[TransactionInDB]:
        with SessionLocal() as db:
            db_transactions = (
                db.query(Transaction)
                .filter(Transaction.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
            if status:
                db_transactions = db_transactions.filter(Transaction.status == status.value)
            return [self._to_domain_model(t) for t in db_transactions]

    def update_transaction(
        self, transaction_id: int, transaction: TransactionUpdate
    ) -> Optional[TransactionInDB]:
        with SessionLocal() as db:
            db_transaction = (
                db.query(Transaction).filter(Transaction.id == transaction_id).first()
            )

            if not db_transaction:
                return None

            update_data = transaction.dict(exclude_unset=True)
            for field, value in update_data.items():
                # metadata should be added, not replaced with the new value. or deleted if the value is None
                if field == "metadata" and value is not None:
                    if db_transaction.metadata is None:
                        db_transaction.metadata = {}
                    db_transaction.metadata.update(value)
                elif hasattr(db_transaction, field):
                    setattr(db_transaction, field, value)

            db.commit()
            db.refresh(db_transaction)
            return self._to_domain_model(db_transaction)

    def delete_transaction(self, transaction_id: int) -> bool:
        with SessionLocal() as db:
            result = (
                db.query(Transaction).filter(Transaction.id == transaction_id).delete()
            )
            db.commit()
            # result = 1 if 1 row is deleted
            return result == 1

    # Reusable function to convert db model to domain model
    def _to_domain_model(self, db_transaction: Transaction) -> TransactionInDB:
        return TransactionInDB(
            id=db_transaction.id,
            user_id=db_transaction.user_id,
            order_id=db_transaction.order_id,
            transaction_type=TransactionType(db_transaction.transaction_type),
            amount=float(db_transaction.amount),
            currency=db_transaction.currency,
            status=TransactionStatus(db_transaction.status),
            payment_method=PaymentMethod(db_transaction.payment_method)
            if db_transaction.payment_method
            else None,
            payment_gateway=PaymentGateway(db_transaction.payment_gateway)
            if db_transaction.payment_gateway
            else None,
            gateway_transaction_id=db_transaction.gateway_transaction_id,
            metadata=db_transaction.metadata or {},
            created_at=db_transaction.created_at,
            updated_at=getattr(db_transaction, "updated_at", None),
        )


class DBOrderRepository(OrderRepository):
    """SQLAlchemy implementation of OrderRepository"""

    def create_order(self, order: OrderCreate) -> OrderInDB:
        with SessionLocal() as db:
            db_order = Order(
                user_id=order.user_id,
                order_number=order.order_number,
                service_type=order.service_type.value,
                service_id=order.metadata.get("service_id", ""),
                quantity=len(order.items) if order.items else 0,
                unit_price=order.subtotal / max(1, len(order.items))
                if order.items
                else 0,
                total_amount=order.total,
                status=order.status.value,
                booking_details={
                    "items": order.items,
                    "subtotal": order.subtotal,
                    "tax": order.tax,
                    "discount": order.discount,
                    "total": order.total,
                },
            )
            db.add(db_order)
            db.commit()
            db.refresh(db_order)
            return self._to_domain_model(db_order)

    def get_order(self, order_id: int) -> Optional[OrderInDB]:
        with SessionLocal() as db:
            db_order = db.query(Order).filter(Order.id == order_id).first()
            return self._to_domain_model(db_order) if db_order else None

    def get_orders_by_user(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrderInDB]:
        with SessionLocal() as db:
            query = db.query(Order).filter(Order.user_id == user_id)
            if status is not None:
                query = query.filter(Order.status == status.value)

            db_orders = query.offset(skip).limit(limit).all()
            return [self._to_domain_model(o) for o in db_orders]

    def update_order_status(
        self, order_id: int, status: OrderStatus
    ) -> Optional[OrderInDB]:
        with SessionLocal() as db:
            db_order = db.query(Order).filter(Order.id == order_id).first()
            if not db_order:
                return None

            db_order.status = status.value
            db_order.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_order)
        return self._to_domain_model(db_order)

    def _to_domain_model(self, db_order: Order) -> OrderInDB:
        booking_details = db_order.booking_details or {}
        return OrderInDB(
            id=db_order.id,
            user_id=db_order.user_id,
            order_number=db_order.order_number,
            service_type=ServiceType(db_order.service_type),
            items=booking_details.get("items", []),
            subtotal=float(booking_details.get("subtotal", 0)),
            tax=float(booking_details.get("tax", 0)),
            discount=float(booking_details.get("discount", 0)),
            total=float(db_order.total_amount),
            status=OrderStatus(db_order.status),
            metadata={
                "service_id": db_order.service_id,
                "quantity": db_order.quantity,
                "unit_price": float(db_order.unit_price),
            },
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
        )


class DBPaymentRepository(PaymentRepository):
    """SQLAlchemy implementation of PaymentRepository"""

    def create_payment(self, payment: PaymentCreate) -> PaymentInDB:
        with SessionLocal() as db:
            db_payment = Payment(
                transaction_id=payment.transaction_id,
                payment_method=payment.payment_method.value,
                amount=float(payment.amount),
                currency=payment.currency,
                status=payment.status.value,
                gateway_response=payment.metadata,
            )
            db.add(db_payment)
            db.commit()
            db.refresh(db_payment)
            return self._to_domain_model(db_payment)

    def get_payment(self, payment_id: int) -> Optional[PaymentInDB]:
        with SessionLocal() as db:
            db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
            return self._to_domain_model(db_payment) if db_payment else None

    def get_payments_by_transaction(self, transaction_id: int) -> List[PaymentInDB]:
        with SessionLocal() as db:
            db_payments = (
                db.query(Payment).filter(Payment.transaction_id == transaction_id).all()
            )
            return [self._to_domain_model(p) for p in db_payments]

    def update_payment_status(
        self,
        payment_id: int,
        status: TransactionStatus,
        gateway_transaction_id: Optional[str] = None,
    ) -> Optional[PaymentInDB]:
        with SessionLocal() as db:
            db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if not db_payment:
                return None

            db_payment.status = status.value
            if gateway_transaction_id is not None:
                db_payment.gateway_transaction_id = gateway_transaction_id
            db_payment.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_payment)
            return self._to_domain_model(db_payment)

    def _to_domain_model(self, db_payment: Payment) -> PaymentInDB:
        return PaymentInDB(
            id=db_payment.id,
            transaction_id=db_payment.transaction_id,
            amount=float(db_payment.amount),
            currency=db_payment.currency,
            payment_method=PaymentMethod(db_payment.payment_method),
            payment_gateway=PaymentGateway(
                getattr(db_payment, "payment_gateway", "dummy")
            ),
            gateway_transaction_id=db_payment.gateway_transaction_id,
            status=PaymentStatus(db_payment.status),
            metadata=db_payment.gateway_response or {},
            created_at=db_payment.created_at,
            updated_at=db_payment.updated_at,
        )


class DBRefundRepository(RefundRepository):
    """SQLAlchemy implementation of RefundRepository"""

    def create_refund(self, refund: RefundCreate) -> RefundInDB:
        with SessionLocal() as db:
            db_refund = Refund(
                transaction_id=refund.transaction_id,
                amount=float(refund.amount),
                reason=refund.reason,
                status=refund.status.value,
                processed_by=refund.processed_by,
                processed_at=refund.processed_at,
            )
            db.add(db_refund)
            db.commit()
            db.refresh(db_refund)
            return self._to_domain_model(db_refund)

    def get_refund(self, refund_id: int) -> Optional[RefundInDB]:
        with SessionLocal() as db:
            db_refund = db.query(Refund).filter(Refund.id == refund_id).first()
            return self._to_domain_model(db_refund) if db_refund else None

    def get_refunds_by_transaction(self, transaction_id: int) -> List[RefundInDB]:
        with SessionLocal() as db:
            db_refunds = (
                db.query(Refund).filter(Refund.transaction_id == transaction_id).all()
            )
            return [self._to_domain_model(r) for r in db_refunds]

    def update_refund_status(
        self,
        refund_id: int,
        status: RefundStatus,
        processed_by: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[RefundInDB]:
        with SessionLocal() as db:
            db_refund = db.query(Refund).filter(Refund.id == refund_id).first()
            if not db_refund:
                return None

            db_refund.status = status.value
            if processed_by is not None:
                db_refund.processed_by = processed_by
            if notes is not None:
                db_refund.reason = notes  # Using reason field for notes as per schema

            if status == RefundStatus.COMPLETED and not db_refund.processed_at:
                db_refund.processed_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(db_refund)
            return self._to_domain_model(db_refund)

    def _to_domain_model(self, db_refund: Refund) -> RefundInDB:
        return RefundInDB(
            id=db_refund.id,
            transaction_id=db_refund.transaction_id,
            amount=float(db_refund.amount),
            reason=db_refund.reason or "",
            status=RefundStatus(db_refund.status),
            processed_by=db_refund.processed_by,
            processed_at=db_refund.processed_at,
            notes=db_refund.reason,  # Reusing reason field for notes
            created_at=db_refund.created_at,
            updated_at=db_refund.processed_at,  # Using processed_at as updated_at
        )
