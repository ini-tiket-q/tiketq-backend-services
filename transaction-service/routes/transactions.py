from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

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

router = APIRouter(tags=["transactions"])

def get_transaction_service(db: Session = Depends(get_database_session)) -> TransactionService:
    """Dependency injection for TransactionService"""
    transaction_repo = DBTransactionRepository(db)
    order_repo = DBOrderRepository(db)
    return TransactionService(transaction_repo, order_repo)

def get_refund_service(db: Session = Depends(get_database_session)) -> RefundService:
    """Dependency injection for RefundService"""
    transaction_repo = DBTransactionRepository(db)
    refund_repo = DBRefundRepository(db)
    payment_repo = DBPaymentRepository(db)
    return RefundService(transaction_repo, refund_repo, payment_repo)

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
            user_id=current_user["id"]
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
        # Use the existing get_transactions_by_user method
        transactions = service.get_transactions_by_user(
            user_id=current_user["id"],
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
            user_id=current_user["id"]
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
            
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
        # Use the existing update_transaction method
        updated_transaction = service.update_transaction(
            transaction_id=transaction_id,
            update_request=update_request,
            user_id=current_user["id"]
        )
        
        if not updated_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found or access denied"
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
        # Cancel the transaction and let the service handle logging
        cancelled_transaction = service.cancel_transaction(
            transaction_id=transaction_id,
            user_id=current_user["id"]
        )
        
        if not cancelled_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found or cannot be cancelled"
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
        # Process the refund using the refund service with integrated logging
        refund = refund_service.create_refund(
            transaction_id=transaction_id,
            refund_request=refund_request,
            processed_by=current_user["id"]
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

