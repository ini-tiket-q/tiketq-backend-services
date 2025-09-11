from math import log
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from typing import List, Optional
from sqlalchemy.orm import Session
import time

from domain.models import (
    TransactionInDB,
    TransactionCreateRequest, TransactionUpdateRequest, TransactionRefundRequest, UserRole
)

from domain.services import (
    TransactionService, RefundService,
    get_database_session,
    require_user_or_admin,
    require_admin
)
from adapters.db import (
    DBTransactionRepository, DBRefundRepository, DBPaymentRepository, DBOrderRepository
)

from adapters.audit_logger import (
    audit_logger, AuditEventType, extract_request_context
)

router = APIRouter(tags=["transactions"])

def get_transaction_service(db: Session = Depends(get_database_session)) -> TransactionService:
    """Dependency injection for TransactionService"""
    transaction_repo = DBTransactionRepository(db)
    order_repo = DBOrderRepository(db)
    payment_repo = DBPaymentRepository(db)
    return TransactionService(transaction_repo, order_repo, payment_repo)

def get_refund_service(db: Session = Depends(get_database_session)) -> RefundService:
    """Dependency injection for RefundService"""
    transaction_repo = DBTransactionRepository(db)
    refund_repo = DBRefundRepository(db)
    payment_repo = DBPaymentRepository(db)
    return RefundService(transaction_repo, refund_repo, payment_repo)

@router.post(
    "/transactions/", 
    response_model=TransactionInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
    description="""
    Create a new transaction.
    
    ### Access Level: Public
    - No authentication required

    This endpoint creates a new transaction, order, and payment in the database and returns the created transaction along with payment url.
    """
)
async def create_transaction(
    request: Request,
    service: TransactionService = Depends(get_transaction_service),
    transaction_request: TransactionCreateRequest = Body(
        ...,
        example={
            "email": "john.doe@example.com",
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
        },
    ),
):
    """Create a new transaction - USER/ADMIN access"""
    start_time = time.time()
    request_context = extract_request_context(request)
    
    try:
        # Log transaction creation attempt
        audit_logger.log_transaction_event(
            event_type=AuditEventType.TRANSACTION_CREATED,
            transaction_id=0,  # Will be updated after creation
            email=transaction_request.email,
            amount=transaction_request.total,
            currency=transaction_request.currency,
            details={
                "transaction_type": transaction_request.transaction_type.value,
                "service_type": transaction_request.service_type.value,
                "payment_method": transaction_request.payment_method.value if transaction_request.payment_method else None,
                "payment_gateway": transaction_request.payment_gateway.value if transaction_request.payment_gateway else None,
                "item_count": len(transaction_request.items),
                "subtotal": transaction_request.subtotal,
                "tax": transaction_request.tax,
                "discount": transaction_request.discount
            },
            request_context=request_context
        )
        
        transaction = service.create_transaction(
            transaction_request=transaction_request,
            email=transaction_request.email
        )
        
        if not transaction:
            # Log failure
            audit_logger.log_transaction_event(
                event_type=AuditEventType.TRANSACTION_FAILED,
                transaction_id=0,
                email=transaction_request.email,
                amount=transaction_request.total,
                currency=transaction_request.currency,
                details={"error": "Failed to create transaction in service layer"},
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create transaction"
            )
        
        # Log successful creation with full details
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log_transaction_event(
            event_type=AuditEventType.TRANSACTION_CREATED,
            transaction_id=transaction.id,
            email=transaction_request.email,
            amount=transaction.amount,
            currency=transaction.currency,
            order_number=transaction.order_number,
            status=transaction.status.value,
            details={
                "transaction_type": transaction.transaction_type.value,
                "service_type": transaction_request.service_type.value,
                "payment_method": transaction.payment_method.value if transaction.payment_method else None,
                "payment_gateway": transaction.payment_gateway.value if transaction.payment_gateway else None,
                "item_count": len(transaction_request.items),
                "subtotal": transaction_request.subtotal,
                "tax": transaction_request.tax,
                "discount": transaction_request.discount,
                "operation_duration_ms": duration_ms,
                "created_at": transaction.created_at.isoformat()
            },
            request_context=request_context
        )
            
        return transaction
        
    except ValueError as e:
        # Log validation error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "create_transaction",
                "validation_error": True,
                "email": transaction_request.email,
                "total": transaction_request.total
            },
            email=transaction_request.email,
            endpoint="/transactions/"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log system error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "create_transaction",
                "email": transaction_request.email,
                "total": transaction_request.total,
                "operation_duration_ms": (time.time() - start_time) * 1000
            },
            email=transaction_request.email,
            endpoint="/transactions/"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction {str(e)}"
        )

