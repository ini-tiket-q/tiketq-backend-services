from fastapi import APIRouter, Depends, HTTPException, status, Body, Header
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from domain.models import TransactionInDB
from domain.services import (
    TransactionService,
    get_database_session,
    create_transaction_service
)

router = APIRouter(tags=["transactions"])

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
    transaction_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """Create a new transaction - USER/ADMIN access"""
    try:
        transaction = service.create_transaction(
            transaction_data=transaction_data,
            user_id=current_user["id"]
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
            detail="Failed to create transaction"
        )

@router.get(
    "/transactions/", 
    response_model=List[TransactionInDB]
)
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """List transactions for the current user - USER/ADMIN access"""
    try:
        if current_user["role"] == "admin":
            # Admin can see all transactions
            transactions = service.transaction_repo.get_transactions(
                skip=skip, 
                limit=limit
            )
        else:
            # Regular users can only see their own transactions
            transactions = service.transaction_repo.get_transactions_by_user(
                user_id=current_user["id"],
                skip=skip,
                limit=limit
            )
        return transactions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions"
        )

@router.get(
    "/transactions/{transaction_id}", 
    response_model=TransactionInDB
)
async def get_transaction(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
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
        
        # Check access rights - users can only see their own transactions
        if current_user["role"] != "admin" and transaction.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transaction"
            )
            
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction"
        )

@router.put(
    "/transactions/{transaction_id}", 
    response_model=TransactionInDB
)
async def update_transaction(
    transaction_id: int,
    transaction_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """Update transaction - USER/ADMIN access"""
    try:
        # First check if transaction exists and user has access
        existing_transaction = service.get_transaction(
            transaction_id=transaction_id,
            user_id=current_user["id"]
        )
        
        if not existing_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check access rights
        if current_user["role"] != "admin" and existing_transaction.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transaction"
            )
        
        # Update transaction
        updated_transaction = service.update_transaction(
            transaction_id=transaction_id,
            transaction=transaction_data,
            user_id=current_user["id"]
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
            detail="Failed to update transaction"
        )

@router.post(
    "/transactions/{transaction_id}/cancel", 
    response_model=TransactionInDB
)
async def cancel_transaction(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """Cancel transaction - USER/ADMIN access"""
    try:
        # First check if transaction exists and user has access
        existing_transaction = service.get_transaction(
            transaction_id=transaction_id,
            user_id=current_user["id"]
        )
        
        if not existing_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check access rights
        if current_user["role"] != "admin" and existing_transaction.user_id != current_user["id"]:
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
        
        # Cancel transaction
        cancelled_transaction = service.update_transaction(
            transaction_id=transaction_id,
            transaction={"status": "CANCELLED"},
            user_id=current_user["id"]
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
            detail="Failed to cancel transaction"
        )

@router.post(
    "/transactions/{transaction_id}/refund", 
    response_model=TransactionInDB
)
async def refund_transaction(
    transaction_id: int,
    refund_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """Process transaction refund - ADMIN access only"""
    try:
        # Check admin access
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for refunds"
            )
        
        # Check if transaction exists
        existing_transaction = service.get_transaction(
            transaction_id=transaction_id,
            user_id=current_user["id"]  # Admin can access any transaction
        )
        
        if not existing_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if transaction can be refunded
        if existing_transaction.status != "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot refund transaction with status: {existing_transaction.status}"
            )
        
        # Validate refund amount
        refund_amount = refund_data.get("amount", existing_transaction.amount)
        if refund_amount > existing_transaction.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount cannot exceed transaction amount"
            )
        
        # Process refund (update transaction status)
        refunded_transaction = service.update_transaction(
            transaction_id=transaction_id,
            transaction={"status": "REFUNDED"},
            user_id=current_user["id"]
        )
        
        if not refunded_transaction:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process refund"
            )
            
        return refunded_transaction
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
            detail="Failed to process refund"
        )

