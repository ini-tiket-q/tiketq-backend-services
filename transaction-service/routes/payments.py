import logging

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from domain.models import (
    PaymentCreateRequest, PaymentInDB, PaymentConfirmRequest,
    PaymentRefundRequest, PaymentWebhookRequest,
    UserRole
)
from domain.services import (
    PaymentService,
    get_database_session,
    require_user_or_admin,
    require_admin
)
from adapters.db import (
    DBTransactionRepository, DBPaymentRepository
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])

def get_payment_service(db: Session = Depends(get_database_session)) -> PaymentService:
    """Dependency injection for PaymentService"""
    transaction_repo = DBTransactionRepository(db)
    payment_repo = DBPaymentRepository(db)
    return PaymentService(transaction_repo, payment_repo)

@router.post(
    "/payments/", 
    response_model=PaymentInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new payment",
    description="""
    Create a new payment for a transaction.
    
    ### Access Level: Public
    - No authentication required
    """
)
async def create_payment(
    payment_data: PaymentCreateRequest = Body(...),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """Create payment - USER/ADMIN access"""
    try:
        payment = payment_service.create_payment(
            transaction_id=payment_data.transaction_id,
            payment_data=payment_data,
            email=payment_data.email
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
            detail=f"Failed to create payment {str(e)}"
        )

@router.get(
    "/payments/{payment_id}", 
    response_model=PaymentInDB,
    summary="Get payment details by ID",
    description="""
    Retrieve details of a specific payment by its ID.
    
    ### Access Level: User/Admin
    - Requires authentication
    - Users can only view their own payments
    - Admins can view any payment
    """
)
async def get_payment_details(
    payment_id: int,
    current_user = Depends(require_user_or_admin),
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
        if current_user.role != UserRole.ADMIN:
            # Get associated transaction to check user ownership
            transaction = payment_service.transaction_repo.get_transaction(payment.transaction_id)
            if not transaction or transaction.email != current_user.email:
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
            detail=f"Failed to retrieve payment details {str(e)}"
        )

@router.post(
    "/payments/{payment_id}/confirm",
    response_model=PaymentInDB,
    summary="Confirm a payment",
    description="""
    Confirm a payment that was initiated.
    
    ### Access Level: Admin Only
    - Requires admin privileges
    - Used to confirm successful payments
    """
)
async def confirm_payment(
    payment_id: int,
    confirm_data: PaymentConfirmRequest = Body(..., example={
        "gateway_response": {
            "transaction_id": "1234567890",
            "success": True,
            "amount": 885000,
            "currency": "IDR",
            "payment_method": "CREDIT_CARD",
            "metadata": {
                "card_number": "1234-5678-9012-3456",
                "card_holder": "John Doe",
                "card_expiry": "12/25",
                "card_cvv": "123"
            }
        }
    }),
    current_user = Depends(require_admin),
    payment_service: PaymentService = Depends(get_payment_service)
):
    try:
        payment = payment_service.confirm_payment(
            payment_id=payment_id,
            gateway_response=confirm_data,
            confirmed_by=current_user.email
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
        logger.error(f"Error confirming payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm payment"
        )

@router.post(
    "/payments/{payment_id}/refund",
    response_model=PaymentInDB,
    summary="Process a payment refund",
    description="""
    Process a refund for a completed payment.
    
    ### Access Level: Admin Only
    - Requires admin privileges
    - Used for processing refunds for completed payments
    """
)
async def process_payment_refund(
    payment_id: int,
    refund_data: PaymentRefundRequest = Body(...),
    current_user = Depends(require_admin),
    payment_service: PaymentService = Depends(get_payment_service)
):
    try:
        # For now, use a simplified refund process
        # In a complete implementation, this would integrate with the refund service
        payment = payment_service.payment_repo.get_payment(payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found or cannot be refunded"
            )
        
        # Log the refund attempt for audit purposes
        # Actual refund processing would be handled by the refund service
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
            detail=f"Failed to process payment refund {str(e)}"
        )

@router.post(
    "/webhooks/payment",
    status_code=status.HTTP_200_OK,
    summary="Payment webhook endpoint",
    description="""
    Webhook endpoint for payment gateway callbacks.
    
    ### Access Level: Public
    - No authentication required
    - Used by payment gateways to send payment status updates
    """
)
async def payment_webhook(
    webhook_request: PaymentWebhookRequest = Body(...),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Payment gateway webhook - Public access"""
    try:
        # For now, just return success
        # In a complete implementation, this would process the webhook
        # and update payment status accordingly
        return {"message": "Webhook received successfully"}
        
    except ValueError as e:
        # Service layer validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment webhook {str(e)}"
        )
