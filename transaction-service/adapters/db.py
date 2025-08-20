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
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

import os
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from typing import List, Optional
from datetime import datetime, timezone

from domain.models import (
    TransactionInDB,
    TransactionCreate,
    TransactionUpdate,
    TransactionStatus,
    TransactionType,
    OrderInDB,
    OrderCreate,
    OrderUpdate,
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
from domain.repository import (
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


# Database session provider - infrastructure concern
class DatabaseSessionProvider:
    """Provides database sessions for the application layer"""
    
    def __init__(self):
        self.session_factory = SessionLocal
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.session_factory()
    
    def close_session(self, session: Session):
        """Close a database session"""
        session.close()


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
    meta_data = Column("metadata", JSON, nullable=True)
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
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT, nullable=False)
    meta_data = Column("metadata", JSON, nullable=True)
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
    meta_data = Column("metadata", JSON, nullable=True)
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
    status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
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

    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, transaction: TransactionCreate) -> TransactionInDB:
        # Set current timestamp for created_at and updated_at
        now = datetime.now(timezone.utc)
        
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
            meta_data=transaction.metadata,
            created_at=now,
            updated_at=now,
        )
        
        try:
            self.db.add(db_transaction)
            self.db.commit()
            self.db.refresh(db_transaction)
            return self._to_domain_model(db_transaction)
        except Exception as e:
            self.db.rollback()
            raise e

    def get_transaction(self, transaction_id: int) -> Optional[TransactionInDB]:
        db_transaction = (
            self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        )
        return self._to_domain_model(db_transaction) if db_transaction else None

    def get_transactions_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100, status: Optional[TransactionStatus] = None
    ) -> List[TransactionInDB]:
        db_transactions = (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        if status:
            db_transactions = db_transactions.filter(Transaction.status == status.value)
        return [self._to_domain_model(t) for t in db_transactions]
    
    def get_transactions(
        self, skip: int = 0, limit: int = 100
    ) -> List[TransactionInDB]:
        """Get all transactions with pagination (admin function)"""
        from domain.services import logger
        db_transactions = (
            self.db.query(Transaction)
            .offset(skip)
            .limit(limit)
            .all()
        )
        logger.debug(f"Retrieved {len(db_transactions)} transactions")
        return [self._to_domain_model(t) for t in db_transactions]

    def update_transaction(
        self, transaction_id: int, transaction: TransactionUpdate
    ) -> Optional[TransactionInDB]:
        db_transaction = (
            self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        )

        if not db_transaction:
            return None

        update_data = transaction.dict(exclude_unset=True)
        for field, value in update_data.items():
            # metadata should be added, not replaced with the new value. or deleted if the value is None
            if field == "metadata" and value is not None:
                if db_transaction.meta_data is None:
                    db_transaction.meta_data = {}
                db_transaction.meta_data.update(value)
            elif hasattr(db_transaction, field):
                setattr(db_transaction, field, value)

        self.db.commit()
        self.db.refresh(db_transaction)
        return self._to_domain_model(db_transaction)

    def delete_transaction(self, transaction_id: int) -> bool:
        result = (
            self.db.query(Transaction).filter(Transaction.id == transaction_id).delete()
        )
        self.db.commit()
        # result = 1 if 1 row is deleted
        return result == 1

    # Reusable function to convert db model to domain model
    def _to_domain_model(self, db_transaction: Transaction) -> TransactionInDB:
        # Get current time in UTC
        now = datetime.now(timezone.utc)
        
        # Handle created_at
        if db_transaction.created_at is None:
            created_at = now
        else:
            created_at = db_transaction.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
        
        # Handle updated_at - default to created_at if None
        if db_transaction.updated_at is None:
            updated_at = created_at  # Use created_at as fallback
        else:
            updated_at = db_transaction.updated_at
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            
        return TransactionInDB(
            id=db_transaction.id,
            user_id=db_transaction.user_id,
            order_id=db_transaction.order_id,
            transaction_type=TransactionType(db_transaction.transaction_type),
            amount=db_transaction.amount,
            currency=db_transaction.currency,
            status=TransactionStatus(db_transaction.status),
            payment_method=(
                PaymentMethod(db_transaction.payment_method)
                if db_transaction.payment_method
                else None
            ),
            payment_gateway=(
                PaymentGateway(db_transaction.payment_gateway)
                if db_transaction.payment_gateway
                else None
            ),
            gateway_transaction_id=db_transaction.gateway_transaction_id,
            metadata=db_transaction.meta_data,
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_transactions_for_report(self, start_date, end_date, status_filter=None, 
                                   transaction_type_filter=None, min_amount=None, 
                                   max_amount=None, user_id=None, currency=None):
        """Get transactions for reporting with filters"""
        query = self.db.query(Transaction).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if status_filter:
            try:
                # Convert string to enum and filter
                status_enum = TransactionStatus(status_filter)
                query = query.filter(Transaction.status == status_enum.value)
            except ValueError:
                # Invalid status, return empty result
                return []
        
        if transaction_type_filter:
            try:
                # Convert string to enum and filter
                type_enum = TransactionType(transaction_type_filter)
                query = query.filter(Transaction.transaction_type == type_enum.value)
            except ValueError:
                # Invalid type, return empty result
                return []
        
        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)
        
        if user_id is not None:
            query = query.filter(Transaction.user_id == user_id)
        
        if currency:
            query = query.filter(Transaction.currency == currency)
        
        transactions = query.order_by(Transaction.created_at.desc()).all()
        return [self._to_domain_model(t) for t in transactions]

    def get_revenue_data(self, start_date, end_date, group_by="day", 
                        currency=None, service_type_filter=None, include_refunds=True):
        """Get revenue data grouped by time period"""
        # This is a simplified implementation - in production you'd use SQL aggregation
        transactions = self.get_transactions_for_report(
            start_date=start_date, 
            end_date=end_date, 
            currency=currency
        )
        
        # Group transactions by period
        revenue_data = {}
        for transaction in transactions:
            # Determine period key based on group_by
            if group_by == "day":
                period_key = transaction.created_at.strftime("%Y-%m-%d")
            elif group_by == "week":
                period_key = transaction.created_at.strftime("%Y-W%U")
            elif group_by == "month":
                period_key = transaction.created_at.strftime("%Y-%m")
            else:
                period_key = transaction.created_at.strftime("%Y-%m-%d")
            
            if period_key not in revenue_data:
                revenue_data[period_key] = {
                    "period": period_key,
                    "revenue": 0.0,
                    "transaction_count": 0,
                    "refund_amount": 0.0
                }
            
            # Only count completed transactions for revenue
            if transaction.status == TransactionStatus.COMPLETED:
                revenue_data[period_key]["revenue"] += transaction.amount
                revenue_data[period_key]["transaction_count"] += 1
            
            # Count refunds if enabled
            if include_refunds and transaction.status == TransactionStatus.REFUNDED:
                revenue_data[period_key]["refund_amount"] += transaction.amount
        
        return list(revenue_data.values())


class DBOrderRepository(OrderRepository):
    """SQLAlchemy implementation of OrderRepository"""

    def __init__(self, db: Session):
        self.db = db

    def create_order(self, order: OrderCreate) -> OrderInDB:
        try:
            print(f"DEBUG: Creating order with type: {type(order)}")
            print(f"DEBUG: Order attributes: {dir(order)}")
            
            # Convert TransactionItem objects to dictionaries for JSON serialization
            items_as_dicts = [
                item.model_dump() if hasattr(item, 'model_dump') else dict(item)
                for item in order.items
            ]
            
            # Create the order with current timestamps
            now = datetime.now(timezone.utc)
            db_order = Order(
                user_id=order.user_id,
                order_number=order.order_number,
                service_type=order.service_type,
                items=items_as_dicts,
                subtotal=order.subtotal,
                tax=order.tax,
                discount=order.discount,
                total=order.total,
                status=order.status,
                meta_data=order.metadata,
                created_at=now,
                updated_at=now,
            )
            
            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)
            return self._to_domain_model(db_order)
        except Exception as e:
            import traceback
            print(f"ERROR in create_order: {e}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            self.db.rollback()
            raise e

    def get_order(self, order_id: int) -> Optional[OrderInDB]:
        db_order = self.db.query(Order).filter(Order.id == order_id).first()
        return self._to_domain_model(db_order) if db_order else None

    def get_orders_by_user(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrderInDB]:
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        if status is not None:
            query = query.filter(Order.status == status)
            
        db_orders = query.offset(skip).limit(limit).all()
        return [self._to_domain_model(o) for o in db_orders]

    def update_order_status(
        self, order_id: int, status: OrderStatus
    ) -> Optional[OrderInDB]:
        db_order = self.db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None

        db_order.status = status
        db_order.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_order)
        return self._to_domain_model(db_order)
    
    def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[OrderInDB]:
        """Get all orders with optional status filter and pagination (admin function)"""
        query = self.db.query(Order)
        
        if status:
            query = query.filter(Order.status == status.value)
            
        db_orders = query.offset(skip).limit(limit).all()
        return [self._to_domain_model(order) for order in db_orders]
    
    def update_order(
        self, 
        order_id: int, 
        order: OrderUpdate
    ) -> Optional[OrderInDB]:
        """Update order with full data"""
        db_order = self.db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None

        # Update fields that are not None
        if order.status is not None:
            db_order.status = order.status.value
        if order.metadata is not None:
            db_order.meta_data = order.metadata
            
        db_order.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_order)
        return self._to_domain_model(db_order)

    def _to_domain_model(self, db_order: Order) -> OrderInDB:
        return OrderInDB(
            id=db_order.id,
            user_id=db_order.user_id,
            order_number=db_order.order_number,
            service_type=db_order.service_type,
            items=db_order.items,
            subtotal=db_order.subtotal,
            tax=db_order.tax,
            discount=db_order.discount,
            total=db_order.total,
            status=db_order.status,
            metadata=db_order.meta_data,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
        )


