from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from ..domain.models import PaymentResponse, PaymentStatus, PaymentMethod
from ..domain.repository import PaymentStorageRepository

Base = declarative_base()


class PaymentRecord(Base):
    """SQLAlchemy model for payment records"""
    __tablename__ = "payments"
    
    payment_id = Column(String(255), primary_key=True)
    order_id = Column(String(255), index=True, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    transaction_time = Column(DateTime, nullable=False)
    expiry_time = Column(DateTime, nullable=True)
    payment_url = Column(String(512), nullable=True)
    token = Column(String(255), nullable=True)
    redirect_url = Column(String(512), nullable=True)
    qr_code_url = Column(String(512), nullable=True)
    virtual_account_number = Column(String(255), nullable=True)
    bank_code = Column(String(50), nullable=True)
    additional_data = Column(Text, nullable=True)  # For storing any additional JSON data
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DatabaseAdapter(PaymentStorageRepository):
    """
    Database adapter for storing payment records.
    Implements the PaymentStorageRepository interface (port).
    """
    
    def __init__(self, db_url: str):
        """
        Initialize database adapter with connection URL
        
        Args:
            db_url: Database connection URL
        """
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
    
    def _payment_record_to_response(self, record: PaymentRecord) -> PaymentResponse:
        """
        Convert database record to domain model
        
        Args:
            record: Database record
            
        Returns:
            PaymentResponse: Domain model
        """
        return PaymentResponse(
            payment_id=record.payment_id,
            order_id=record.order_id,
            status=record.status,
            amount=record.amount,
            payment_method=record.payment_method,
            transaction_time=record.transaction_time,
            expiry_time=record.expiry_time,
            payment_url=record.payment_url,
            token=record.token,
            redirect_url=record.redirect_url,
            qr_code_url=record.qr_code_url,
            virtual_account_number=record.virtual_account_number,
            bank_code=record.bank_code
        )
    
    async def save_payment(self, payment: PaymentResponse) -> None:
        """
        Save payment record to database
        
        Args:
            payment: Payment response to save
        """
        session = self.Session()
        try:
            # Check if payment already exists
            existing = session.query(PaymentRecord).filter_by(payment_id=payment.payment_id).first()
            
            if existing:
                # Update existing record
                existing.status = payment.status
                existing.amount = payment.amount
                existing.payment_method = payment.payment_method
                existing.transaction_time = payment.transaction_time
                existing.expiry_time = payment.expiry_time
                existing.payment_url = payment.payment_url
                existing.token = payment.token
                existing.redirect_url = payment.redirect_url
                existing.qr_code_url = payment.qr_code_url
                existing.virtual_account_number = payment.virtual_account_number
                existing.bank_code = payment.bank_code
                existing.updated_at = datetime.now()
            else:
                # Create new record
                record = PaymentRecord(
                    payment_id=payment.payment_id,
                    order_id=payment.order_id,
                    status=payment.status,
                    amount=payment.amount,
                    payment_method=payment.payment_method,
                    transaction_time=payment.transaction_time,
                    expiry_time=payment.expiry_time,
                    payment_url=payment.payment_url,
                    token=payment.token,
                    redirect_url=payment.redirect_url,
                    qr_code_url=payment.qr_code_url,
                    virtual_account_number=payment.virtual_account_number,
                    bank_code=payment.bank_code,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(record)
            
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise ValueError(f"Failed to save payment: {str(e)}")
        finally:
            session.close()
    
    async def get_payment(self, payment_id: str) -> Optional[PaymentResponse]:
        """
        Retrieve payment record from database
        
        Args:
            payment_id: ID of payment to retrieve
            
        Returns:
            Optional[PaymentResponse]: Payment record if found, None otherwise
        """
        session = self.Session()
        try:
            record = session.query(PaymentRecord).filter_by(payment_id=payment_id).first()
            
            if record:
                return self._payment_record_to_response(record)
            else:
                return None
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to get payment: {str(e)}")
        finally:
            session.close()
    
    async def update_payment_status(self, payment_id: str, status: PaymentStatus) -> None:
        """
        Update payment status in database
        
        Args:
            payment_id: ID of payment to update
            status: New payment status
        """
        session = self.Session()
        try:
            record = session.query(PaymentRecord).filter_by(payment_id=payment_id).first()
            
            if record:
                record.status = status
                record.updated_at = datetime.now()
                session.commit()
            else:
                raise ValueError(f"Payment with ID {payment_id} not found")
        except SQLAlchemyError as e:
            session.rollback()
            raise ValueError(f"Failed to update payment status: {str(e)}")
        finally:
            session.close()
    
    async def get_payments_by_order_id(self, order_id: str) -> List[PaymentResponse]:
        """
        Get all payments associated with an order
        
        Args:
            order_id: Order ID to search for
            
        Returns:
            List[PaymentResponse]: List of payments for the order
        """
        session = self.Session()
        try:
            records = session.query(PaymentRecord).filter_by(order_id=order_id).all()
            
            return [self._payment_record_to_response(record) for record in records]
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to get payments by order ID: {str(e)}")
        finally:
            session.close()
