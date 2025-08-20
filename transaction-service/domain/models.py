from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
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


# Transaction Item Model
class TransactionItem(BaseModel):
    """Model for individual transaction items"""

    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    price: float = Field(..., gt=0, description="Item price (must be greater than 0)")
    quantity: int = Field(1, gt=0, description="Item quantity (defaults to 1)")
    description: Optional[str] = Field(
        None, max_length=1000, description="Item description"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional item metadata"
    )

    @field_validator("price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


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
    # Additional transaction data
    metadata: Dict[str, Any] = {}


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
    user_id: int = Field(..., description="ID of the user who placed the order")
    order_number: str = Field(
        default_factory=lambda: f"ORD-{uuid4().hex[:8].upper()}",
        description="Unique order number"
    )
    service_type: ServiceType = Field(..., description="Type of service being ordered")
    items: List[TransactionItem] = Field(
        default_factory=list, 
        description="List of items in the order"
    )
    subtotal: float = Field(..., ge=0, description="Subtotal before tax and discount")
    tax: float = Field(default=0.0, ge=0, description="Tax amount")
    discount: float = Field(default=0.0, ge=0, description="Discount amount")
    total: float = Field(..., ge=0, description="Total amount after tax and discount")
    status: OrderStatus = Field(default=OrderStatus.DRAFT, description="Current status of the order")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional order metadata"
    )


class OrderCreate(OrderBase):
    """Request model for creating a new order with validation"""

    @model_validator(mode="after")
    def validate_totals(self):
        """Validate that the calculated totals match the provided values"""
        # Calculate expected total
        calculated_total = self.subtotal + self.tax - self.discount

        # Ensure total matches the calculated total within a small tolerance
        if abs(calculated_total - self.total) > 0.01:  # Allow for floating point precision
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

    transaction_id: int = Field(
        ..., gt=0, description="Transaction ID must be positive"
    )
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    currency: Currency = Currency.IDR
    payment_method: PaymentMethod = Field(..., description="Payment method is required")
    payment_gateway: PaymentGateway = Field(
        ..., description="Payment gateway is required"
    )
    gateway_transaction_id: Optional[str] = Field(None, max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Payment amount must be greater than 0")
        if v > 999999999:  # 999 million max
            raise ValueError("Payment amount exceeds maximum allowed value")
        return v


class PaymentConfirmRequest(BaseModel):
    """Request model for confirming payments"""

    gateway_response: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = Field(None, max_length=500)


class PaymentRefundRequest(BaseModel):
    """Request model for processing payment refunds"""

    amount: Optional[float] = Field(
        None, gt=0, description="Refund amount (defaults to full payment amount)"
    )
    reason: str = Field(
        ..., min_length=1, max_length=255, description="Reason for refund"
    )
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Refund amount must be greater than 0")
        return v


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

    service_type: ServiceType = Field(..., description="Type of service being ordered")
    items: List[Dict[str, Any]] = Field(..., min_length=1, description="Order items")
    tax: float = Field(0.0, ge=0, description="Tax amount")
    discount: float = Field(0.0, ge=0, description="Discount amount")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional order metadata"
    )

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        """Validate order items structure"""
        if not v:
            raise ValueError("Items cannot be empty")

        for item in v:
            if not isinstance(item, dict):
                raise ValueError("Each item must be a dictionary")

            # Check required fields
            required_fields = ["price", "quantity"]
            for field in required_fields:
                if field not in item:
                    raise ValueError(f"Item missing required field: {field}")

            # Validate price and quantity
            if not isinstance(item["price"], (int, float)) or item["price"] <= 0:
                raise ValueError("Item price must be a positive number")

            if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                raise ValueError("Item quantity must be a positive integer")

        return v

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

    transaction_type: TransactionType = Field(..., description="Type of transaction")
    amount: float = Field(..., gt=0, description="Transaction amount")
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
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional transaction metadata"
    )

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        """Validate transaction items structure"""
        if not v:
            raise ValueError("Items cannot be empty")
        return v

    @field_validator("amount", "subtotal", "tax", "discount", "total")
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
            # Calculate subtotal from items
            self.subtotal = sum(
                item.get("price", 0) * item.get("quantity", 1) for item in self.items
            )

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
    user_id: Optional[int] = Field(None, gt=0, description="Filter by specific user ID")
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
    processed_by: Optional[int] = Field(
        None, gt=0, description="Filter by admin who processed refund"
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
    user_id: int
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
    user_id: int
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
