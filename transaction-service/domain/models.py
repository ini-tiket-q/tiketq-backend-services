from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from uuid import uuid4

from .model_configs import ModelConfigs, ValidationMessages


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
    credit_card = "credit_card"
    bank_transfer = "bank_transfer"
    e_wallet = "e_wallet"
    qris = "qris"
    retail = "retail"


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
    SUCCESS = "SUCCESS"  # Changed from COMPLETED to match database enum
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    EXPIRED = "EXPIRED"  # Added to match database enum


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

# Transaction Item Model
class TransactionItem(BaseModel):
    """Individual item in a transaction"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "customer@example.com",
                "name": "Jakarta to Bali Flight",
                "price": 850000,
                "quantity": 1,
                "description": "Economy class flight from Jakarta (CGK) to Bali (DPS)",
                "metadata": {
                    "departure_date": "2025-09-15",
                    "flight_number": "GA-123",
                    "airline": "Garuda Indonesia",
                    "class": "Economy",
                },
            }
        }
    )

    name: str = Field(..., max_length=200, description="Item name")
    price: float = Field(..., gt=0, description="Item price")
    quantity: int = Field(..., gt=0, description="Item quantity")
    description: Optional[str] = Field(
        None, max_length=500, description="Item description"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Item metadata")


class TransactionBase(BaseModel):
    email: str = Field(
        ..., description="Email of the user who made the transaction", max_length=255
    )
    order_number: str = Field(default_factory=lambda: f"ORD-{uuid4().hex[:8].upper()}")
    transaction_type: TransactionType
    amount: float
    currency: Currency = Currency.IDR
    status: TransactionStatus = TransactionStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    payment_gateway: Optional[PaymentGateway] = None
    gateway_transaction_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    payment_url: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    payment_method: Optional[PaymentMethod] = None
    payment_gateway: Optional[PaymentGateway] = None
    gateway_transaction_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TransactionInDB(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    email: str = Field(
        ..., description="Email of the user who placed the order", max_length=255
    )
    order_number: str = Field(
        default_factory=lambda: f"ORD-{uuid4().hex[:8].upper()}",
        description="Unique order number",
    )
    service_type: ServiceType = Field(..., description="Type of service being ordered")
    items: List[TransactionItem] = Field(
        default_factory=list, description="List of items in the order"
    )
    subtotal: float = Field(..., ge=0, description="Subtotal before tax and discount")
    tax: float = Field(default=0.0, ge=0, description="Tax amount")
    discount: float = Field(default=0.0, ge=0, description="Discount amount")
    total: float = Field(..., ge=0, description="Total amount after tax and discount")
    status: OrderStatus = Field(
        default=OrderStatus.DRAFT, description="Current status of the order"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional order metadata"
    )


class OrderCreate(OrderBase):
    """Request model for creating a new order with validation"""

    @model_validator(mode="after")
    def validate_totals(self):
        """Validate that the calculated totals match the provided values"""
        # Calculate expected total
        calculated_total = self.subtotal + self.tax - self.discount

        # Ensure total matches the calculated total within a small tolerance
        if (
            abs(calculated_total - self.total) > 0.01
        ):  # Allow for floating point precision
            raise ValueError(
                f"Total amount {self.total} does not match the calculated total "
                f"(subtotal {self.subtotal} + tax {self.tax} - discount {self.discount} = {calculated_total})"
            )

        return self


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class OrderInDB(OrderBase):
    """Database model for orders with all fields from OrderBase plus database-specific fields"""

    id: int = Field(..., description="Unique identifier for the order")
    created_at: datetime = Field(..., description="When the order was created")
    updated_at: datetime = Field(..., description="When the order was last updated")

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy (Pydantic v2)


class PaymentBase(BaseModel):
    transaction_id: int
    amount: float
    currency: Currency = Currency.IDR
    payment_method: PaymentMethod
    payment_gateway: PaymentGateway
    gateway_transaction_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    gateway_transaction_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentInDB(PaymentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
        from_attributes = True


# =============================================================================
# API Request Models for Payment Validation
# =============================================================================


class PaymentCreateRequest(BaseModel):
    """Request model for creating payments with validation"""

    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    currency: Currency = Currency.IDR
    payment_method: PaymentMethod = Field(..., description="Payment method is required")
    payment_gateway: PaymentGateway = Field(
        ..., description="Payment gateway is required"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ModelConfigs.payment_create_config()

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError(ValidationMessages.AMOUNT_POSITIVE)
        if v > 999999999:  # 999 million max
            raise ValueError(ValidationMessages.AMOUNT_MAX_EXCEEDED)
        return v


class PaymentConfirmRequest(BaseModel):
    """Request model for confirming payments"""

    gateway_response: Dict[str, Any] = Field(default_factory=dict)
    token: str = Field(..., description="Token for payment authentication")
    notes: Optional[str] = Field(None, max_length=500)


class PaymentWebhookRequest(BaseModel):
    """Request model for payment webhook validation"""

    payment_id: int = Field(..., gt=0)
    status: str = Field(..., min_length=1, max_length=50)
    gateway_response: Dict[str, Any] = Field(default_factory=dict)
    signature: Optional[str] = Field(
        None, description="Webhook signature for verification"
    )


# Order Request Models
class OrderCreateRequest(BaseModel):
    """Request model for order creation validation"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service_type": "FLIGHTS",
                "items": [
                    {
                        "name": "Jakarta to Bali Flight",
                        "price": 850000,
                        "quantity": 1,
                        "description": "Economy class flight from Jakarta (CGK) to Bali (DPS)",
                        "metadata": {
                            "departure_date": "2025-09-15",
                            "flight_number": "GA-123",
                            "airline": "Garuda Indonesia",
                            "class": "Economy",
                        },
                    }
                ],
                "tax": 85000,
                "discount": 50000,
                "metadata": {
                    "passenger_name": "John Doe",
                    "booking_reference": "TQ-FL-001",
                    "special_requests": "Window seat preferred",
                },
            }
        }
    )
    service_type: ServiceType = Field(..., description="Type of service being ordered")
    items: List[TransactionItem] = Field(..., min_length=1, description="Order items")
    tax: float = Field(0.0, ge=0, description="Tax amount")
    discount: float = Field(0.0, ge=0, description="Discount amount")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional order metadata"
    )

    model_config = ModelConfigs.order_create_config()

    @field_validator("tax", "discount")
    @classmethod
    def validate_amounts(cls, v):
        """Validate tax and discount amounts"""
        if v < 0:
            raise ValueError("Tax and discount must be non-negative")
        return v