class DBPaymentRepository(PaymentRepository):
    """SQLAlchemy implementation of PaymentRepository"""

    def __init__(self, db: Session):
        self.db = db

    def create_payment(self, payment: PaymentCreate) -> PaymentInDB:
        db_payment = Payment(
            transaction_id=payment.transaction_id,
            payment_method=payment.payment_method.value,
            payment_gateway=payment.payment_gateway.value,
            amount=float(payment.amount),
            currency=payment.currency,
            status=payment.status.value,
            gateway_transaction_id=payment.gateway_transaction_id,
            meta_data=payment.metadata,
        )
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        return self._to_domain_model(db_payment)

    def get_payment(self, payment_id: int) -> Optional[PaymentInDB]:
        db_payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        return self._to_domain_model(db_payment) if db_payment else None

    def get_payments_by_transaction(self, transaction_id: int) -> List[PaymentInDB]:
        db_payments = (
            self.db.query(Payment).filter(Payment.transaction_id == transaction_id).all()
        )
        return [self._to_domain_model(p) for p in db_payments]

    def update_payment_status(
        self,
        payment_id: int,
        status: TransactionStatus,
        gateway_transaction_id: Optional[str] = None,
    ) -> Optional[PaymentInDB]:
        db_payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not db_payment:
            return None

        db_payment.status = status.value
        if gateway_transaction_id is not None:
            db_payment.gateway_transaction_id = gateway_transaction_id
        db_payment.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_payment)
        return self._to_domain_model(db_payment)

    def update_payment(
        self,
        payment_id: int,
        payment_data: dict
    ) -> Optional[PaymentInDB]:
        """Update payment with arbitrary data"""
        db_payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not db_payment:
            return None

        # Update fields from payment_data
        for field, value in payment_data.items():
            if field == "status" and isinstance(value, str):
                # Handle status as string value
                db_payment.status = value
            elif field == "metadata" and value is not None:
                # Merge metadata using meta_data column
                if db_payment.meta_data is None:
                    db_payment.meta_data = {}
                db_payment.meta_data.update(value)
            elif hasattr(db_payment, field):
                setattr(db_payment, field, value)

        db_payment.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_payment)
        return self._to_domain_model(db_payment)

    def _to_domain_model(self, db_payment: Payment) -> PaymentInDB:
        return PaymentInDB(
            id=db_payment.id,
            transaction_id=db_payment.transaction_id,
            amount=float(db_payment.amount),
            currency=db_payment.currency,
            payment_method=PaymentMethod(db_payment.payment_method),
            payment_gateway=PaymentGateway(db_payment.payment_gateway),
            gateway_transaction_id=db_payment.gateway_transaction_id,
            status=PaymentStatus(db_payment.status),
            metadata=db_payment.metadata,
            created_at=db_payment.created_at,
            updated_at=db_payment.updated_at,
        )


