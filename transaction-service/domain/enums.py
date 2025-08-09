from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class RefundStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Currency(str, Enum):
    IDR = "IDR"
    # USD = "USD"
    # EUR = "EUR"
    # SGD = "SGD"

class ServiceType(str, Enum):
    FLIGHTS = "FLIGHTS"
    HOTELS = "HOTELS"
    FERRIES = "FERRIES"
    PPOB = "PPOB"

class TransactionType(str, Enum):
    BOOKING = "BOOKING"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    CANCELLATION = "CANCELLATION"

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

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
