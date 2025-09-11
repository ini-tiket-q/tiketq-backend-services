import logging

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from domain.models import (
    PaymentInDB, PaymentConfirmRequest,
    UserRole
)
from domain.services import (
    PaymentService,
    get_database_session,
    require_user_or_admin,
    require_admin
)
from adapters.db import (
    DBTransactionRepository, DBPaymentRepository, DBOrderRepository
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])

def get_payment_service(db: Session = Depends(get_database_session)) -> PaymentService:
    """Dependency injection for PaymentService"""
    transaction_repo = DBTransactionRepository(db)
    payment_repo = DBPaymentRepository(db)
    order_repo = DBOrderRepository(db)
    return PaymentService(transaction_repo, payment_repo, order_repo)


@router.get(
    "/payments/{order_number}", 
    response_model=PaymentInDB,
    summary="Get transaction payment details by order number",
    description="""
    Retrieve details of a specific payment by its order number.
    
    ### Access Level: User/Admin
    - Requires authentication
    - Users can only view their own payments
    - Admins can view any payment
    """
)
async def get_payment_details(
    order_number: str,
    current_user = Depends(require_user_or_admin),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get payment details - USER/ADMIN access"""
    try:
        payment = payment_service.payment_repo.get_payment_by_order_number(order_number)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        logger.info("Payment found: %s", payment)
        # Check authorization - users can only see their own payments
        if current_user.role != UserRole.ADMIN:
            # Get associated transaction to check user ownership
            logger.info("Checking user authorization for payment %s", payment.transaction_id)
            transaction = payment_service.transaction_repo.get_transaction(payment.transaction_id)
            logger.info("Transaction found: %s", transaction)
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
    "/payments/{order_number}/confirm",
    response_model=PaymentInDB,
    summary="Confirm a transaction payment",
    description="""
    Confirm a transaction payment that was initiated.
    
    ### Access Level: Public (with token)
    - Used to confirm successful payments
    """
)
async def confirm_payment(
    order_number: str,
    confirm_data: PaymentConfirmRequest = Body(..., example={
        "gateway_response": {
            "transaction_id": "1234567890",
            "success": True,
            "amount": 885000,
            "currency": "IDR",
            "payment_method": "credit_card",
            "metadata": {
                "card_number": "1234-5678-9012-3456",
                "card_holder": "John Doe",
                "card_expiry": "12/25",
                "card_cvv": "123"
            }
        },
        "token": "Payment token here"
    }),
    payment_service: PaymentService = Depends(get_payment_service)
):
    try:
        payment = payment_service.confirm_payment(
            order_number=order_number,
            gateway_response=confirm_data,
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
        

@router.get(
    "/payments/admin/get-token",
    status_code=status.HTTP_200_OK,
    summary="Payment token endpoint",
    description="""
    Create payment token for admin test.
    
    ### Access Level: Admin
    - No authentication required
    - create payment token for admin test
    """
)
async def payment_token(
    payment_service: PaymentService = Depends(get_payment_service),
    current_user = Depends(require_admin),
):
    """Payment token - Admin access"""
    try:
        logger.info("Creating payment token route")
        return payment_service.create_payment_token()
        
    except ValueError as e:
        # Service layer validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment token {str(e)}"
        )