@router.get(
    "/transactions/", 
    response_model=List[TransactionInDB],
    summary="List all transactions",
    description="""
    Retrieve a list of transactions.
    
    ### Access Level: User/Admin
    - Requires authentication
    - Users can only see their own transactions
    - Admins can see all transactions
    """
)
async def list_transactions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    email: Optional[str] = None,
    current_user: dict = Depends(require_user_or_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """List transactions for the current user - USER/ADMIN access"""
    start_time = time.time()
    request_context = extract_request_context(request)
    
    try:
        # Log transaction list request
        audit_logger.log_api_request(
            method="GET",
            endpoint="/transactions/",
            email=current_user.email,
            user_role=current_user.role.value,
            ip_address=request_context.get("ip_address"),
            user_agent=request_context.get("user_agent")
        )
        
        # Handle email search (admin only)
        if email:
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can search transactions by email"
                )
            
            # Use the service layer search method
            transactions = service.search_transactions_by_email(
                search_email=email,
                status_filter=None,
                skip=skip,
                limit=limit,
                admin_email=current_user.email
            )
            
            # Log admin search
            audit_logger.log_security_event(
                event_type=AuditEventType.API_REQUEST,
                email=current_user.email,
                user_role=current_user.role.value,
                message=f"Admin searched transactions for email: {email}",
                details={
                    "operation": "search_transactions_by_email",
                    "search_email": email,
                    "result_count": len(transactions),
                    "skip": skip,
                    "limit": limit,
                    "admin_search": True
                },
                request_context=request_context
            )
            
            return transactions
        
        # Regular listing behavior
        if current_user.role == UserRole.ADMIN:
            # Admin can see all transactions
            transactions = service.get_all_transactions(
                skip=skip, 
                limit=limit
            )
            
            # Log admin access to all transactions
            audit_logger.log_security_event(
                event_type=AuditEventType.API_REQUEST,
                email=current_user.email,
                user_role=current_user.role.value,
                message=f"Admin accessed all transactions (count: {len(transactions)})",
                details={
                    "access_type": "admin_all_transactions",
                    "skip": skip,
                    "limit": limit,
                    "result_count": len(transactions)
                },
                request_context=request_context
            )
        else:
            # Regular users can only see their own transactions
            transactions = service.get_transactions_by_user(
                email=current_user.email,
                skip=skip,
                limit=limit
            )
            
            # Log user access to own transactions
            audit_logger.log_api_request(
                method="GET",
                endpoint="/transactions/",
                email=current_user.email,
                user_role=current_user.role.value,
                duration_ms=(time.time() - start_time) * 1000,
                status_code=200,
                ip_address=request_context.get("ip_address"),
                user_agent=request_context.get("user_agent")
            )
            
        return transactions
        
    except Exception as e:
        # Log error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "list_transactions",
                "email": current_user.email,
                "skip": skip,
                "limit": limit,
                "operation_duration_ms": (time.time() - start_time) * 1000
            },
            email=current_user.email,
            endpoint="/transactions/"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transactions {str(e)}"
        )

