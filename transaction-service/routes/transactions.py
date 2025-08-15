from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from domain.models import (
    TransactionInDB,
    TransactionCreateRequest, TransactionUpdateRequest, TransactionRefundRequest, UserRole
)

from domain.services import RefundService
from domain.services import (
    TransactionService,
    get_database_session,
    create_transaction_service,
    get_refund_service,
    require_user_or_admin,
    require_admin
)

router = APIRouter(tags=["transactions"])

def get_transaction_service(db: Session = Depends(get_database_session)) -> TransactionService:
    """Dependency injection for TransactionService"""
    return create_transaction_service(db)

# Transaction Endpoints
@router.post(
    "/transactions/", 
    response_model=TransactionInDB,
    status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    transaction_request: TransactionCreateRequest,
    current_user: dict = Depends(require_user_or_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """Create a new transaction - USER/ADMIN access"""
    try:
        transaction = service.create_transaction(
            transaction_request=transaction_request,
            user_id=current_user.id
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create transaction"
            )
            
        return transaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction {str(e)}"
        )

@router.get(
    "/transactions/", 
    response_model=List[TransactionInDB]
)
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_user_or_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """List transactions for the current user - USER/ADMIN access"""
    try:
        if current_user.role == UserRole.ADMIN:
            # Admin can see all transactions
            transactions = service.get_all_transactions(
                skip=skip, 
                limit=limit
            )
        else:
            # Regular users can only see their own transactions
            transactions = service.get_transactions_by_user(
                user_id=current_user.id,
                skip=skip,
                limit=limit
            )
        return transactions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transactions {str(e)}"
        )

@router.get(
    "/transactions/{transaction_id}", 
    response_model=TransactionInDB
)
async def get_transaction(
    transaction_id: int,
    current_user: dict = Depends(require_user_or_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction details by ID - USER/ADMIN access"""
    try:
        transaction = service.get_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
            # Access rights are already checked by require_user_or_admin decorator
            
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transaction {str(e)}"
        )

@router.put(
    "/transactions/{transaction_id}", 
    response_model=TransactionInDB
)
async def update_transaction(
    transaction_id: int,
    update_request: TransactionUpdateRequest,
    current_user: dict = Depends(require_user_or_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """Update transaction - USER/ADMIN access"""
    try:
        # First check if transaction exists and user has access
        existing_transaction = service.get_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id
        )
        
        if not existing_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check access rights
        if current_user.role != UserRole.ADMIN and existing_transaction.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transaction"
            )
        
        # Update transaction using validated request model
        updated_transaction = service.update_transaction(
            transaction_id=transaction_id,
            update_request=update_request,
            user_id=current_user.id
        )
        
        if not updated_transaction:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update transaction"
            )
            
        return updated_transaction
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transaction {str(e)}"
        )

@router.post(
    "/transactions/{transaction_id}/cancel", 
    response_model=TransactionInDB
)
async def cancel_transaction(
    transaction_id: int,
    current_user: dict = Depends(require_user_or_admin),
    service: TransactionService = Depends(get_transaction_service)
):
    """Cancel transaction - USER/ADMIN access"""
    try:
        # First check if transaction exists and user has access
        existing_transaction = service.get_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id
        )
        
        if not existing_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check access rights
        if current_user.role != UserRole.ADMIN and existing_transaction.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transaction"
            )
        
        # Check if transaction can be cancelled
        if existing_transaction.status not in ["PENDING", "PROCESSING"]:
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
            user_id=current_user.id
        )
        
        if not cancelled_transaction:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel transaction"
            )
            
        return cancelled_transaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel transaction {str(e)}"
        )

@router.post(
    "/transactions/{transaction_id}/refund", 
    response_model=dict,
    status_code=status.HTTP_200_OK
)
async def refund_transaction(
    transaction_id: int,
    refund_request: TransactionRefundRequest,
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
    try:
        # Process the refund using the refund service
        refund = refund_service.create_refund(
            transaction_id=transaction_id,
            refund_request=refund_request,
            processed_by=current_user.id
        )
        
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process refund"
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process refund: {str(e)}"
        )

