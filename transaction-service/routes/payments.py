from fastapi import APIRouter, Depends, HTTPException, status, Body, Header
from typing import Dict, Any
from sqlalchemy.orm import Session

from domain.models import PaymentInDB, PaymentStatus
from domain.services import PaymentService, TransactionService
from infrastructure.dependencies import (
    get_database_session,
    create_payment_service,
    create_transaction_service
)

router = APIRouter(tags=["payments"])

def get_current_user(authorization: str = Header(None)):
    """Mock authentication - replace with real auth service integration"""
    if not authorization or not authorization.startswith("Bearer "):
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
        # Validate required fields
        if "transaction_id" not in payment_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="transaction_id is required"
            )
        
        payment = payment_service.create_payment(
            transaction_id=payment_data["transaction_id"],
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
        # Get the payment first
        payment = payment_service.payment_repo.get_payment(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Check if payment can be refunded
        if payment.status != PaymentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only completed payments can be refunded"
            )
        
        # Update payment status to refunded
        # Note: This is a simplified implementation
        # In a real system, you'd integrate with payment gateway APIs
        updated_payment = payment_service.payment_repo.update_payment(
            payment_id=payment_id,
            payment_data={
                "status": PaymentStatus.REFUNDED.value,
                "metadata": {
                    **payment.metadata,
                    "refund_reason": refund_data.get("reason", ""),
                    "refunded_by": current_user["id"],
                    "refund_amount": refund_data.get("amount", payment.amount)
                }
            }
        )
        
        return updated_payment
        
    except HTTPException:
        raise
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
        # This is a simplified implementation
        
        payment_id = webhook_data.get("payment_id")
        status_update = webhook_data.get("status")
        gateway_response = webhook_data.get("gateway_response", {})
        
        if not payment_id or not status_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="payment_id and status are required"
            )
        
        # Update payment status based on webhook
        payment = payment_service.payment_repo.update_payment(
            payment_id=payment_id,
            payment_data={
                "status": status_update,
                "gateway_response": gateway_response
            }
        )
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return {"message": "Webhook processed successfully", "payment_id": payment_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment webhook"
        )