class OrderStatusUpdateRequest(BaseModel):
    """Request model for order status update validation"""

    status: OrderStatus = Field(..., description="New order status")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for status update"
    )

    @field_validator("status")
    @classmethod
    def validate_status_transition(cls, v):
        """Validate status transition logic"""
        # Add business logic for valid status transitions if needed
        valid_statuses = [status.value for status in OrderStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v


# Transaction Request Models
class TransactionCreateRequest(BaseModel):
    """Request model for transaction creation validation"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "customer@example.com",
                "transaction_type": "BOOKING",
                "currency": "IDR",
                "service_type": "FLIGHTS",
                "items": [
                    {
                        "name": "Jakarta to Bali Flight",
                        "price": 850000,
                        "quantity": 1,
                        "description": "Economy class flight from Jakarta (CGK) to Bali (DPS)",
                        "metadata": {
                            "departure_date": "2025-09-15",
                            "flight_number": "GA-123",
                            "airline": "Garuda Indonesia",
                            "class": "Economy",
                        },
                    }
                ],
                "subtotal": 850000,
                "tax": 85000,
                "discount": 50000,
                "total": 885000,
                "payment_method": "credit_card",
                "payment_gateway": "MIDTRANS",
                "transaction_metadata": {
                    "order_id": "ORD-79AFA780",
                    "passenger_name": "John Doe",
                    "booking_reference": "TQ-FL-001",
                    "ip_address": "192.168.1.100",
                },
                "payment_metadata": {
                    "bank_name": "BCA",
                    "card_last_digits": "1234",
                    "card_type": "visa",
                },
            }
        }
    )
    email: str = Field(
        ..., max_length=255, description="Email of the user making the transaction"
    )
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    currency: Currency = Field(Currency.IDR, description="Transaction currency")
    service_type: ServiceType = Field(
        ..., description="Type of service being transacted"
    )
    items: List[TransactionItem] = Field(
        ..., min_length=1, description="List of transaction items"
    )
    subtotal: Optional[float] = Field(
        None, ge=0, description="Subtotal before tax and discount"
    )
    tax: float = Field(0.0, ge=0, description="Tax amount")
    discount: float = Field(0.0, ge=0, description="Discount amount")
    total: Optional[float] = Field(None, ge=0, description="Total amount")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    payment_gateway: Optional[PaymentGateway] = Field(
        None, description="Payment gateway"
    )
    transaction_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional transaction metadata"
    )
    payment_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional payment metadata"
    )

    model_config = ModelConfigs.transaction_create_config()

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        """Validate transaction items structure"""
        if not v:
            raise ValueError(ValidationMessages.ITEMS_EMPTY)
        return v

    @field_validator("subtotal", "tax", "discount", "total")
    @classmethod
    def validate_amounts(cls, v):
        """Validate monetary amounts"""
        if v is not None and v < 0:
            raise ValueError("Amounts must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_totals(self):
        """Validate total calculation consistency"""
        if self.subtotal is None:
            # Calculate subtotal from items - items are TransactionItem objects
            self.subtotal = sum(item.price * item.quantity for item in self.items)

        if self.total is None:
            # Calculate total
            self.total = self.subtotal + self.tax - self.discount

        # Validate that total matches calculation
        expected_total = self.subtotal + self.tax - self.discount
        if (
            abs(self.total - expected_total) > 0.01
        ):  # Allow for minor floating point differences
            raise ValueError(
                f"Total {self.total} does not match calculated total {expected_total}"
            )

        return self


class TransactionUpdateRequest(BaseModel):
    """Request model for transaction update validation"""

    status: Optional[TransactionStatus] = Field(
        None, description="New transaction status"
    )
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    payment_gateway: Optional[PaymentGateway] = Field(
        None, description="Payment gateway"
    )
    gateway_transaction_id: Optional[str] = Field(
        None, max_length=255, description="Gateway transaction ID"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for update"
    )

    @field_validator("gateway_transaction_id")
    @classmethod
    def validate_gateway_id(cls, v):
        """Validate gateway transaction ID format"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Gateway transaction ID cannot be empty")
        return v


