import os
import logging
from fastapi import APIRouter, HTTPException, status, Body, Path, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.models import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentMethod,
    PaymentCancellationRequest,
    PaymentRefundRequest,
    WebhookNotification
)
from domain.services import PaymentService
from adapters.midtrans_adapter import MidtransAdapter
from adapters.db import DatabaseAdapter
from adapters.webhook_handler import WebhookHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

def get_payment_service() -> PaymentService:
    """
    Dependency to get payment service instance with shared database
    """
    # Get Midtrans configuration
    midtrans_server_key = os.getenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-example")
    midtrans_client_key = os.getenv("MIDTRANS_CLIENT_KEY", "SB-Mid-client-example")
    is_production = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"

    # Initialize adapters - db_url will be read from secrets inside DatabaseAdapter
    midtrans_adapter = MidtransAdapter(
        server_key=midtrans_server_key,
        client_key=midtrans_client_key,
        is_production=is_production
    )

    # DatabaseAdapter will automatically connect to shared tiketq_db
    db_adapter = DatabaseAdapter()

    return PaymentService(
        payment_repository=midtrans_adapter,
        storage_repository=db_adapter
    )

def get_webhook_handler() -> WebhookHandler:
    """
    Dependency to get webhook handler instance
    """
    midtrans_server_key = os.getenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-example")
    return WebhookHandler(server_key=midtrans_server_key)

# Health check endpoint
@router.get("/health",
    summary="Health check",
    description="Check if payment service and database are healthy")
async def health_check(payment_service: PaymentService = Depends(get_payment_service)):
    """Health check endpoint"""
    try:
        # Check database connectivity
        db_healthy = payment_service.storage_repository.health_check()

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "service": "payment-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@router.post("/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new payment",
    description="Creates a new payment through Midtrans and stores in shared database")
async def create_payment(
    payment_request: PaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a new payment"""
    try:
        logger.info(f"Creating payment for order: {payment_request.order_id}")

        payment_response = await payment_service.create_payment(payment_request)

        logger.info(f"Payment created successfully in shared DB: {payment_response.id}")
        return payment_response

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )

@router.get("/{payment_id}",
    response_model=PaymentResponse,
    summary="Get payment details with auto status update",
    description="Retrieves payment details from database and auto-updates status from Midtrans")
async def get_payment(
    payment_id: str = Path(..., description="Payment ID"),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get payment details by ID with automatic status update"""
    try:
        logger.info(f"Getting payment with auto status update: {payment_id}")

        # This will automatically check and update status
        payment = await payment_service.get_payment(payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        logger.info(f"Payment retrieved with status: {payment.status}")
        return payment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment: {str(e)}"
        )

@router.post("/{payment_id}/cancel",
    response_model=PaymentResponse,
    summary="Cancel a payment",
    description="Cancels a pending payment through Midtrans")
async def cancel_payment(
    payment_id: str = Path(..., description="The ID of the payment to cancel"),
    request: PaymentCancellationRequest = Body(...),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Cancel a pending payment"""
    try:
        logger.info(f"Canceling payment: {payment_id}")

        payment_response = await payment_service.cancel_payment(payment_id)

        logger.info(f"Payment canceled successfully: {payment_id}")
        return payment_response

    except ValueError as e:
        logger.error(f"Cannot cancel payment: {payment_id}, {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error canceling payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel payment"
        )

@router.post("/{payment_id}/refund",
    response_model=PaymentResponse,
    summary="Refund a payment",
    description="Initiates a refund for a completed payment")
async def refund_payment(
    payment_id: str = Path(..., description="The ID of the payment to refund"),
    request: PaymentRefundRequest = Body(...),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Refund a completed payment"""
    try:
        logger.info(f"Refunding payment: {payment_id}, amount: {request.amount}")

        payment_response = await payment_service.refund_payment(payment_id, request.amount)

        logger.info(f"Payment refunded successfully: {payment_id}")
        return payment_response

    except ValueError as e:
        logger.error(f"Cannot refund payment: {payment_id}, {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error refunding payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refund payment"
        )

@router.get("/order/{order_id}",
    response_model=List[PaymentResponse],
    summary="Get payments by order",
    description="Retrieves all payments associated with a specific order")
async def get_payments_by_order(
    order_id: str = Path(..., description="The order ID to get payments for"),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get all payments for a specific order"""
    try:
        logger.info(f"Getting payments for order: {order_id}")

        payments = await payment_service.get_payments_by_order_id(order_id)

        return payments

    except Exception as e:
        logger.error(f"Error getting payments for order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments"
        )

@router.post("/webhook",
    summary="Handle Midtrans webhook",
    description="Process payment status updates from Midtrans")
async def handle_webhook(
    notification_data: Dict[str, Any] = Body(...),
    webhook_handler: WebhookHandler = Depends(get_webhook_handler),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Handle webhook notifications from Midtrans"""
    try:
        logger.info(f"Received webhook notification: {notification_data}")

        # Process webhook and update payment status
        result = await webhook_handler.process_webhook(
            notification_data=notification_data,
            payment_repository=payment_service.storage_repository,
            verify_signature=True  # Set to False for testing
        )

        logger.info(f"Webhook processed successfully: {result}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle webhook: {str(e)}"
        )

# Add manual status check endpoint
@router.get("/{payment_id}/status",
    summary="Force check payment status from Midtrans",
    description="Forces a status check from Midtrans and updates database")
async def force_check_payment_status(
    payment_id: str = Path(..., description="Payment ID"),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Force check payment status from Midtrans"""
    try:
        logger.info(f"Force checking payment status: {payment_id}")

        # Get payment first
        payment = await payment_service.get_payment(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        # Force status check
        current_status = await payment_service.get_payment_status(payment_id)

        # Get updated payment
        updated_payment = await payment_service.get_payment(payment_id)

        return {
            "payment_id": payment_id,
            "order_id": payment.order_id,
            "current_status": current_status.value,
            "last_updated": updated_payment.updated_at.isoformat(),
            "amount": payment.amount,
            "payment_method": payment.payment_method.value,
            "auto_updated": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error force checking payment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check payment status: {str(e)}"
        )

# Add manual status update endpoint for testing
@router.put("/{payment_id}/status",
    response_model=PaymentResponse,
    summary="Update payment status manually",
    description="Manually update payment status (for testing)")
async def update_payment_status(
    payment_id: str = Path(..., description="Payment ID"),
    status_update: Dict[str, str] = Body(..., example={"status": "SUCCESS"}),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Manually update payment status"""
    try:
        new_status_str = status_update.get("status")
        if not new_status_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status is required"
            )

        # Validate status
        try:
            new_status = PaymentStatus(new_status_str.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {new_status_str}"
            )

        # Update status
        await payment_service.storage_repository.update_payment_status(payment_id, new_status)

        # Get updated payment
        updated_payment = await payment_service.get_payment(payment_id)
        if not updated_payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        logger.info(f"Payment status manually updated: {payment_id} -> {new_status}")
        return updated_payment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating payment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update payment status: {str(e)}"
        )
