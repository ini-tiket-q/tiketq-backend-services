from typing import Optional, List, Dict, Any, Generator
from uuid import uuid4
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
import os
from fastapi import HTTPException, status, Depends, Header
from adapters.external_api import (get_user_info, create_payment_url)
from jose import jwt, JWTError

from domain.models import (
    TransactionInDB, TransactionCreate, TransactionUpdate, TransactionStatus,
    OrderInDB, OrderCreate, OrderUpdate, OrderStatus,
    PaymentInDB, PaymentCreate, PaymentStatus, Currency,
    TransactionItem,
    # Payment request models
    PaymentCreateRequest, PaymentConfirmRequest,
    # Order request models
    OrderCreateRequest, OrderStatusUpdateRequest,
    # Transaction request models
    TransactionCreateRequest, TransactionUpdateRequest, TransactionRefundRequest,
    # Report request and response models
    TransactionReportRequest, TransactionReportResponse, TransactionReportData,
    RevenueReportRequest, RevenueReportResponse, RevenueDataPoint,
    RefundReportRequest, RefundReportResponse, RefundReportData,
    # Refund models
    RefundCreate, RefundStatus,
    # Auth models
    UserRole, UserResponse
)

from adapters.db import (
    DBTransactionRepository,
    DBOrderRepository,
    DBPaymentRepository,
    DBRefundRepository,
    DatabaseSessionProvider,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

class TransactionService:
    """Service for handling transaction-related business logic.
    
    This service manages the complete lifecycle of transactions including creation,
    status updates, and retrieval while ensuring data consistency and business rules.
    """
    
    def __init__(
        self, 
        transaction_repo: DBTransactionRepository,
        order_repo: DBOrderRepository,
        payment_repo: DBPaymentRepository,
    ):
        self.transaction_repo = transaction_repo
        self.order_repo = order_repo
        self.payment_repo = payment_repo
    
    def create_transaction(self, transaction_request: TransactionCreateRequest, email: str) -> Optional[TransactionInDB]:
        """Create a new transaction with validated request model.
        
        Args:
            transaction_request: Validated TransactionCreateRequest model
            email: Email of the user creating the transaction
            
        Returns:
            TransactionInDB if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or required data is missing
        """
        try:
            # Generate unique order number
            while True:
                order_number = f"ORD-{str(uuid4())[:8].upper()}"
                # Check if order number already exists
                if not self.order_repo.get_order_by_order_number(order_number):
                    break
            
            # Use validated amounts from request
            subtotal = transaction_request.subtotal
            tax = transaction_request.tax
            discount = transaction_request.discount
            total = transaction_request.total

            items_as_dicts = []
            item_details_for_payment = []
            
            # Convert TransactionItem objects to dictionaries
            for item in transaction_request.items:
                items_as_dicts.append(item.model_dump() if hasattr(item, 'model_dump') else dict(item))
                item_details_for_payment.append({
                    "id": order_number,
                    "price": item.price,
                    "quantity": item.quantity,
                    "name": item.name,
                })

            item_details_for_payment.append({
                "id": order_number,
                "price": tax - discount,
                "quantity": 1,
                "name": "Tax and discount",
            })

            # Create order data with email
            order_data = {
                'email': email,
                'order_number': order_number,
                'service_type': transaction_request.service_type,
                'items': items_as_dicts,
                'subtotal': subtotal,
                'tax': tax,
                'discount': discount,
                'total': total,
                'status': OrderStatus.CONFIRMED,
                'metadata': transaction_request.transaction_metadata
            }
            
            order = self.order_repo.create_order(OrderCreate(**order_data))
            if not order:
                logger.error("Failed to create order")
                return None


            # create payment gateway url from payment service
            payment_body = {
                "order_id": order_number,
                "amount": float(total),  # Ensure amount is a float
                "payment_method": transaction_request.payment_method.value.lower(),  # Ensure lowercase for payment method
                "customer_details": {
                    "email": email,
                },
                "item_details": item_details_for_payment,
                "description": "Payment for order " + order.order_number,
            }

            payment_url_body = create_payment_url(payment_body)
            if not payment_url_body:
                logger.error("Failed to create payment")
                return None

            # Create transaction using validated request data
            transaction = TransactionCreate(
                email=email,
                order_number=order.order_number,
                transaction_type=transaction_request.transaction_type,
                amount=total,
                currency=transaction_request.currency,
                status=TransactionStatus.PROCESSING,
                payment_method=transaction_request.payment_method,
                payment_gateway=transaction_request.payment_gateway,
                gateway_transaction_id= payment_url_body.get("transaction_id"),
                metadata=transaction_request.transaction_metadata
            )

            db_transaction = self.transaction_repo.create_transaction(transaction)
            if not db_transaction:
                logger.error("Failed to create transaction")
                return None
            # create payment in db
            payment = PaymentCreate(
                transaction_id=db_transaction.id,
                amount=transaction_request.total,
                currency=transaction_request.currency,
                payment_method=transaction_request.payment_method,
                payment_gateway=transaction_request.payment_gateway,
                gateway_transaction_id=payment_url_body.get("transaction_id"),
                status=PaymentStatus.PENDING,
                metadata=transaction_request.payment_metadata
            )

            db_payment = self.payment_repo.create_payment(payment)
            if not db_payment:
                logger.error("Failed to create payment")
                return None

            logger.info(
                f"Payment created successfully - ID: {db_payment.id}, "
                f"Transaction ID: {db_payment.transaction_id}, "
                f"Amount: {db_payment.amount} {db_payment.currency}, "
                f"Method: {db_payment.payment_method.value if db_payment.payment_method else 'Not set'}, "
                f"Gateway: {db_payment.payment_gateway.value if db_payment.payment_gateway else 'Not set'}"
                f"Metadata: {db_payment.metadata}!!!"
            )

            # Log successful transaction creation
            logger.info(
                f"Transaction created successfully - ID: {db_transaction.id}, "
                f"Email: {email}, Amount: {db_transaction.amount} {db_transaction.currency}, " 
                f"Service: {transaction_request.service_type.value}, "
                f"Order: {order.order_number}, "
                f"Method: {transaction_request.payment_method.value if transaction_request.payment_method else 'Not set'}, "
                f"Gateway: {transaction_request.payment_gateway.value if transaction_request.payment_gateway else 'Not set'}, "
                f"Items: {len(transaction_request.items)}"
            )

            # add payment url to transaction
            db_transaction.payment_url = payment_url_body.get("payment_url")
                
            return db_transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}", exc_info=True)
            return None
    
    def get_transaction(self, transaction_id: int, email: str, role: UserRole) -> Optional[TransactionInDB]:
        """Get a transaction by ID with authorization check.
        
        Args:
            transaction_id: ID of the transaction to retrieve
            email: Email of the user making the request
            
        Returns:
            TransactionInDB if found and authorized, None otherwise
        """
        try:
            transaction = self.transaction_repo.get_transaction(transaction_id)
            if role == UserRole.ADMIN and transaction:
                return transaction
            else:
                if not transaction or transaction.email != email:
                    logger.info(f"Unauthorized access to transaction {transaction_id} - User: {email}")
                    return None
                return transaction
        except Exception as e:
            logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            return None

    def get_transactions_by_user(
        self, 
        email: str, 
        status: Optional[TransactionStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionInDB]:
        """Get paginated list of transactions for a user.
        
        Args:
            email: Email of the user
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of TransactionInDB objects
        """
        try:
            return self.transaction_repo.get_transactions_by_user(
                email=email,
                status=status,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving transactions for user {email}: {str(e)}")
            return []
    
    def get_all_transactions(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionInDB]:
        """Get all transactions (admin function).
        
        Args:
            skip: Number of transactions to skip for pagination
            limit: Maximum number of transactions to return
            
        Returns:
            List of TransactionInDB objects
        """
        try:
            return self.transaction_repo.get_transactions(
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving all transactions: {str(e)}")
            return []
    
    def search_transactions_by_email(
        self,
        search_email: str,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        admin_email: str = None
    ) -> List[TransactionInDB]:
        """Search transactions by email with validation (admin function).
        
        Args:
            search_email: Email address to search for transactions
            status_filter: Optional status string to filter by
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            admin_email: Email of the admin performing the search (for logging)
            
        Returns:
            List of TransactionInDB objects
            
        Raises:
            ValueError: If validation fails (invalid status, email format, etc.)
        """
        try:
            # Validate email format
            if not search_email or not search_email.strip():
                raise ValueError("Search email cannot be empty")
            
            # Basic email format validation
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, search_email.strip()):
                raise ValueError(f"Invalid email format: {search_email}")
            
            # Validate and convert status filter
            status_enum = None
            if status_filter:
                try:
                    status_enum = TransactionStatus(status_filter.upper())
                except ValueError:
                    valid_statuses = [s.value for s in TransactionStatus]
                    raise ValueError(f"Invalid status value: {status_filter}. Valid values are: {valid_statuses}")
            
            # Validate pagination parameters
            if skip < 0:
                raise ValueError("Skip parameter cannot be negative")
            if limit <= 0 or limit > 1000:  # Set reasonable upper limit
                raise ValueError("Limit must be between 1 and 1000")
            
            # Get transactions using existing service method with validation
            transactions = self.get_transactions_by_user(
                email=search_email.strip().lower(),
                status=status_enum,
                skip=skip,
                limit=limit
            )
            
            # Log successful search for audit purposes
            logger.info(
                f"Admin search completed - Admin: {admin_email}, "
                f"Search email: {search_email}, Status: {status_filter}, "
                f"Results: {len(transactions)}, Skip: {skip}, Limit: {limit}"
            )
            
            return transactions
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(
                f"Error in admin transaction search - Admin: {admin_email}, "
                f"Search email: {search_email}, Error: {str(e)}"
            )
            raise ValueError(f"Failed to search transactions: {str(e)}")
    
    def update_transaction(
        self, 
        transaction_id: int, 
        update_request: TransactionUpdateRequest,
    ) -> Optional[TransactionInDB]:
        """Update transaction with validated request model.
        
        Args:
            transaction_id: ID of the transaction to update
            update_request: Validated TransactionUpdateRequest model
            email: Email of the user making the request
            
        Returns:
            Updated TransactionInDB if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or unauthorized access
        """
        try:
            transaction_check = self.transaction_repo.get_transaction(transaction_id)
            if not transaction_check:
                raise ValueError("Transaction not found or access denied")

            # Create update data from validated request
            update_data = {}
            
            if update_request.status is not None:
                update_data["status"] = update_request.status
            if update_request.payment_method is not None:
                update_data["payment_method"] = update_request.payment_method
            if update_request.payment_gateway is not None:
                update_data["payment_gateway"] = update_request.payment_gateway
            if update_request.gateway_transaction_id is not None:
                update_data["gateway_transaction_id"] = update_request.gateway_transaction_id
            if update_request.metadata is not None:
                update_data["metadata"] = update_request.metadata

            transaction_update = TransactionUpdate(**update_data)
            
            # Store original transaction for audit logging
            original_transaction = transaction_check
                
            updated_transaction = self.transaction_repo.update_transaction(
                transaction_id, 
                transaction_update
            )
            
            # Log successful transaction update
            if updated_transaction:
                logger.info(
                    f"Transaction updated successfully - ID: {transaction_id}, "
                    f"Status changed: {original_transaction.status.value if original_transaction.status else 'None'} -> "
                    f"{updated_transaction.status.value if updated_transaction.status else 'None'}, "
                    f"Order: {original_transaction.order_number}, "
                    f"Amount: {original_transaction.amount}, "
                    f"Changes: {update_data}"
                )
            
            return updated_transaction
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
            return None
    
    def cancel_transaction(self, transaction_id: int) -> Optional[TransactionInDB]:
        """Cancel a transaction with logging"""
        try:
            from domain.models import TransactionStatus
            
            # Create an update request to set status to cancelled
            cancel_request = TransactionUpdateRequest(status=TransactionStatus.CANCELLED)
            
            result = self.update_transaction(transaction_id, cancel_request)
            
            if result:
                logger.info(f"Transaction cancelled: transaction_id={transaction_id}")
                
            return result
        except Exception as e:
            logger.error(f"Failed to cancel transaction {transaction_id}: {str(e)}")
            raise
    
    # Delete transaction with authorization check (should be admin)
    # def delete_transaction(self, transaction_id: int, email: str) -> bool:
    #     """Delete a transaction with authorization check"""
    #     transaction = self.transaction_repo.get_transaction(transaction_id)
    #     if not transaction or transaction.email != email:
    #         return False
            
    #     return self.transaction_repo.delete_transaction(transaction_id)

class OrderService:
    """Service for handling order-related business logic.
    
    This service manages order creation, retrieval, and updates while enforcing
    business rules and data consistency.
    """
    
    def __init__(
        self, 
        order_repo: DBOrderRepository,
    ):
        self.order_repo = order_repo
    
    def get_order(self, order_id: int) -> Optional[OrderInDB]:
        """Get an order by ID with optional authorization check.
        
        Args:
            order_id: ID of the order to retrieve
            email: Optional user email for authorization
            
        Returns:
            OrderInDB if found (and authorized if email provided), None otherwise
        """
        try:
            order = self.order_repo.get_order(order_id)
            if not order:
                return None

            return order
            
        except Exception as e:
            logger.error(f"Error retrieving order {order_id}: {str(e)}")
            return None

    def get_order_by_number(self, order_number: str) -> Optional[OrderInDB]:
        """Get an order by order number with optional authorization check.
        
        Args:
            order_number: order number to retrieve
            
        Returns:
            OrderInDB if found (and authorized if email provided), None otherwise
        """
        try:
            order = self.order_repo.get_order_by_order_number(order_number)
            if not order:
                return None
             
            return order
            
        except Exception as e:
            logger.error(f"Error retrieving order {order_number}: {str(e)}")
            return None
    
    def get_orders_by_user(
        self, 
        email: str, 
        status: Optional[OrderStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[OrderInDB]:
        """Get paginated list of orders for a user.
        
        Args:
            email: Email of the user
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of OrderInDB objects
        """
        try:
            return self.order_repo.get_orders_by_user(
                email=email,
                status=status,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving orders for user {email}: {str(e)}")
            return []
    
    def create_order(self, order_request: "OrderCreateRequest", email: str) -> Optional[OrderInDB]:
        """Create a new order with Pydantic validation.
        
        Args:
            order_request: Validated OrderCreateRequest model
            email: Email of the user creating the order
            
        Returns:
            OrderInDB if created successfully, None otherwise
            
        Raises:
            ValueError: If validation fails or required data is missing
        """
        try:
            # Calculate totals from validated items
            items = order_request.items
            subtotal = sum(item.price * item.quantity for item in items)
            total = subtotal + order_request.tax - order_request.discount
            
            # Convert dictionary items to TransactionItem objects
            transaction_items = []
            for item in items:
                print(f"DEBUG: Processing item: {item}, type: {type(item)}")
                transaction_item = TransactionItem(
                    name=item.name,
                    price=item.price,
                    quantity=item.quantity,
                    description=item.description,
                    metadata=item.metadata
                )
                transaction_items.append(transaction_item)
            
            # Prepare order data
            order_create_data = {
                "email": email,
                "service_type": order_request.service_type,
                "items": transaction_items,
                "subtotal": subtotal,
                "tax": order_request.tax,
                "discount": order_request.discount,
                "total": total,
                "status": OrderStatus.DRAFT,
                "metadata": order_request.metadata
            }
            
            order_create = OrderCreate(**order_create_data)
            
            return self.order_repo.create_order(order_create)
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Error creating order for user {email}: {str(e)}")
            logger.error(f"Full traceback: {tb}")
            print(f"TRACEBACK: {tb}")
            return None
    
    def get_orders(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[OrderStatus] = None
    ) -> List[OrderInDB]:
        """Get all orders (admin function).
        
        Args:
            skip: Number of orders to skip for pagination
            limit: Maximum number of orders to return
            status: Optional status filter
            
        Returns:
            List of OrderInDB objects
        """
        try:
            return self.order_repo.get_orders(
                status=status,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving all orders: {str(e)}")
            return []
    
    def update_order_status(
        self, 
        order_id: int, 
        status_request: "OrderStatusUpdateRequest",
    ) -> Optional[OrderInDB]:
        """Update order status with Pydantic validation.
        
        Args:
            order_id: ID of the order to update
            status_request: Validated OrderStatusUpdateRequest model
            email: Email of the user making the request
            
        Returns:
            Updated OrderInDB if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or unauthorized access
        """
        try:
            # Create update data from validated request
            update_data = {
                "status": status_request.status
            }
            
            # Add metadata if provided
            if status_request.metadata is not None:
                update_data["metadata"] = status_request.metadata
            
            update_order = OrderUpdate(**update_data)
            
            # If order is completed, set completed_at
            if update_order.status == OrderStatus.COMPLETED and 'completed_at' not in update_order:
                update_order.completed_at = datetime.now(timezone.utc)
                
            return self.order_repo.update_order(
                order_id, 
                update_order
            )
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
            return None

    # def delete_order(self, order_id: int, email: str) -> bool:
                

class PaymentService:
    """Service for handling payment-related business logic.
    
    This service manages payment processing, status updates, and validation
    while integrating with payment gateways.
    """
    
    def __init__(
        self, 
        transaction_repo: DBTransactionRepository,
        payment_repo: DBPaymentRepository,
        order_repo: DBOrderRepository,
    ):
        self.transaction_repo = transaction_repo
        self.payment_repo = payment_repo
        self.order_repo = order_repo
    
    def create_payment(
        self, 
        transaction_id: int,
        payment_data: PaymentCreateRequest,
        email: str
    ) -> Optional[PaymentInDB]:
        """Create a new payment record for a transaction.
        
        Args:
            transaction_id: ID of the transaction to create payment for
            payment_data: Dictionary containing payment details
            email: Email of the user making the payment
            
        Returns:
            PaymentInDB if successful, None otherwise
            
        Raises:
            ValueError: If payment data validation fails
        """
        try:
            # Get and validate transaction
            transaction = self.transaction_repo.get_transaction(transaction_id)
            if not transaction or transaction.email != email:
                logger.error(f"Transaction {transaction_id} not found or unauthorized")
                raise ValueError("Transaction not found or unauthorized")
            
            # Validate payment amount matches transaction amount
            if payment_data.amount != transaction.amount:
                logger.error(
                    f"Payment amount {payment_data.amount} does not match "
                    f"transaction amount {transaction.amount} for transaction {transaction_id}"
                )
                raise ValueError("Payment amount does not match transaction amount")
                
            # Check if transaction is already completed
            if transaction.status == TransactionStatus.COMPLETED:
                logger.warning(f"Transaction {transaction_id} is already completed")
                payments = self.payment_repo.get_payments_by_transaction(transaction_id)
                raise ValueError(f"Transaction is already completed, {payments[0]}")
            
            # Create payment record using validated data
            payment = PaymentCreate(
                transaction_id=payment_data.transaction_id,
                amount=payment_data.amount,
                currency=Currency(payment_data.currency)
                if payment_data.currency
                else transaction.currency,
                payment_method=payment_data.payment_method,
                payment_gateway=payment_data.payment_gateway,
                gateway_transaction_id=payment_data.gateway_transaction_id,
                status=PaymentStatus.PENDING,
                metadata=payment_data.metadata or {},
            )
            
            # Save payment to database
            db_payment = self.payment_repo.create_payment(payment)
            if not db_payment:
                logger.error(f"Failed to create payment for transaction {transaction_id}")
                return None
                
            # Log successful payment creation
            logger.info(
                f"Payment created successfully - ID: {db_payment.id}, "
                f"Transaction: {transaction_id}, Email: {email}, "
                f"Amount: {db_payment.amount} {db_payment.currency}, "
                f"Method: {db_payment.payment_method.value}, "
                f"Gateway: {db_payment.payment_gateway.value}"
            )
                
            # Update transaction status
            self.transaction_repo.update_transaction(
                transaction_id,
                TransactionUpdate(
                    status=TransactionStatus.PROCESSING,
                    payment_method=payment.payment_method,
                    payment_gateway=payment.payment_gateway,
                    gateway_transaction_id=payment.gateway_transaction_id
                )
            )
            logger.info(
                f"Transaction {transaction_id} status updated to PROCESSING "
            )

            # Get the order using order_number from transaction
            order = self.order_repo.get_order_by_order_number(transaction.order_number)

            if order:
                # Update order status to CONFIRMED
                self.order_repo.update_order_status(
                    order.id,
                    OrderStatus.CONFIRMED
                )
                logger.info(
                    f"Order {order.order_number} status updated to CONFIRMED "
                    f"after payment creation for transaction {transaction_id}"
                )

            else:
                logger.error(
                    f"Order {transaction.order_number} not found for transaction {transaction_id}"
                )

            return db_payment
            
        except Exception as e:
            logger.error(f"Error creating payment for transaction {transaction_id}: {str(e)}", exc_info=True)
            return None
    
    def confirm_payment(
        self, 
        order_number: str, 
        gateway_response: PaymentConfirmRequest,
    ) -> Optional[PaymentInDB]:
        """Confirm a payment with gateway response data.
        
        Args:
            payment_id: ID of the payment to confirm
            gateway_response: Response data from payment gateway
            confirmed_by: Optional user ID who confirmed the payment
            
        Returns:
            Updated PaymentInDB if successful, None otherwise
            
        Raises:
            ValueError: If payment confirmation data validation fails
        """
    
        try:
            # Validate payment token
            if not self.validate_payment_token(gateway_response.token):
                logger.error("Invalid payment token")
                raise ValueError("Invalid payment token")

            # Get payment with order number
            payment = self.payment_repo.get_payment_by_order_number(order_number)
            if not payment:
                logger.error(f"Payment {order_number} not found")
                return None

            payment_id = payment.id
            
            # Get payment with transaction
            logger.info(f"Payment {payment_id} found")
            payment = self.payment_repo.get_payment(payment_id)
            transaction = self.transaction_repo.get_transaction(payment.transaction_id)
            order = self.order_repo.get_order_by_order_number(transaction.order_number)

            if not payment or not transaction or not order:
                logger.error(f"Payment {payment_id} not found or transaction not found or order not found")
                return None
            
            # Update payment status
            logger.info(
                f"Payment {gateway_response.gateway_response.get('success', False)}"
            )
            status = PaymentStatus.SUCCESS if gateway_response.gateway_response.get('success', False) else PaymentStatus.FAILED
            
            # Update payment record
            updated_payment = self.payment_repo.update_payment_status(
                payment_id=payment_id,
                status=status,
                gateway_transaction_id=gateway_response.gateway_response.get('transaction_id')
            )
            
            if not updated_payment:
                logger.error(f"Failed to update payment {payment_id}")
                return None
                
            # Update transaction status based on payment status
            transaction_status = (
                TransactionStatus.COMPLETED 
                if status == PaymentStatus.SUCCESS 
                else TransactionStatus.FAILED
            )
            
            self.transaction_repo.update_transaction(
                transaction_id=payment.transaction_id,
                transaction=TransactionUpdate(
                    status=transaction_status,
                    gateway_transaction_id=gateway_response.gateway_response.get('transaction_id'),
                    metadata={
                        **payment.metadata,
                        'gateway_response': gateway_response.gateway_response,
                        'confirmed_at': datetime.now(timezone.utc)
                    }
                )
            )
            
            self.order_repo.update_order_status(
                order_id=order.id,
                status=OrderStatus.PAID,
            )
            
            return updated_payment
            
        except Exception as e:
            logger.error(f"Error confirming payment with order number {order_number}: {str(e)}", exc_info=True)
            return None

    def validate_payment_token(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            status: str = payload.get("token")
            if status == "success":
                return True
            return False
        except JWTError:
            return False

    def create_payment_token(self):
        try:
            logger.info("Creating payment token")
            payload = {
                "token": "success"
            }
            return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        except Exception as e:
            logger.error(f"Error creating payment token: {str(e)}", exc_info=True)
            return None


# =============================================================================
# Dependency Injection and Service Factories
# =============================================================================


def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides database sessions.
    This is the only place where FastAPI directly interacts with the database.
    """
    
    _session_provider = DatabaseSessionProvider()
    session = _session_provider.get_session()
    try:
        yield session
    finally:
        _session_provider.close_session(session)

# Application layer - service composition
def create_payment_service(db_session: Session) -> PaymentService:
    """
    Factory function to create PaymentService with all its dependencies.
    This is where we compose the hexagonal architecture.
    """
    
    # Infrastructure adapters (ports implementations)
    transaction_repo = DBTransactionRepository(db_session)
    payment_repo = DBPaymentRepository(db_session)
    
    # Domain service
    return PaymentService(
        transaction_repo=transaction_repo,
        payment_repo=payment_repo
    )

def create_transaction_service(db_session: Session) -> TransactionService:
    """
    Factory function to create TransactionService with all its dependencies.
    """
    
    # Infrastructure adapters
    transaction_repo = DBTransactionRepository(db_session)
    order_repo = DBOrderRepository(db_session)
    
    # Domain service
    return TransactionService(
        transaction_repo=transaction_repo,
        order_repo=order_repo
    )

def create_order_service(db_session: Session) -> OrderService:
    """
    Factory function to create OrderService with all its dependencies.
    """
    
    # Infrastructure adapters
    order_repo = DBOrderRepository(db_session)
    
    # Domain service
    return OrderService(
        order_repo=order_repo
    )


class RefundService:
    """Service for handling refund-related business logic.
    
    This service manages the refund process including validation, status updates,
    and integration with payment gateways.
    """
    
    def __init__(
        self,
        transaction_repo: DBTransactionRepository,
        refund_repo: DBRefundRepository,
        payment_repo: DBPaymentRepository
    ):
        self.transaction_repo = transaction_repo
        self.refund_repo = refund_repo
        self.payment_repo = payment_repo
    
    def create_refund(
        self,
        transaction_id: int,
        refund_request: "TransactionRefundRequest",
        processed_by: str
    ) -> Dict[str, Any]:
        """Create a new refund for a transaction.
        
        Args:
            transaction_id: ID of the transaction to refund
            refund_request: Validated refund request data
            processed_by: Email of the admin processing the refund
            
        Returns:
            Dict containing refund details if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or refund cannot be processed
        """
        try:
            # Get the transaction
            transaction = self.transaction_repo.get_transaction(transaction_id)
            if not transaction:
                raise ValueError("Transaction not found")
                
            # Validate transaction status
            if transaction.status != TransactionStatus.COMPLETED:
                raise ValueError("Only completed transactions can be refunded")
                
            # Get the payment for this transaction
            payments = self.payment_repo.get_payments_by_transaction(transaction_id)
            if not payments:
                raise ValueError("No payment found for this transaction")
                
            payment = payments[0]  # Get the first payment (assuming one payment per transaction)
            
            # Calculate refund amount (default to full amount if not specified)
            refund_amount = refund_request.amount if refund_request.amount else transaction.amount
            
            if refund_amount <= 0:
                raise ValueError("Refund amount must be greater than 0")
                
            if refund_amount > transaction.amount:
                raise ValueError("Refund amount cannot exceed transaction amount")
                
            # Create refund record
            refund_data = {
                "transaction_id": transaction_id,
                "amount": refund_amount,
                "reason": refund_request.reason,
                "status": RefundStatus.PROCESSING,
                "processed_by": processed_by,
                "processed_at": datetime.now(timezone.utc),
                "notes": refund_request.notes
            }
            
            refund = self.refund_repo.create_refund(RefundCreate(**refund_data))
            if not refund:
                raise ValueError("Failed to create refund record")
                
            # Update transaction status
            self.transaction_repo.update_transaction(
                transaction_id,
                TransactionUpdate(status=TransactionStatus.REFUNDED)
            )
            
            # Here you would typically integrate with payment gateway to process the refund
            # For example: payment_gateway.process_refund(payment.gateway_transaction_id, refund_amount)
            
            # Update refund status to completed
            refund = self.refund_repo.update_refund_status(
                refund_id=refund.id,
                status=RefundStatus.COMPLETED,
                processed_by=processed_by,
                notes="Refund processed successfully"
            )
            
            # Log successful refund processing
            logger.info(
                f"Refund processed successfully - ID: {refund.id}, "
                f"Transaction: {transaction_id}, "
                f"Amount: {refund_amount}, "
                f"Processed by: {processed_by}, "
                f"Reason: {refund_request.reason}"
            )
            
            return {
                "refund_id": refund.id,
                "transaction_id": refund.transaction_id,
                "amount": refund.amount,
                "status": refund.status,
                "reason": refund.reason,
                "processed_at": refund.processed_at
            }
            
        except Exception as e:
            # Update refund status to failed if it was created
            if 'refund' in locals():
                self.refund_repo.update_refund_status(
                    refund_id=refund.id,
                    status=RefundStatus.FAILED,
                    processed_by=processed_by,
                    notes=f"Refund failed: {str(e)}"
                )
            raise ValueError(f"Failed to process refund: {str(e)}")
    
    def get_refund(self, refund_id: int) -> Optional[Dict[str, Any]]:
        """Get refund details by ID.
        
        Args:
            refund_id: ID of the refund to retrieve
            
        Returns:
            Dict containing refund details if found, None otherwise
        """
        refund = self.refund_repo.get_refund(refund_id)
        if not refund:
            return None
            
        return {
            "id": refund.id,
            "transaction_id": refund.transaction_id,
            "amount": refund.amount,
            "status": refund.status,
            "reason": refund.reason,
            "processed_by": refund.processed_by,
            "processed_at": refund.processed_at,
            "notes": refund.notes,
            "created_at": refund.created_at
        }
    
    def get_refunds_by_transaction(self, transaction_id: int) -> List[Dict[str, Any]]:
        """Get all refunds for a transaction.
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            List of refund details
        """
        refunds = self.refund_repo.get_refunds_by_transaction(transaction_id)
        return [
            {
                "id": refund.id,
                "amount": refund.amount,
                "status": refund.status,
                "reason": refund.reason,
                "processed_at": refund.processed_at,
                "created_at": refund.created_at
            }
            for refund in refunds
        ]

# =============================================================================
# REPORTS SERVICE
# =============================================================================
class ReportsService:
    """Service for handling reports and analytics operations"""
    
    def __init__(self, transaction_repo, refund_repo=None):
        self.transaction_repo = transaction_repo
        self.refund_repo = refund_repo
    
    def generate_transaction_report(self, report_request: "TransactionReportRequest") -> "TransactionReportResponse":
        """Generate transaction report with filters"""
        try:
            # Get transactions based on filters
            transactions = self.transaction_repo.get_transactions_for_report(
                start_date=report_request.date_range.start_date,
                end_date=report_request.date_range.end_date,
                status_filter=report_request.status_filter,
                transaction_type_filter=report_request.transaction_type,
                min_amount=report_request.min_amount,
                max_amount=report_request.max_amount,
                email=report_request.email,
                currency=report_request.currency
            )
            
            # Calculate summary statistics
            total_count = len(transactions)
            total_amount = sum(t.amount for t in transactions)
            status_breakdown = {}
            type_breakdown = {}
            
            for transaction in transactions:
                # Status breakdown
                status = transaction.status.value if hasattr(transaction.status, 'value') else str(transaction.status)
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                # Type breakdown
                trans_type = transaction.transaction_type.value if hasattr(transaction.transaction_type, 'value') else str(transaction.transaction_type)
                type_breakdown[trans_type] = type_breakdown.get(trans_type, 0) + 1
            
            summary = {
                "total_transactions": total_count,
                "total_amount": total_amount,
                "average_amount": total_amount / total_count if total_count > 0 else 0,
                "status_breakdown": status_breakdown,
                "type_breakdown": type_breakdown,
                "currency": report_request.currency
            }
            
            # Convert to response format
            transaction_data = [
                TransactionReportData(
                    transaction_id=t.id,
                    email=t.email,
                    order_id=t.order_id,
                    transaction_type=t.transaction_type,
                    amount=t.amount,
                    currency=t.currency,
                    status=t.status,
                    payment_method=t.payment_method,
                    payment_gateway=t.payment_gateway,
                    created_at=t.created_at,
                    updated_at=t.updated_at
                ) for t in transactions
            ]
            
            return TransactionReportResponse(
                summary=summary,
                transactions=transaction_data,
                total_count=total_count,
                total_amount=total_amount,
                date_range=report_request.date_range
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate transaction report: {str(e)}")
    
    def generate_revenue_report(self, report_request: "RevenueReportRequest") -> "RevenueReportResponse":
        """Generate revenue analytics report"""
        try:
            # Get revenue data grouped by period
            revenue_data = self.transaction_repo.get_revenue_data(
                start_date=report_request.date_range.start_date,
                end_date=report_request.date_range.end_date,
                group_by=report_request.group_by,
                currency=report_request.currency,
                service_type_filter=report_request.service_type_filter,
                include_refunds=report_request.include_refunds
            )
            
            # Calculate summary
            total_revenue = sum(point['revenue'] for point in revenue_data)
            total_transactions = sum(point['transaction_count'] for point in revenue_data)
            total_refunds = sum(point['refund_amount'] for point in revenue_data)
            
            summary = {
                "total_revenue": total_revenue,
                "total_transactions": total_transactions,
                "total_refunds": total_refunds,
                "net_revenue": total_revenue - total_refunds,
                "average_transaction_value": total_revenue / total_transactions if total_transactions > 0 else 0,
                "refund_rate": (total_refunds / total_revenue * 100) if total_revenue > 0 else 0,
                "currency": report_request.currency,
                "group_by": report_request.group_by
            }
            
            # Convert to response format
            data_points = [
                RevenueDataPoint(
                    period=point['period'],
                    revenue=point['revenue'],
                    transaction_count=point['transaction_count'],
                    refund_amount=point['refund_amount']
                ) for point in revenue_data
            ]
            
            return RevenueReportResponse(
                summary=summary,
                revenue_data=data_points,
                total_revenue=total_revenue,
                total_transactions=total_transactions,
                total_refunds=total_refunds,
                date_range=report_request.date_range
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate revenue report: {str(e)}")
    
    def generate_refund_report(self, report_request: "RefundReportRequest") -> "RefundReportResponse":
        """Generate refund report with filters"""
        try:
            # Get refunds based on filters
            refunds = self.refund_repo.get_refunds_for_report(
                start_date=report_request.date_range.start_date,
                end_date=report_request.date_range.end_date,
                status_filter=report_request.status_filter,
                min_amount=report_request.min_amount,
                max_amount=report_request.max_amount,
                reason_filter=report_request.reason_filter,
                processed_by=report_request.processed_by
            )
            
            # Calculate summary statistics
            total_count = len(refunds)
            total_amount = sum(r.amount for r in refunds)
            status_breakdown = {}
            reason_breakdown = {}
            
            for refund in refunds:
                # Status breakdown
                status = refund.status.value if hasattr(refund.status, 'value') else str(refund.status)
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                # Reason breakdown (extract main keyword)
                reason_key = refund.reason.split()[0].lower() if refund.reason else "unknown"
                reason_breakdown[reason_key] = reason_breakdown.get(reason_key, 0) + 1
            
            summary = {
                "total_refunds": total_count,
                "total_amount": total_amount,
                "average_amount": total_amount / total_count if total_count > 0 else 0,
                "status_breakdown": status_breakdown,
                "reason_breakdown": reason_breakdown
            }
            
            # Convert to response format
            refund_data = [
                RefundReportData(
                    refund_id=r.id,
                    transaction_id=r.transaction_id,
                    email=r.email if hasattr(r, 'email') else None,  # Get from transaction if needed
                    amount=r.amount,
                    reason=r.reason,
                    status=r.status,
                    processed_by=r.processed_by,
                    processed_at=r.processed_at,
                    created_at=r.created_at
                ) for r in refunds
            ]
            
            return RefundReportResponse(
                summary=summary,
                refunds=refund_data,
                total_count=total_count,
                total_amount=total_amount,
                date_range=report_request.date_range
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate refund report: {str(e)}")


# Service factory for reports
def get_refund_service(db: Session = Depends(get_database_session)) -> RefundService:
    """Factory function to create RefundService with all its dependencies"""
    transaction_repo = DBTransactionRepository(db)
    refund_repo = DBRefundRepository(db)
    payment_repo = DBPaymentRepository(db)
    return RefundService(transaction_repo, refund_repo, payment_repo)


def get_reports_service(db: Session = Depends(get_database_session)) -> ReportsService:
    """Factory function to create ReportsService with proper dependencies"""
    transaction_repo = DBTransactionRepository(db)
    refund_repo = DBRefundRepository(db)
    return ReportsService(transaction_repo, refund_repo)


# AUTH SERVICE
SECRET_KEY = os.getenv("JWT_SECRET", "secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def get_current_user(authorization: Optional[str] = Header(None)) -> UserResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_info = get_user_info(authorization)
    return UserResponse(**user_info)


def require_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


def require_user_or_admin(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    if current_user.role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User or admin access required",
        )
    return current_user