class TransactionRefundRequest(BaseModel):
    """Request model for transaction refund validation"""

    amount: Optional[float] = Field(
        None, gt=0, description="Refund amount (defaults to full amount)"
    )
    reason: str = Field(
        ..., min_length=1, max_length=500, description="Reason for refund"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        """Validate refund reason"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Refund reason cannot be empty")
        return v.strip()


# =============================================================================
# REPORT MODELS
# =============================================================================


class ReportDateRange(BaseModel):
    """Date range for report filtering"""

    start_date: datetime = Field(..., description="Start date for the report")
    end_date: datetime = Field(..., description="End date for the report")

    @model_validator(mode="after")
    def validate_date_range(self):
        """Validate that end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")

        # Limit to maximum 1 year range
        days_diff = (self.end_date - self.start_date).days
        if days_diff > 365:
            raise ValueError("Date range cannot exceed 365 days")

        return self


class TransactionReportRequest(BaseModel):
    """Request model for transaction reports validation"""

    date_range: ReportDateRange = Field(..., description="Date range for the report")
    status_filter: Optional[str] = Field(
        None, description="Filter by transaction status"
    )
    transaction_type: Optional[str] = Field(
        None, description="Filter by transaction type"
    )
    min_amount: Optional[float] = Field(
        None, ge=0, description="Minimum transaction amount"
    )
    max_amount: Optional[float] = Field(
        None, ge=0, description="Maximum transaction amount"
    )
    email: Optional[str] = Field(
        None, description="Filter by specific user's email address"
    )
    currency: Optional[str] = Field("IDR", max_length=3, description="Currency filter")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code"""
        if v and len(v) != 3:
            raise ValueError("Currency must be a 3-character code")
        return v.upper() if v else "IDR"

    @model_validator(mode="after")
    def validate_amount_range(self):
        """Validate amount range"""
        if (
            self.min_amount is not None
            and self.max_amount is not None
            and self.min_amount > self.max_amount
        ):
            raise ValueError("Minimum amount cannot be greater than maximum amount")
        return self


class RevenueReportRequest(BaseModel):
    """Request model for revenue analytics validation"""

    date_range: ReportDateRange = Field(..., description="Date range for the report")
    group_by: str = Field(
        "day", pattern="^(day|week|month)$", description="Grouping period"
    )
    currency: Optional[str] = Field("IDR", max_length=3, description="Currency filter")
    service_type_filter: Optional[List[str]] = Field(
        None, description="Filter by service types"
    )
    include_refunds: bool = Field(
        True, description="Include refunds in revenue calculation"
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code"""
        if v and len(v) != 3:
            raise ValueError("Currency must be a 3-character code")
        return v.upper() if v else "IDR"


class RefundReportRequest(BaseModel):
    """Request model for refund reports validation"""

    date_range: ReportDateRange = Field(..., description="Date range for the report")
    status_filter: Optional[str] = Field(None, description="Filter by refund status")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum refund amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum refund amount")
    reason_filter: Optional[str] = Field(
        None, max_length=100, description="Filter by refund reason keyword"
    )
    processed_by: Optional[str] = Field(
        None, description="Email of admin who processed refund"
    )

    @model_validator(mode="after")
    def validate_amount_range(self):
        """Validate amount range"""
        if (
            self.min_amount is not None
            and self.max_amount is not None
            and self.min_amount > self.max_amount
        ):
            raise ValueError("Minimum amount cannot be greater than maximum amount")
        return self


# Report Response Models
class TransactionReportData(BaseModel):
    """Transaction report data model"""

    transaction_id: int
    email: str
    order_id: str
    transaction_type: TransactionType
    amount: float
    currency: str
    status: TransactionStatus
    payment_method: Optional[PaymentMethod]
    payment_gateway: Optional[PaymentGateway]
    created_at: datetime
    updated_at: Optional[datetime]


class TransactionReportResponse(BaseModel):
    """Response model for transaction reports"""

    summary: Dict[str, Any] = Field(..., description="Report summary statistics")
    transactions: List[TransactionReportData] = Field(
        ..., description="Transaction data"
    )
    total_count: int = Field(..., description="Total number of transactions")
    total_amount: float = Field(..., description="Total transaction amount")
    date_range: ReportDateRange = Field(..., description="Report date range")


class RevenueDataPoint(BaseModel):
    """Revenue data point for time-series data"""

    period: str = Field(..., description="Time period (date/week/month)")
    revenue: float = Field(..., description="Revenue amount for the period")
    transaction_count: int = Field(..., description="Number of transactions in period")
    refund_amount: float = Field(0.0, description="Total refunds in period")


class RevenueReportResponse(BaseModel):
    """Response model for revenue analytics"""

    summary: Dict[str, Any] = Field(..., description="Revenue summary statistics")
    revenue_data: List[RevenueDataPoint] = Field(
        ..., description="Time-series revenue data"
    )
    total_revenue: float = Field(..., description="Total revenue in period")
    total_transactions: int = Field(..., description="Total number of transactions")
    total_refunds: float = Field(..., description="Total refund amount")
    date_range: ReportDateRange = Field(..., description="Report date range")


class RefundReportData(BaseModel):
    """Refund report data model"""

    refund_id: int
    transaction_id: int
    email: str
    amount: float
    reason: str
    status: RefundStatus
    processed_by: Optional[int]
    processed_at: Optional[datetime]
    created_at: datetime


class RefundReportResponse(BaseModel):
    """Response model for refund reports"""

    summary: Dict[str, Any] = Field(..., description="Refund summary statistics")
    refunds: List[RefundReportData] = Field(..., description="Refund data")
    total_count: int = Field(..., description="Total number of refunds")
    total_amount: float = Field(..., description="Total refund amount")
    date_range: ReportDateRange = Field(..., description="Report date range")


# AUTH
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserResponse(BaseModel):
    id: int
    email: str
    role: UserRole
