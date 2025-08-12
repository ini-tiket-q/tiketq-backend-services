from abc import ABC, abstractmethod
from typing import List, Optional
from .models import (
    TransactionInDB, TransactionCreate, TransactionUpdate, TransactionStatus,
    OrderInDB, OrderCreate, OrderUpdate, OrderStatus,
    PaymentInDB, PaymentCreate,
    RefundInDB, RefundCreate, RefundStatus
)

# abstractmethod will raise NotImplementedError if not implemented
class TransactionRepository(ABC):
    """Abstract base class for transaction data access"""
    
    @abstractmethod
    def create_transaction(self, transaction: TransactionCreate) -> TransactionInDB:
        """Create a new transaction"""
        pass
    
    @abstractmethod
    def get_transaction(self, transaction_id: int) -> Optional[TransactionInDB]:
        """Get a transaction by ID"""
        pass
    
    @abstractmethod
    def get_transactions_by_user(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionInDB]:
        """Get transactions for a specific user with pagination"""
        pass
    
    @abstractmethod
    def get_transactions(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionInDB]:
        """Get all transactions with pagination (admin function)"""
        pass
    
    @abstractmethod
    def update_transaction(
        self, 
        transaction_id: int, 
        transaction: TransactionUpdate
    ) -> Optional[TransactionInDB]:
        """Update a transaction"""
        pass
    
    @abstractmethod
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        pass

class OrderRepository(ABC):
    """Abstract base class for order data access"""
    
    @abstractmethod
    def create_order(self, order: OrderCreate) -> OrderInDB:
        """Create a new order"""
        pass
    
    @abstractmethod
    def get_order(self, order_id: int) -> Optional[OrderInDB]:
        """Get an order by ID"""
        pass
    
    @abstractmethod
    def get_orders_by_user(
        self, 
        user_id: int, 
        status: Optional[OrderStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[OrderInDB]:
        """Get orders for a specific user with optional status filter and pagination"""
        pass
    
    @abstractmethod
    def update_order_status(
        self, 
        order_id: int, 
        status: OrderStatus
    ) -> Optional[OrderInDB]:
        """Update order status"""
        pass
    
    @abstractmethod
    def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[OrderInDB]:
        """Get all orders with optional status filter and pagination (admin function)"""
        pass
    
    @abstractmethod
    def update_order(
        self, 
        order_id: int, 
        order: OrderUpdate
    ) -> Optional[OrderInDB]:
        """Update order with full data"""
        pass

class PaymentRepository(ABC):
    """Abstract base class for payment data access"""
    
    @abstractmethod
    def create_payment(self, payment: PaymentCreate) -> PaymentInDB:
        """Create a new payment record"""
        pass
    
    @abstractmethod
    def get_payment(self, payment_id: int) -> Optional[PaymentInDB]:
        """Get a payment by ID"""
        pass
    
    @abstractmethod
    def get_payments_by_transaction(
        self, 
        transaction_id: int
    ) -> List[PaymentInDB]:
        """Get all payments for a transaction"""
        pass
    
    @abstractmethod
    def update_payment_status(
        self, 
        payment_id: int, 
        status: TransactionStatus,
        gateway_transaction_id: Optional[str] = None
    ) -> Optional[PaymentInDB]:
        """Update payment status and optional gateway transaction ID"""
        pass

class RefundRepository(ABC):
    """Abstract base class for refund data access"""
    
    @abstractmethod
    def create_refund(self, refund: RefundCreate) -> RefundInDB:
        """Create a new refund request"""
        pass
    
    @abstractmethod
    def get_refund(self, refund_id: int) -> Optional[RefundInDB]:
        """Get a refund by ID"""
        pass
    
    @abstractmethod
    def get_refunds_by_transaction(
        self, 
        transaction_id: int
    ) -> List[RefundInDB]:
        """Get all refunds for a transaction"""
        pass
    
    @abstractmethod
    def update_refund_status(
        self, 
        refund_id: int, 
        status: RefundStatus,
        processed_by: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Optional[RefundInDB]:
        """Update refund status and processing information"""
        pass