class DBRefundRepository(RefundRepository):
    """SQLAlchemy implementation of RefundRepository"""

    def __init__(self, db: Session):
        self.db = db

    def create_refund(self, refund: RefundCreate) -> RefundInDB:
        db_refund = Refund(
            transaction_id=refund.transaction_id,
            amount=float(refund.amount),
            reason=refund.reason,
            status=refund.status.value,
            processed_by=refund.processed_by,
            processed_at=refund.processed_at,
        )
        self.db.add(db_refund)
        self.db.commit()
        self.db.refresh(db_refund)
        return self._to_domain_model(db_refund)

    def get_refund(self, refund_id: int) -> Optional[RefundInDB]:
        db_refund = self.db.query(Refund).filter(Refund.id == refund_id).first()
        return self._to_domain_model(db_refund) if db_refund else None

    def get_refunds_by_transaction(self, transaction_id: int) -> List[RefundInDB]:
        db_refunds = (
            self.db.query(Refund).filter(Refund.transaction_id == transaction_id).all()
        )
        return [self._to_domain_model(r) for r in db_refunds]

    def update_refund_status(
        self,
        refund_id: int,
        status: RefundStatus,
        processed_by: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[RefundInDB]:
        db_refund = self.db.query(Refund).filter(Refund.id == refund_id).first()
        if not db_refund:
            return None

        db_refund.status = status.value
        if processed_by is not None:
            db_refund.processed_by = processed_by
        if notes is not None:
            db_refund.reason = notes  # Using reason field for notes as per schema

        if status == RefundStatus.COMPLETED and not db_refund.processed_at:
            db_refund.processed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(db_refund)
        return self._to_domain_model(db_refund)

    def get_refunds_for_report(self, start_date, end_date, status_filter=None, 
                               min_amount=None, max_amount=None, reason_filter=None, 
                               processed_by=None):
        """Get refunds for reporting with filtering options"""
        query = self.db.query(Refund)
        
        # Date range filter
        if start_date:
            query = query.filter(Refund.created_at >= start_date)
        if end_date:
            query = query.filter(Refund.created_at <= end_date)
        
        # Status filter
        if status_filter:
            try:
                status_enum = RefundStatus(status_filter)
                query = query.filter(Refund.status == status_enum.value)
            except ValueError:
                # Invalid status, return empty result
                return []
        
        # Amount range filter
        if min_amount is not None:
            query = query.filter(Refund.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Refund.amount <= max_amount)
        
        # Reason filter (keyword search)
        if reason_filter:
            query = query.filter(Refund.reason.ilike(f"%{reason_filter}%"))
        
        # Processed by filter
        if processed_by is not None:
            query = query.filter(Refund.processed_by == processed_by)
        
        # Execute query and convert to domain models
        db_refunds = query.all()
        return [self._to_domain_model(refund) for refund in db_refunds]

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