@router.get(
    "/transactions/{transaction_id}", 
    response_model=TransactionInDB,
    summary="Get transaction details by ID",
    description="""
    Retrieve details of a specific transaction by its ID.
    
    ### Access Level: User/Admin
    - Requires authentication
    - Users can only access their own transactions
    - Admins can access any transaction
    """
)
async def get_transaction(
    transaction_id: int,
    request: Request,
    current_user: dict = Depends(require_user_or_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction details by ID - USER/ADMIN access"""
    start_time = time.time()
    request_context = extract_request_context(request)
    
    try:
        # Log transaction access attempt
        audit_logger.log_api_request(
            method="GET",
            endpoint=f"/transactions/{transaction_id}",
            email=current_user.email,
            user_role=current_user.role.value,
            ip_address=request_context.get("ip_address"),
            user_agent=request_context.get("user_agent")
        )
        
        transaction = service.get_transaction(
            transaction_id=transaction_id,
            email=current_user.email,
            role=current_user.role
        )
        
        if not transaction:
            # Log unauthorized access attempt
            audit_logger.log_security_event(
                event_type=AuditEventType.UNAUTHORIZED_ACCESS,
                email=current_user.email,
                user_role=current_user.role.value,
                message=f"Unauthorized access to transaction {transaction_id}",
                details={
                    "transaction_id": transaction_id,
                    "access_denied": True
                },
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Log successful transaction access
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log_transaction_event(
            event_type=AuditEventType.API_REQUEST,
            transaction_id=transaction.id,
            email=current_user.email,
            user_role=current_user.role.value,
            amount=transaction.amount,
            currency=transaction.currency,
            order_number=transaction.order_number,
            status=transaction.status.value,
            details={
                "operation": "get_transaction",
                "access_granted": True,
                "operation_duration_ms": duration_ms
            },
            request_context=request_context
        )
            
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        # Log system error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "get_transaction",
                "transaction_id": transaction_id,
                "email": current_user.email,
                "operation_duration_ms": (time.time() - start_time) * 1000
            },
            email=current_user.email,
            transaction_id=transaction_id,
            endpoint=f"/transactions/{transaction_id}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transaction {str(e)}"
        )

@router.put(
    "/transactions/{transaction_id}", 
    response_model=TransactionInDB,
    summary="Update transaction details",
    description="""
    Update an existing transaction's details.
    
    ### Access Level: Admin Only
    - Requires admin privileges
    - Used for administrative updates to transactions
    """
)
async def update_transaction(
    transaction_id: int,
    update_request: TransactionUpdateRequest,
    request: Request,
    current_user: dict = Depends(require_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """Update transaction - USER/ADMIN access"""
    start_time = time.time()
    request_context = extract_request_context(request)
    
    try:
        # Log transaction update attempt
        audit_logger.log_transaction_event(
            event_type=AuditEventType.TRANSACTION_UPDATED,
            transaction_id=transaction_id,
            email=current_user.email,
            user_role=current_user.role.value,
            details={
                "operation": "update_transaction",
                "update_fields": {
                    field: getattr(update_request, field) 
                    for field in ['status', 'payment_method', 'payment_gateway', 'gateway_transaction_id'] 
                    if getattr(update_request, field) is not None
                }
            },
            request_context=request_context
        )
        
        # First check if transaction exists and user has access
        existing_transaction = service.get_transaction(
            transaction_id=transaction_id,
            email=current_user.email,
            role=current_user.role
        )

        if not existing_transaction:
            # Log unauthorized access
            audit_logger.log_security_event(
                event_type=AuditEventType.UNAUTHORIZED_ACCESS,
                email=current_user.email,
                user_role=current_user.role.value,
                message=f"Unauthorized update attempt on transaction {transaction_id}",
                details={
                    "transaction_id": transaction_id,
                    "operation": "update",
                    "access_denied": True
                },
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Update transaction using validated request model
        updated_transaction = service.update_transaction(
            transaction_id=transaction_id,
            update_request=update_request,
        )
        
        if not updated_transaction:
            # Log update failure
            audit_logger.log_transaction_event(
                event_type=AuditEventType.TRANSACTION_FAILED,
                transaction_id=transaction_id,
                email=current_user.email,
                user_role=current_user.role.value,
                details={
                    "operation": "update_transaction",
                    "error": "Service layer update failed"
                },
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found or access denied"
            )
        
        # Log successful update
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log_transaction_event(
            event_type=AuditEventType.TRANSACTION_UPDATED,
            transaction_id=updated_transaction.id,
            email=current_user.email,
            user_role=current_user.role.value,
            amount=updated_transaction.amount,
            currency=updated_transaction.currency,
            order_number=updated_transaction.order_number,
            status=updated_transaction.status.value,
            details={
                "operation": "update_transaction",
                "previous_status": existing_transaction.status.value,
                "new_status": updated_transaction.status.value,
                "operation_duration_ms": duration_ms,
                "updated_fields": {
                    field: getattr(update_request, field) 
                    for field in ['status', 'payment_method', 'payment_gateway', 'gateway_transaction_id'] 
                    if getattr(update_request, field) is not None
                }
            },
            request_context=request_context
        )
            
        return updated_transaction
        
    except HTTPException:
        raise
    except ValueError as e:
        # Log validation error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "update_transaction",
                "validation_error": True,
                "transaction_id": transaction_id,
                "email": current_user.email,
            },
            email=current_user.email,
            transaction_id=transaction_id,
            endpoint=f"/transactions/{transaction_id}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log system error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "update_transaction",
                "transaction_id": transaction_id,
                "email": current_user.email,
                "operation_duration_ms": (time.time() - start_time) * 1000
            },
            email=current_user.email,
            transaction_id=transaction_id,
            endpoint=f"/transactions/{transaction_id}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transaction {str(e)}"
        )

@router.post(
    "/transactions/{transaction_id}/cancel", 
    response_model=TransactionInDB,
    summary="Cancel a transaction",
    description="""
    Cancel an existing transaction.
    
    ### Access Level: User/Admin
    - Requires authentication
    - Users can only cancel their own transactions
    - Admins can cancel any transaction
    - Only PENDING or PROCESSING transactions can be cancelled
    """
)
async def cancel_transaction(
    transaction_id: int,
    request: Request,
    current_user: dict = Depends(require_user_or_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """Cancel transaction - USER/ADMIN access"""
    start_time = time.time()
    request_context = extract_request_context(request)
    
    try:
        # Log cancellation attempt
        audit_logger.log_transaction_event(
            event_type=AuditEventType.TRANSACTION_CANCELLED,
            transaction_id=transaction_id,
            email=current_user.email,
            user_role=current_user.role.value,
            details={
                "operation": "cancel_transaction",
                "initiated_by": "user" if current_user.role == UserRole.USER else "admin"
            },
            request_context=request_context
        )
        
        # First check if transaction exists and user has access
        existing_transaction = service.get_transaction(
            transaction_id=transaction_id,
            email=current_user.email,
            role=current_user.role
        )
        
        if not existing_transaction:
            # Log unauthorized cancellation attempt
            audit_logger.log_security_event(
                event_type=AuditEventType.UNAUTHORIZED_ACCESS,
                email=current_user.email,
                user_role=current_user.role.value,
                message=f"Unauthorized cancellation attempt on transaction {transaction_id}",
                details={
                    "transaction_id": transaction_id,
                    "operation": "cancel",
                    "access_denied": True
                },
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check access rights
        if current_user.role != UserRole.ADMIN and existing_transaction.email != current_user.email:
            # Log permission denied
            audit_logger.log_security_event(
                event_type=AuditEventType.PERMISSION_DENIED,
                email=current_user.email,
                user_role=current_user.role.value,
                message=f"Permission denied for transaction {transaction_id} cancellation",
                details={
                    "transaction_id": transaction_id,
                    "transaction_owner": existing_transaction.email,
                    "requesting_user": current_user.email
                },
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transaction"
            )
        
        # Check if transaction can be cancelled
        if existing_transaction.status not in ["PENDING", "PROCESSING"]:
            # Log invalid cancellation attempt
            audit_logger.log_transaction_event(
                event_type=AuditEventType.TRANSACTION_FAILED,
                transaction_id=transaction_id,
                email=current_user.email,
                user_role=current_user.role.value,
                amount=existing_transaction.amount,
                currency=existing_transaction.currency,
                status=existing_transaction.status.value,
                details={
                    "operation": "cancel_transaction",
                    "error": f"Cannot cancel transaction with status: {existing_transaction.status.value}",
                    "invalid_status": True
                },
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel transaction with status: {existing_transaction.status}"
            )
        
        # Cancel transaction using validated request model
        from domain.models import TransactionStatus
        cancel_request = TransactionUpdateRequest(status=TransactionStatus.CANCELLED)
        cancelled_transaction = service.update_transaction(
            transaction_id=transaction_id,
            update_request=cancel_request,
        )
        
        if not cancelled_transaction:
            # Log cancellation failure
            audit_logger.log_transaction_event(
                event_type=AuditEventType.TRANSACTION_FAILED,
                transaction_id=transaction_id,
                email=current_user.email,
                user_role=current_user.role.value,
                details={
                    "operation": "cancel_transaction",
                    "error": "Service layer cancellation failed"
                },
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found or cannot be cancelled"
            )
        
        # Log successful cancellation
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log_transaction_event(
            event_type=AuditEventType.TRANSACTION_CANCELLED,
            transaction_id=cancelled_transaction.id,
            email=current_user.email,
            user_role=current_user.role.value,
            amount=cancelled_transaction.amount,
            currency=cancelled_transaction.currency,
            order_number=cancelled_transaction.order_number,
            status=cancelled_transaction.status.value,
            details={
                "operation": "cancel_transaction",
                "previous_status": existing_transaction.status.value,
                "new_status": cancelled_transaction.status.value,
                "cancellation_reason": "user_requested" if current_user.role == UserRole.USER else "admin_cancelled",
                "operation_duration_ms": duration_ms
            },
            request_context=request_context
        )
            
        return cancelled_transaction
        
    except HTTPException:
        raise
    except Exception as e:
        # Log system error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "cancel_transaction",
                "transaction_id": transaction_id,
                "email": current_user.email,
                "operation_duration_ms": (time.time() - start_time) * 1000
            },
            email=current_user.email,
            transaction_id=transaction_id,
            endpoint=f"/transactions/{transaction_id}/cancel"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel transaction {str(e)}"
        )

@router.post(
    "/transactions/{transaction_id}/refund", 
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Process a refund for a transaction",
    description="""
    Process a refund for a completed transaction.
    
    ### Access Level: Admin Only
    - Requires admin privileges
    - Used for processing refunds for completed transactions
    
    ### Parameters:
    - **transaction_id**: ID of the transaction to refund
    - **amount**: Optional amount to refund (defaults to full amount)
    - **reason**: Reason for the refund (required)
    - **notes**: Additional notes about the refund (optional)
    """
)
async def refund_transaction(
    transaction_id: int,
    refund_request: TransactionRefundRequest,
    request: Request,
    current_user: dict = Depends(require_admin),  # Only admin can process refunds
    refund_service: RefundService = Depends(get_refund_service)
):
    """
    Process a refund for a completed transaction - ADMIN access only
    
    - **transaction_id**: ID of the transaction to refund
    - **amount**: Optional amount to refund (defaults to full amount)
    - **reason**: Reason for the refund (required)
    - **notes**: Additional notes about the refund (optional)
    """
    start_time = time.time()
    request_context = extract_request_context(request)
    
    try:
        # Log refund processing attempt
        audit_logger.log_transaction_event(
            event_type=AuditEventType.TRANSACTION_REFUNDED,
            transaction_id=transaction_id,
            email=current_user.email,
            user_role=current_user.role.value,
            amount=refund_request.amount,
            details={
                "operation": "process_refund",
                "refund_reason": refund_request.reason,
                "refund_notes": refund_request.notes,
                "processed_by": current_user.id,
                "admin_initiated": True
            },
            request_context=request_context
        )
        
        # Process the refund using the refund service
        refund = refund_service.create_refund(
            transaction_id=transaction_id,
            refund_request=refund_request,
            processed_by=current_user.id
        )
        
        if not refund:
            # Log refund processing failure
            audit_logger.log_transaction_event(
                event_type=AuditEventType.TRANSACTION_FAILED,
                transaction_id=transaction_id,
                email=current_user.email,
                user_role=current_user.role.value,
                details={
                    "operation": "process_refund",
                    "error": "Refund service failed to create refund"
                },
                request_context=request_context
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process refund"
            )
        
        # Log successful refund processing
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log_transaction_event(
            event_type=AuditEventType.TRANSACTION_REFUNDED,
            transaction_id=transaction_id,
            email=current_user.email,
            user_role=current_user.role.value,
            amount=refund["amount"],
            details={
                "operation": "process_refund",
                "refund_id": refund["refund_id"],
                "refund_amount": refund["amount"],
                "refund_status": refund["status"],
                "processed_by": current_user.id,
                "refund_reason": refund_request.reason,
                "refund_notes": refund_request.notes,
                "operation_duration_ms": duration_ms,
                "processed_at": refund["processed_at"]
            },
            request_context=request_context
        )
        
        # Also log business event for compliance
        audit_logger.log_security_event(
            event_type=AuditEventType.BUSINESS_EVENT if hasattr(AuditEventType, 'BUSINESS_EVENT') else AuditEventType.API_REQUEST,
            email=current_user.email,
            user_role=current_user.role.value,
            message=f"Refund processed: {refund['amount']:.2f} IDR for transaction {transaction_id}",
            details={
                "event_type": "refund_processed",
                "transaction_id": transaction_id,
                "refund_id": refund["refund_id"],
                "amount": refund["amount"],
                "compliance_required": refund["amount"] >= 5000000,  # High-value refund
                "admin_approval": True
            },
            request_context=request_context
        )
            
        return {
            "message": "Refund processed successfully",
            "refund_id": refund["refund_id"],
            "transaction_id": refund["transaction_id"],
            "amount": refund["amount"],
            "status": refund["status"],
            "processed_at": refund["processed_at"]
        }
        
    except ValueError as e:
        # Log validation error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "process_refund",
                "validation_error": True,
                "transaction_id": transaction_id,
                "email": current_user.email,
                "refund_amount": refund_request.amount
            },
            email=current_user.email,
            transaction_id=transaction_id,
            endpoint=f"/transactions/{transaction_id}/refund"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log system error
        audit_logger.log_error(
            error=e,
            context={
                "operation": "process_refund",
                "transaction_id": transaction_id,
                "email": current_user.email,
                "refund_amount": refund_request.amount,
                "operation_duration_ms": (time.time() - start_time) * 1000
            },
            email=current_user.email,
            transaction_id=transaction_id,
            endpoint=f"/transactions/{transaction_id}/refund"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process refund: {str(e)}"
        )

