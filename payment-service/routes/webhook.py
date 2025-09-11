import logging
from fastapi import APIRouter, HTTPException, status, Body, Depends, Request
from typing import Dict, Any
from datetime import datetime

from domain.services import PaymentService, get_database_session
from adapters.webhook_handler import WebhookHandler
from sqlalchemy.orm import Session
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

def get_payment_service(db: Session = Depends(get_database_session)) -> PaymentService:
    """Dependency to get payment service instance"""
    from adapters.midtrans_adapter import MidtransAdapter
    from adapters.db import DatabaseAdapter

    midtrans_server_key = os.getenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-example")
    midtrans_client_key = os.getenv("MIDTRANS_CLIENT_KEY", "SB-Mid-client-example")
    is_production = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"

    midtrans_adapter = MidtransAdapter(
        server_key=midtrans_server_key,
        client_key=midtrans_client_key,
        is_production=is_production
    )

    db_adapter = DatabaseAdapter(db)

    return PaymentService(
        payment_repository=midtrans_adapter,
        storage_repository=db_adapter
    )

def get_webhook_handler() -> WebhookHandler:
    """Dependency to get webhook handler instance"""
    midtrans_server_key = os.getenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-example")
    return WebhookHandler(server_key=midtrans_server_key)

@router.post("/midtrans",
    summary="Handle Midtrans webhook notification",
    description="Process payment status updates from Midtrans webhook")
async def handle_midtrans_webhook(
    request: Request,
    notification_data: Dict[str, Any] = Body(...),
    webhook_handler: WebhookHandler = Depends(get_webhook_handler),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Handle webhook notifications from Midtrans"""
    try:
        # Log the incoming webhook
        logger.info(f"Received Midtrans webhook notification")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Notification data: {notification_data}")

        # Process webhook and update payment status
        result = await webhook_handler.process_webhook(
            notification_data=notification_data,
            payment_repository=payment_service.storage_repository,
            verify_signature=False  # Set to False for development/testing with ngrok
        )

        logger.info(f"Webhook processed successfully: {result}")

        # Return success response that Midtrans expects
        return {
            "status": "success",
            "message": "Notification processed successfully",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        logger.error(f"Notification data: {notification_data}")

        # Still return 200 to prevent Midtrans from retrying
        return {
            "status": "error",
            "message": f"Failed to process notification: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/test",
    summary="Test webhook endpoint",
    description="Simple test endpoint to verify webhook is accessible")
async def test_webhook():
    """Test endpoint to verify webhook is working"""
    return {
        "status": "success",
        "message": "Webhook endpoint is working",
        "timestamp": datetime.now().isoformat(),
        "service": "payment-service",
        "port": 8003
    }

@router.post("/test-notification",
    summary="Test webhook with sample notification",
    description="Test webhook processing with sample Midtrans notification")
async def test_webhook_notification(
    webhook_handler: WebhookHandler = Depends(get_webhook_handler),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Test webhook with sample notification data"""
    try:
        # Sample Midtrans notification data
        sample_notification = {
            "transaction_time": "2025-01-15 10:30:00",
            "transaction_status": "settlement",
            "transaction_id": "test-transaction-001",
            "status_message": "midtrans payment notification",
            "status_code": "200",
            "signature_key": "sample-signature",
            "payment_type": "credit_card",
            "order_id": "ORDER-TEST-001",
            "merchant_id": "G123456789",
            "gross_amount": "100000.00",
            "fraud_status": "accept",
            "currency": "IDR"
        }

        logger.info("Testing webhook with sample notification")

        result = await webhook_handler.process_webhook(
            notification_data=sample_notification,
            payment_repository=payment_service.storage_repository,
            verify_signature=False
        )

        return {
            "status": "success",
            "message": "Test notification processed",
            "sample_data": sample_notification,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error testing webhook: {e}")
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
