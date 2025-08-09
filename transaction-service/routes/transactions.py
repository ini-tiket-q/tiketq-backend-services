# from fastapi import APIRouter, Depends, HTTPException, status, Body
# from typing import List, Optional
# from uuid import UUID
# from datetime import datetime

# from sqlalchemy.orm import Session

# from ..domain.models import (
#     TransactionInDB, TransactionCreate, TransactionUpdate, TransactionStatus,
#     OrderInDB, OrderCreate, OrderStatus,
#     PaymentInDB, PaymentCreate, PaymentStatus, PaymentMethod,
#     RefundInDB, RefundCreate, RefundStatus
# )
# from ..domain.services import TransactionService, PaymentService, RefundService
# from ..adapters.repositories import SQLAlchemyUnitOfWork
# from ..adapters.db import SessionLocal, get_db

# router = APIRouter(prefix="/api/v1", tags=["transactions"])

# def get_current_user():
#     # TODO: Replace with real authentication
#     return {"id": 1, "role": "admin"}  # or "user"

# def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
#     """Dependency for TransactionService"""
#     uow = SQLAlchemyUnitOfWork()
#     return TransactionService(
#         transaction_repo=uow.transactions,
#         order_repo=uow.orders,
#         payment_repo=uow.payments,
#         refund_repo=uow.refunds
#     )

# def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
#     """Dependency for PaymentService"""
#     uow = SQLAlchemyUnitOfWork()
#     return PaymentService(
#         transaction_repo=uow.transactions,
#         payment_repo=uow.payments,
#         unit_of_work=uow
#     )

# def get_refund_service(db: Session = Depends(get_db)) -> RefundService:
#     """Dependency for RefundService"""
#     uow = SQLAlchemyUnitOfWork()
#     return RefundService(
#         transaction_repo=uow.transactions,
#         order_repo=uow.orders,
#         refund_repo=uow.refunds,
#         unit_of_work=uow
#     )

# # Transaction Endpoints
# @router.post(
#     "/transactions/", 
#     response_model=TransactionInDB,
#     status_code=status.HTTP_201_CREATED
# )
# async def create_transaction(
#     transaction_data: dict = Body(...),
#     current_user: dict = Depends(get_current_user),
#     service: TransactionService = Depends(get_transaction_service)
# ):
#     """Create a new transaction"""
#     try:
#         transaction = await service.create_transaction(
#             transaction_data=transaction_data,
#             user_id=current_user["id"]
#         )
#         return transaction
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to create transaction"
#         )

# @router.get(
#     "/transactions/", 
#     response_model=List[TransactionInDB]
# )
# async def list_transactions(
#     skip: int = 0,
#     limit: int = 100,
#     current_user: dict = Depends(get_current_user),
#     service: TransactionService = Depends(get_transaction_service)
# ):
#     """List transactions for the current user"""
#     try:
#         if current_user["role"] == "admin":
#             # Admin can see all transactions
#             transactions = await service.transaction_repo.get_transactions(
#                 skip=skip, 
#                 limit=limit
#             )
#         else:
#             # Regular users can only see their own transactions
#             transactions = await service.transaction_repo.get_transactions_by_user(
#                 user_id=current_user["id"],
#                 skip=skip,
#                 limit=limit
#             )
#         return transactions
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve transactions"
#         )

# @router.get(
#     "/transactions/{transaction_id}", 
#     response_model=TransactionInDB
# )
# async def get_transaction(
#     transaction_id: int,
#     current_user: dict = Depends(get_current_user),
#     service: TransactionService = Depends(get_transaction_service)
# ):
#     """Get a specific transaction by ID"""
#     transaction = await service.get_transaction(
#         transaction_id=transaction_id,
#         user_id=current_user["id"]
#     )
    
#     if not transaction:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Transaction not found"
#         )
    
#     # Check if user has permission to view this transaction
#     if current_user["role"] != "admin" and transaction.user_id != current_user["id"]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to view this transaction"
#         )
    
#     return transaction

# # Payment Endpoints
# @router.post(
#     "/transactions/{transaction_id}/payments",
#     response_model=PaymentInDB,
#     status_code=status.HTTP_201_CREATED
# )
# async def process_payment(
#     transaction_id: int,
#     payment_data: dict = Body(...),
#     current_user: dict = Depends(get_current_user),
#     service: PaymentService = Depends(get_payment_service)
# ):
#     """Process a payment for a transaction"""
#     try:
#         payment = await service.process_payment(
#             transaction_id=transaction_id,
#             payment_data=payment_data,
#             user_id=current_user["id"]
#         )
        
#         if not payment:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Transaction not found or not eligible for payment"
#             )
            
#         return payment
        
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to process payment"
#         )

# # Refund Endpoints
# @router.post(
#     "/transactions/{transaction_id}/refunds",
#     response_model=RefundInDB,
#     status_code=status.HTTP_201_CREATED
# )
# async def request_refund(
#     transaction_id: int,
#     refund_data: dict = Body(...),
#     current_user: dict = Depends(get_current_user),
#     service: RefundService = Depends(get_refund_service)
# ):
#     """Request a refund for a transaction"""
#     try:
#         refund = await service.request_refund(
#             transaction_id=transaction_id,
#             reason=refund_data.get("reason", ""),
#             user_id=current_user["id"]
#         )
        
#         if not refund:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Transaction not found or not eligible for refund"
#             )
            
#         return refund
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to process refund request"
#         )

# @router.post(
#     "/refunds/{refund_id}/{action}",
#     response_model=RefundInDB
# )
# async def process_refund(
#     refund_id: int,
#     action: str,
#     notes: Optional[str] = None,
#     current_user: dict = Depends(get_current_user),
#     service: RefundService = Depends(get_refund_service)
# ):
#     """Process a refund request (approve/reject)"""
#     if current_user["role"] != "admin":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only admins can process refunds"
#         )
    
#     if action.lower() not in ["approve", "reject"]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Action must be either 'approve' or 'reject'"
#         )
    
#     try:
#         refund = await service.process_refund(
#             refund_id=refund_id,
#             action=action,
#             processed_by=current_user["id"],
#             notes=notes
#         )
        
#         if not refund:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Refund not found or cannot be processed"
#             )
            
#         return refund
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to {action} refund"
#         )
