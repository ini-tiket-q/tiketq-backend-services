import logging
from fastapi import APIRouter, HTTPException, status, Body, Depends, Request
from typing import Dict, Any
from datetime import datetime
# GANTI IMPORT JWT INI:
# import jwt
# DENGAN:
# import PyJWT as jwt
# ATAU:
from jose import jwt
import requests
import os

from domain.services import PaymentService, get_database_session
from adapters.webhook_handler import WebhookHandler
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-payment-key")
ALGORITHM = "HS256"

# Create router instance
router = APIRouter()

def create_payment_token(order_id: str, transaction_status: str):
    """Create JWT token for payment confirmation"""
    try:
        logger.info(f"Creating payment token for order: {order_id}")
        logger.info(f"SECRET_KEY available: {'Yes' if SECRET_KEY else 'No'}")
        logger.info(f"SECRET_KEY length: {len(SECRET_KEY) if SECRET_KEY else 0}")
        logger.info(f"ALGORITHM: {ALGORITHM}")

        payload = {
            "order_id": order_id,
            "status": transaction_status,
            "token_type": "payment_confirmation",
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Token payload: {payload}")

        # Test which JWT library is available
        try:
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            logger.info(f"Token created successfully for order: {order_id}")
            logger.info(f"Token preview: {token[:50]}...")
            return token
        except AttributeError as attr_error:
            logger.error(f"JWT encode AttributeError: {attr_error}")
            # Try alternative approach
            import PyJWT
            token = PyJWT.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            logger.info(f"Token created with PyJWT for order: {order_id}")
            return token

    except Exception as e:
        logger.error(f"Error creating payment token: {str(e)}", exc_info=True)
        logger.error(f"SECRET_KEY: {SECRET_KEY}")
        logger.error(f"Exception type: {type(e).__name__}")
        return None

async def confirm_payment(order_id: str, payment_token: str):
    """Send POST request to transaction-service payments/{order_id}/confirm endpoint"""
    try:
        # Try multiple URLs for different environments
        TRANSACTION_SERVICE_URL = os.getenv("TRANSACTION_SERVICE_URL", "http://localhost:8004")

        # Fallback URLs for different environments
        urls_to_try = [
            TRANSACTION_SERVICE_URL,                # From environment
            "http://transaction-service:8004",      # Docker service name
            "http://localhost:8004",                # Local development
            "http://127.0.0.1:8004",               # Alternative localhost
            "http://host.docker.internal:8004"     # Docker Desktop
        ]

        for attempt, base_url in enumerate(urls_to_try, 1):
            confirm_url = f"{base_url}/payments/{order_id}/confirm"

            logger.info(f"🚀 Attempt {attempt}: Trying transaction-service URL: {confirm_url}")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {payment_token}"
            }

            payload = {
                "gateway_response": {
                    "transaction_id": order_id,
                    "success": True,
                    "amount": 0,
                    "currency": "IDR",
                    "payment_method": "midtrans",
                    "metadata": {
                        "payment_token": payment_token,
                        "confirmed_at": datetime.now().isoformat(),
                        "webhook_source": "midtrans"
                    }
                },
                "token": payment_token
            }

            try:
                response = requests.post(confirm_url, json=payload, headers=headers, timeout=5)

                logger.info(f"📡 Response status from {base_url}: {response.status_code}")

                if response.status_code == 200:
                    logger.info(f"✅ Payment confirmation successful for order: {order_id} via {base_url}")
                    try:
                        response_data = response.json()
                        logger.info(f"📄 Response data: {response_data}")
                        return response_data
                    except:
                        logger.info(f"📄 Response text: {response.text}")
                        return {"status": "success", "message": "Confirmed", "url": base_url}
                else:
                    logger.warning(f"❌ Payment confirmation failed from {base_url}. Status: {response.status_code}")
                    logger.warning(f"Response: {response.text}")
                    continue  # Try next URL

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"🔌 Connection failed to {base_url}: Connection refused")
                continue  # Try next URL
            except requests.exceptions.Timeout as e:
                logger.warning(f"⏰ Timeout to {base_url}")
                continue  # Try next URL
            except Exception as e:
                logger.warning(f"💥 Request error to {base_url}: {str(e)}")
                continue  # Try next URL

        # If all URLs failed
        logger.error(f"❌ All transaction-service URLs failed for order: {order_id}")
        logger.error(f"Tried URLs: {urls_to_try}")
        return None

    except Exception as e:
        logger.error(f"💥 Error confirming payment for order {order_id}: {str(e)}")
        return None

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

    # DatabaseAdapter harus punya semua method yang diperlukan
    db_adapter = DatabaseAdapter(db)

    return PaymentService(
        payment_repository=midtrans_adapter,
        storage_repository=db_adapter  # Ini yang digunakan oleh webhook_handler
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
            verify_signature=False
        )

        logger.info(f"Webhook processed successfully: {result}")

        # Check if payment is successful and get order_id
        transaction_status = notification_data.get("transaction_status")
        order_id = notification_data.get("order_id")
        gross_amount = notification_data.get("gross_amount", "0")

        payment_confirmation_result = None
        payment_token = None

        # If payment is successful, create token and confirm payment
        if transaction_status in ["settlement", "capture"] and order_id:
            logger.info(f"Payment successful for order: {order_id}, creating token and confirming payment")

            # Create payment token
            payment_token = create_payment_token(order_id, transaction_status)
            logger.info(f"Token creation result for order {order_id}: {'SUCCESS' if payment_token else 'FAILED'}")

            if payment_token:
                logger.info(f"Token created successfully, attempting confirmation for order: {order_id}")

                # INI SALAH - confirm_payment_with_amount belum didefinisikan di line ini
                # payment_confirmation_result = await confirm_payment_with_amount(
                #     order_id, payment_token, gross_amount, notification_data
                # )

                # GANTI DENGAN confirm_payment yang sudah ada di line 65:
                payment_confirmation_result = await confirm_payment(order_id, payment_token)

                if payment_confirmation_result:
                    logger.info(f"Payment confirmation sent successfully to transaction-service for order: {order_id}")
                    logger.info(f"Confirmation response: {payment_confirmation_result}")
                else:
                    logger.warning(f"Failed to send payment confirmation to transaction-service for order: {order_id}")
            else:
                logger.error(f"Failed to create payment token for order: {order_id}")

        # Return success response that Midtrans expects
        response_data = {
            "status": "success",
            "message": "Notification processed successfully",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }

        # Add payment confirmation info if available
        if payment_token and payment_confirmation_result:
            response_data["payment_confirmation"] = {
                "order_id": order_id,
                "payment_token": payment_token[:50] + "...",  # Truncate for security
                "confirmation_result": payment_confirmation_result,
                "confirmed_at": datetime.now().isoformat(),
                "sent_to": "transaction-service:8004"
            }
        elif transaction_status in ["settlement", "capture"]:
            # More detailed error info
            error_detail = "Unknown error"
            if not payment_token:
                error_detail = "Failed to create payment token"
            elif not payment_confirmation_result:
                error_detail = "Failed to confirm payment with transaction-service"

            response_data["payment_confirmation"] = {
                "order_id": order_id,
                "status": "failed",
                "message": f"Failed to create token or confirm payment to transaction-service: {error_detail}",
                "token_created": payment_token is not None,
                "token_preview": payment_token[:30] + "..." if payment_token else None
            }

        return response_data

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        logger.error(f"Notification data: {notification_data}")

        # Still return 200 to prevent Midtrans from retrying
        return {
            "status": "error",
            "message": f"Failed to process notification: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def confirm_payment_with_amount(order_id: str, payment_token: str, gross_amount: str, notification_data: Dict):
    """Enhanced confirm payment with amount and metadata from Midtrans notification"""
    try:
        TRANSACTION_SERVICE_URL = os.getenv("TRANSACTION_SERVICE_URL", "http://localhost:8004")
        confirm_url = f"{TRANSACTION_SERVICE_URL}/payments/{order_id}/confirm"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {payment_token}"
        }

        # Convert gross_amount to float
        try:
            amount = float(gross_amount.replace(",", "")) if isinstance(gross_amount, str) else float(gross_amount)
        except:
            amount = 0.0

        payload = {
            "gateway_response": {
                "transaction_id": notification_data.get("transaction_id", order_id),
                "success": True,
                "amount": amount,
                "currency": notification_data.get("currency", "IDR"),
                "payment_method": notification_data.get("payment_type", "midtrans"),
                "metadata": {
                    "midtrans_transaction_id": notification_data.get("transaction_id"),
                    "midtrans_order_id": order_id,
                    "transaction_status": notification_data.get("transaction_status"),
                    "payment_token": payment_token,
                    "confirmed_at": datetime.now().isoformat(),
                    "webhook_source": "midtrans",
                    "fraud_status": notification_data.get("fraud_status"),
                    "status_code": notification_data.get("status_code"),
                    "status_message": notification_data.get("status_message")
                }
            },
            "token": payment_token
        }

        logger.info(f"Sending payment confirmation to transaction-service: {confirm_url}")
        logger.info(f"Payload: {payload}")

        response = requests.post(confirm_url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info(f"Transaction-service payment confirmation successful for order: {order_id}")
            return response.json()
        else:
            logger.error(f"Transaction-service payment confirmation failed. Status: {response.status_code}, Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error confirming payment with transaction-service for order {order_id}: {str(e)}")
        return None

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
