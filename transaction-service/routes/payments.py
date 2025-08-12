from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from sqlalchemy.orm import Session

from domain.models import PaymentInDB, PaymentStatus
from domain.services import (
    PaymentService, 
    TransactionService,
    get_database_session,
    create_payment_service,
    create_transaction_service
)

router = APIRouter(tags=["payments"])

# Security scheme for JWT Bearer token
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Mock authentication - replace with real auth service integration"""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # For now, return a mock user - this should integrate with auth service
    # The API Gateway should handle authentication and pass user info
    return {"id": 1, "role": "user", "email": "test@example.com"}

def get_payment_service(db: Session = Depends(get_database_session)) -> PaymentService:
    """Dependency injection for PaymentService"""
    return create_payment_service(db)

def get_transaction_service(db: Session = Depends(get_database_session)) -> TransactionService:
    """Dependency injection for TransactionService"""
    return create_transaction_service(db)

# Payment Endpoints based on documentation
@router.post(
    "/payments/", 
    response_model=PaymentInDB,
    status_code=status.HTTP_201_CREATED
)
async def create_payment(
    payment_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create payment - USER/ADMIN access"""
    try:
        # Call service layer with all validation handling
        payment = payment_service.create_payment(
            transaction_id=payment_data.get("transaction_id"),
            payment_data=payment_data,
            user_id=current_user["id"]
        )
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create payment or transaction not found"
            )
            
        return payment
        
    except ValueError as e:
        # Service layer validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment"
        )

@router.get(
    "/payments/{payment_id}", 
    response_model=PaymentInDB
)
async def get_payment_details(
    payment_id: int,
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get payment details - USER/ADMIN access"""
    try:
        payment = payment_service.payment_repo.get_payment(payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Check authorization - users can only see their own payments
        if current_user["role"] != "admin":
            # Get associated transaction to check user ownership
            transaction = payment_service.transaction_repo.get_transaction(payment.transaction_id)
            if not transaction or transaction.user_id != current_user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this payment"
                )
        
        return payment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment details"
        )

@router.post(
    "/payments/{payment_id}/confirm",
    response_model=PaymentInDB
)
async def confirm_payment(
    payment_id: int,
    gateway_response: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Confirm payment - ADMIN access only"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can confirm payments"
        )
    
    try:
        payment = payment_service.confirm_payment(
            payment_id=payment_id,
            gateway_response=gateway_response,
            confirmed_by=current_user["id"]
        )
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found or cannot be confirmed"
            )
            
        return payment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm payment"
        )

@router.post(
    "/payments/{payment_id}/refund",
    response_model=PaymentInDB
)
async def process_payment_refund(
    payment_id: int,
    refund_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Process payment refund - ADMIN access only"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can process payment refunds"
        )
    
    try:
        # Call service layer with all validation handling
        updated_payment = payment_service.process_refund(
            payment_id=payment_id,
            refund_data=refund_data,
            refunded_by=current_user["id"]
        )
        
        if not updated_payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found or cannot be refunded"
            )
        
        return updated_payment
        
    except ValueError as e:
        # Service layer validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment refund"
        )

@router.post(
    "/webhooks/payment",
    status_code=status.HTTP_200_OK
)
async def payment_webhook(
    webhook_data: Dict[str, Any] = Body(...),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Payment gateway webhook - Public access"""
    try:
        # TODO: Implement webhook signature validation
        # Call service layer with all validation handling
        payment = payment_service.process_webhook(webhook_data)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return {"message": "Webhook processed successfully", "payment_id": payment.id}
        
    except ValueError as e:
        # Service layer validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment webhook"
        )
