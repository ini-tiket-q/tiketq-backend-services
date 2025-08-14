import os
import json
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Enum, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import UUID
import uuid

from domain.models import PaymentResponse, PaymentStatus, PaymentMethod
from domain.repository import PaymentStorageRepository

Base = declarative_base()


class PaymentRecord(Base):
    """SQLAlchemy model for payment records"""
    __tablename__ = "payments"  # Table name in shared database

    # Use UUID for primary key
    payment_id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(255), index=True, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, index=True)
    amount = Column(DECIMAL(15, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    transaction_time = Column(DateTime, nullable=False)
    expiry_time = Column(DateTime, nullable=True)
    payment_url = Column(Text, nullable=True)
    token = Column(String(500), nullable=True)
    redirect_url = Column(Text, nullable=True)
    qr_code_url = Column(Text, nullable=True)
    virtual_account_number = Column(String(255), nullable=True)
    bank_code = Column(String(50), nullable=True)
    additional_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PaymentRecord(payment_id='{self.payment_id}', order_id='{self.order_id}', status='{self.status}')>"


class DatabaseAdapter(PaymentStorageRepository):
    """
    PostgreSQL database adapter for storing payment records in shared tiketq_db.
    """

    def __init__(self, db_url: str = None):
        """
        Initialize database adapter with connection URL for shared database
        """
        if not db_url:
            # Read from secrets files (Docker secrets)
            try:
                with open('/run/secrets/db_user', 'r') as f:
                    db_user = f.read().strip()
                with open('/run/secrets/db_password', 'r') as f:
                    db_password = f.read().strip()

                db_url = f"postgresql://{db_user}:{db_password}@postgres:5432/tiketq_db"
            except FileNotFoundError:
                # Fallback for development
                db_user = os.getenv("POSTGRES_USER", "tiketq_user")
                db_password = os.getenv("POSTGRES_PASSWORD", "tiketq_password")
                db_host = os.getenv("POSTGRES_HOST", "postgres")
                db_name = os.getenv("POSTGRES_DB", "tiketq_db")

                db_url = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"

        print(f"Connecting to shared database: {db_url.split('@')[1]}")  # Don't log credentials

        # Configure engine for PostgreSQL
        self.engine = create_engine(
            db_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        self.Session = sessionmaker(bind=self.engine)

        # Create payment tables if they don't exist
        self._create_payment_tables()

    def _create_payment_tables(self):
        """Create payment-specific tables in shared database"""
        try:
            # Only create payment tables, don't interfere with other service tables
            PaymentRecord.__table__.create(self.engine, checkfirst=True)
            print("Payment tables created/verified successfully in tiketq_db")
        except Exception as e:
            print(f"Error creating payment tables: {e}")
            raise

    def _payment_record_to_response(self, record: PaymentRecord) -> PaymentResponse:
        """Convert database record to domain model"""
        metadata = {}
        if record.token:
            metadata["token"] = record.token
        if record.redirect_url:
            metadata["redirect_url"] = record.redirect_url
        if record.qr_code_url:
            metadata["qr_code_url"] = record.qr_code_url
        if record.virtual_account_number:
            metadata["virtual_account_number"] = record.virtual_account_number
        if record.bank_code:
            metadata["bank_code"] = record.bank_code
        if record.additional_data:
            try:
                additional = json.loads(record.additional_data)
                metadata.update(additional)
            except (json.JSONDecodeError, TypeError):
                metadata["additional_data"] = record.additional_data

        return PaymentResponse(
            id=record.payment_id,
            order_id=record.order_id,
            transaction_id=record.payment_id,
            amount=float(record.amount),
            status=record.status,
            payment_method=record.payment_method,
            payment_url=record.payment_url,
            created_at=record.created_at,
            updated_at=record.updated_at,
            metadata=metadata if metadata else None
        )

    async def save_payment(self, payment: PaymentResponse) -> None:
        """Save payment record to shared database"""
        session = self.Session()
        try:
            existing = session.query(PaymentRecord).filter_by(payment_id=payment.id).first()

            if existing:
                # Update existing record
                existing.status = payment.status
                existing.amount = payment.amount
                existing.payment_method = payment.payment_method
                existing.transaction_time = payment.created_at
                existing.payment_url = payment.payment_url
                existing.updated_at = datetime.utcnow()

                if payment.metadata:
                    existing.token = payment.metadata.get("token")
                    existing.redirect_url = payment.metadata.get("redirect_url")
                    existing.qr_code_url = payment.metadata.get("qr_code_url")
                    existing.virtual_account_number = payment.metadata.get("virtual_account_number")
                    existing.bank_code = payment.metadata.get("bank_code")
                    existing.additional_data = json.dumps(payment.metadata)

            else:
                # Create new record
                new_payment = PaymentRecord(
                    payment_id=payment.id,
                    order_id=payment.order_id,
                    status=payment.status,
                    amount=payment.amount,
                    payment_method=payment.payment_method,
                    transaction_time=payment.created_at,
                    payment_url=payment.payment_url,
                    created_at=payment.created_at,
                    updated_at=payment.updated_at
                )

                if payment.metadata:
                    new_payment.token = payment.metadata.get("token")
                    new_payment.redirect_url = payment.metadata.get("redirect_url")
                    new_payment.qr_code_url = payment.metadata.get("qr_code_url")
                    new_payment.virtual_account_number = payment.metadata.get("virtual_account_number")
                    new_payment.bank_code = payment.metadata.get("bank_code")
                    new_payment.additional_data = json.dumps(payment.metadata)

                session.add(new_payment)

            session.commit()
            print(f"Payment saved to shared database: {payment.id}")

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Database error saving payment: {e}")
            raise ValueError(f"Failed to save payment: {str(e)}")
        finally:
            session.close()

    async def get_payment(self, payment_id: str) -> Optional[PaymentResponse]:
        """Retrieve payment record from shared database"""
        session = self.Session()
        try:
            record = session.query(PaymentRecord).filter_by(payment_id=payment_id).first()

            if record:
                return self._payment_record_to_response(record)

            return None

        except SQLAlchemyError as e:
            print(f"Database error getting payment: {e}")
            raise ValueError(f"Failed to get payment: {str(e)}")
        finally:
            session.close()

    async def update_payment_status(self, payment_id: str, status: PaymentStatus) -> None:
        """Update payment status in shared database"""
        session = self.Session()
        try:
            record = session.query(PaymentRecord).filter_by(payment_id=payment_id).first()

            if record:
                record.status = status
                record.updated_at = datetime.utcnow()
                session.commit()
                print(f"Payment status updated in shared DB: {payment_id} -> {status}")
            else:
                raise ValueError(f"Payment with ID {payment_id} not found")

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Database error updating payment status: {e}")
            raise ValueError(f"Failed to update payment status: {str(e)}")
        finally:
            session.close()

    async def get_payments_by_order(self, order_id: str) -> List[PaymentResponse]:
        """Get all payments associated with an order from shared database"""
        session = self.Session()
        try:
            records = session.query(PaymentRecord).filter_by(order_id=order_id).order_by(PaymentRecord.created_at.desc()).all()

            return [self._payment_record_to_response(record) for record in records]

        except SQLAlchemyError as e:
            print(f"Database error getting payments by order: {e}")
            raise ValueError(f"Failed to get payments by order ID: {str(e)}")
        finally:
            session.close()

    async def get_payments_by_order_id(self, order_id: str) -> List[PaymentResponse]:
        """Alias method for compatibility"""
        return await self.get_payments_by_order(order_id)

    def health_check(self) -> bool:
        """Check shared database connection health"""
        try:
            session = self.Session()
            session.execute("SELECT 1")
            session.close()
            return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False
