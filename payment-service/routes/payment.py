from fastapi import APIRouter, Depends, HTTPException, Request, Body
from typing import List, Optional
from ..domain.models import PaymentRequest, PaymentResponse, PaymentStatus
from ..domain.services import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


async def get_payment_service() -> PaymentService:
    """
    Dependency to get payment service instance.
    In a real application, this would be configured with proper dependency injection.
    """
    from ..adapters.midtrans_adapter import MidtransAdapter
    from ..adapters.db import DatabaseAdapter
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    server_key = os.getenv("MIDTRANS_SERVER_KEY", "")
    client_key = os.getenv("MIDTRANS_CLIENT_KEY", "")
    is_production = os.getenv("MIDTRANS_PRODUCTION", "false").lower() == "true"
    
    db_host = os.getenv("DB_HOST", "postgres")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "tiketq_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    payment_repository = MidtransAdapter(
        server_key=server_key,
        client_key=client_key,
        is_production=is_production
    )
    
    storage_repository = DatabaseAdapter(db_url=db_url)
    
    return PaymentService(
        payment_repository=payment_repository,
        storage_repository=storage_repository
    )


@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment_request: PaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Create a new payment transaction
    """
    try:
        return await payment_service.create_payment(payment_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


@router.get("/{payment_id}/status", response_model=PaymentStatus)
async def get_payment_status(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get the current status of a payment
    """
    try:
        return await payment_service.get_payment_status(payment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get payment details
    """
    try:
        payment = await payment_service.storage_repository.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail=f"Payment with ID {payment_id} not found")
        return payment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment: {str(e)}")


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Cancel a pending payment
    """
    try:
        return await payment_service.cancel_payment(payment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel payment: {str(e)}")


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: str,
    amount: Optional[float] = None,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Refund a completed payment
    """
    try:
        return await payment_service.refund_payment(payment_id, amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refund payment: {str(e)}")


@router.get("/order/{order_id}", response_model=List[PaymentResponse])
async def get_payments_by_order(
    order_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get all payments for an order
    """
    try:
        return await payment_service.get_payments_by_order_id(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payments: {str(e)}")


@router.post("/webhook", status_code=200)
async def handle_webhook(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Handle payment notifications from Midtrans
    """
    try:
        notification_data = await request.json()
        
        notification = await payment_service.handle_notification(notification_data)
        
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process notification: {str(e)}")
