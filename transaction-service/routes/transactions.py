from fastapi import APIRouter, Depends, HTTPException, status, Body, Header
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from domain.models import TransactionInDB
from domain.services import TransactionService
from infrastructure.dependencies import (
    get_database_session,
    create_transaction_service
)

router = APIRouter(prefix="/api/v1", tags=["transactions"])

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

