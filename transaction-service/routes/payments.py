from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from domain.models import (
    PaymentCreateRequest, PaymentInDB, PaymentConfirmRequest,
    PaymentRefundRequest, PaymentWebhookRequest
)
from domain.services import (
    PaymentService, 
    TransactionService,
    get_database_session,
    create_payment_service,
    create_transaction_service,
    require_user_or_admin,
    require_admin
)

router = APIRouter(tags=["payments"])

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
    payment_data: PaymentCreateRequest = Body(...),
    current_user = Depends(require_user_or_admin),
    payment_service: PaymentService = Depends(get_payment_service),
    db: Session = Depends(get_database_session)
):
    """Create payment - USER/ADMIN access"""
    try:
        # Convert Pydantic model to dict and pass to service layer
        payment_dict = payment_data.model_dump()
        payment = payment_service.create_payment(
            transaction_id=payment_dict.pop("transaction_id"),
            payment_data=payment_dict,
            user_id=current_user.id
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
    response_model=PaymentInDB
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
            detail=f"Failed to retrieve payment details {str(e)}"
        )

@router.post(
    "/payments/{payment_id}/confirm",
    response_model=PaymentInDB
)
async def confirm_payment(
    payment_id: int,
    confirm_data: PaymentConfirmRequest = Body(...),
    current_user = Depends(require_admin),
    payment_service: PaymentService = Depends(get_payment_service)
):
    try:
        # Convert Pydantic model to dict for the service layer
        confirm_dict = confirm_data.model_dump()
        payment = payment_service.confirm_payment(
            payment_id=payment_id,
            gateway_response=confirm_dict.get("gateway_response", {}),
            confirmed_by=current_user.id
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
            detail=f"Failed to confirm payment {str(e)}"
        )

@router.post(
    "/payments/{payment_id}/refund",
    response_model=PaymentInDB
)
async def process_payment_refund(
    payment_id: int,
    refund_data: PaymentRefundRequest = Body(...),
    current_user = Depends(require_admin),
    payment_service: PaymentService = Depends(get_payment_service)
):
    try:
        # Convert Pydantic model to dict for the service layer
        refund_dict = refund_data.model_dump()
        updated_payment = payment_service.process_refund(
            payment_id=payment_id,
            refund_data=refund_dict,
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
            detail=f"Failed to process payment refund {str(e)}"
        )

@router.post(
    "/webhooks/payment",
    status_code=status.HTTP_200_OK
)
async def payment_webhook(
    webhook_request: PaymentWebhookRequest = Body(...),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Payment gateway webhook - Public access"""
    try:
        # TODO: Implement webhook signature validation
        # Convert Pydantic model to dict for the service layer
        webhook_dict = webhook_request.model_dump()
        payment = payment_service.process_webhook(webhook_dict)
        
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
            detail=f"Failed to process payment webhook {str(e)}"
        )
