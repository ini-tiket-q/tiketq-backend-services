import logging
from fastapi import APIRouter, HTTPException, status, Body, Depends, Request
from typing import Dict, Any
from datetime import datetime, timedelta
from jose import jwt, JWTError
import requests
import os
import asyncio

from domain.services import PaymentService, get_database_session
from adapters.webhook_handler import WebhookHandler
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-payment-key")
ALGORITHM = "HS256"

# Create router instance
router = APIRouter()

def create_payment_token(order_id: str, transaction_status: str):
    """Create JWT token for payment confirmation"""
    try:
        logger.info(f"Creating payment token for order: {order_id}")
        payload = {
            "order_id": order_id,
            "transaction_status": transaction_status,
            "token": "success",
            "service": "payment-service",
            "iat": datetime.now().timestamp(),
            "exp": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"✅ Token created successfully for order: {order_id}")
        return token
    except Exception as e:
        logger.error(f"❌ Error creating payment token: {str(e)}", exc_info=True)
        return None

async def send_confirmation_with_retry(url: str, payload: dict, headers: dict, max_retries: int = 3):
    """Send confirmation with retry logic"""
    for retry in range(max_retries):
        try:
            logger.info(f"🔄 Retry {retry + 1}/{max_retries} for URL: {url}")

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            logger.info(f"📡 Response status: {response.status_code}")
            logger.info(f"📄 Response content: {response.text}")

            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {"status": "success", "message": "Confirmed", "response": response.text}
            elif response.status_code == 500:
                logger.warning(f"⚠️ Transaction-service error (500) - retry {retry + 1}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2)  # Wait 2 seconds before retry
                    continue
                else:
                    return None
            else:
                logger.warning(f"❌ Non-retryable error: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Timeout on retry {retry + 1}")
            if retry < max_retries - 1:
                await asyncio.sleep(1)
                continue
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"🔌 Connection error on retry {retry + 1}: {str(e)}")
            if retry < max_retries - 1:
                await asyncio.sleep(1)
                continue
        except Exception as e:
            logger.warning(f"💥 Unexpected error on retry {retry + 1}: {str(e)}")
            if retry < max_retries - 1:
                await asyncio.sleep(1)
                continue

    return None

async def confirm_payment_with_amount(order_id: str, payment_token: str, gross_amount: str, notification_data: Dict):
    """Enhanced confirm payment with amount and metadata from Midtrans notification"""
    try:
        # Primary Cloudflare URL only - since local/docker are not working
        TRANSACTION_SERVICE_URL = os.getenv("TRANSACTION_SERVICE_URL", "https://transaction.satria-dev.site")

        confirm_url = f"{TRANSACTION_SERVICE_URL}/payments/{order_id}/confirm"

        logger.info(f"🚀 Attempting payment confirmation to: {confirm_url}")

        # Standard headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {payment_token}",
            "User-Agent": "TiketQ-Payment-Service/1.0",
            "X-Source": "payment-webhook",
            "X-Order-ID": order_id
        }

        # Convert gross_amount to float
        try:
            amount = float(gross_amount.replace(",", "")) if isinstance(gross_amount, str) else float(gross_amount)
        except:
            amount = 0.0

        # Enhanced payload with more debugging info
        payload = {
            "gateway_response": {
                "transaction_id": notification_data.get("transaction_id", order_id),
                "success": True,
                "amount": amount,
                "currency": notification_data.get("currency", "IDR"),
                "payment_method": notification_data.get("payment_type", "midtrans"),
                "status": "SUCCESS",
                "metadata": {
                    "midtrans_transaction_id": notification_data.get("transaction_id"),
                    "midtrans_order_id": order_id,
                    "transaction_status": notification_data.get("transaction_status"),
                    "payment_token": payment_token,
                    "confirmed_at": datetime.now().isoformat(),
                    "webhook_source": "midtrans",
                    "fraud_status": notification_data.get("fraud_status"),
                    "status_code": notification_data.get("status_code"),
                    "status_message": notification_data.get("status_message"),
                    "settlement_time": notification_data.get("settlement_time"),
                    "transaction_time": notification_data.get("transaction_time"),
                    "merchant_id": notification_data.get("merchant_id"),
                    "gross_amount": gross_amount,
                    "webhook_timestamp": datetime.now().isoformat()
                }
            },
            "token": payment_token,
            "status": "SUCCESS",
            "webhook_metadata": {
                "order_id": order_id,
                "amount": amount,
                "currency": "IDR",
                "payment_method": notification_data.get("payment_type", "midtrans"),
                "processed_at": datetime.now().isoformat()
            }
        }

        logger.info(f"📤 Sending enhanced payload with debugging info")
        logger.info(f"📤 Payload summary: order_id={order_id}, amount={amount}, method={notification_data.get('payment_type')}")

        # Send with retry logic
        result = await send_confirmation_with_retry(confirm_url, payload, headers)

        if result:
            logger.info(f"✅ Payment confirmation successful for order: {order_id}")
            return result
        else:
            logger.error(f"❌ Payment confirmation failed after all retries for order: {order_id}")
            return None

    except Exception as e:
        logger.error(f"💥 Error confirming payment for order {order_id}: {str(e)}")
        return None

async def simple_confirm_payment(order_id: str, payment_token: str):
    """Simple fallback confirmation method"""
    try:
        TRANSACTION_SERVICE_URL = os.getenv("TRANSACTION_SERVICE_URL", "https://transaction.satria-dev.site")
        confirm_url = f"{TRANSACTION_SERVICE_URL}/payments/{order_id}/confirm"

        logger.info(f"🔄 Simple fallback confirmation for order: {order_id}")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TiketQ-Payment-Service/1.0",
            "X-Source": "payment-webhook-fallback"
        }

        # Minimal payload
        payload = {
            "gateway_response": {
                "transaction_id": order_id,
                "success": True,
                "amount": 0,
                "currency": "IDR",
                "payment_method": "midtrans",
                "status": "SUCCESS",
                "metadata": {
                    "payment_token": payment_token,
                    "confirmed_at": datetime.now().isoformat(),
                    "webhook_source": "midtrans"
                }
            },
            "token": payment_token,
            "status": "SUCCESS"
        }

        logger.info(f"📤 Sending simple fallback payload")

        result = await send_confirmation_with_retry(confirm_url, payload, headers, max_retries=2)

        if result:
            logger.info(f"✅ Simple fallback confirmation successful for order: {order_id}")
            return result
        else:
            logger.error(f"❌ Simple fallback confirmation failed for order: {order_id}")
            return None

    except Exception as e:
        logger.error(f"💥 Error in simple confirm payment for order {order_id}: {str(e)}")
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
        logger.info(f"🔔 Received Midtrans webhook notification")
        logger.info(f"📋 Headers: {dict(request.headers)}")
        logger.info(f"📋 Notification data: {notification_data}")

        # Process webhook and update payment status
        result = await webhook_handler.process_webhook(
            notification_data=notification_data,
            payment_repository=payment_service.storage_repository,
            verify_signature=False
        )

        logger.info(f"✅ Webhook processed successfully: {result}")

        # Check if payment is successful and get order_id
        transaction_status = notification_data.get("transaction_status")
        order_id = notification_data.get("order_id")
        gross_amount = notification_data.get("gross_amount", "0")

        payment_confirmation_result = None
        payment_token = None

        # If payment is successful, create token and confirm payment
        if transaction_status in ["settlement", "capture"] and order_id:
            logger.info(f"💰 Payment successful for order: {order_id}, creating token and confirming payment")
            logger.info(f"💰 Amount: {gross_amount}, Method: {notification_data.get('payment_type')}")

            # Create payment token
            payment_token = create_payment_token(order_id, transaction_status)
            logger.info(f"🔑 Token creation result for order {order_id}: {'SUCCESS' if payment_token else 'FAILED'}")

            if payment_token:
                logger.info(f"🚀 Token created successfully, attempting confirmation for order: {order_id}")

                # Try enhanced confirm first
                payment_confirmation_result = await confirm_payment_with_amount(
                    order_id, payment_token, gross_amount, notification_data
                )

                if payment_confirmation_result:
                    logger.info(f"✅ Enhanced payment confirmation successful for order: {order_id}")
                else:
                    logger.warning(f"❌ Enhanced confirmation failed, trying simple fallback for order: {order_id}")
                    # Try simple fallback
                    payment_confirmation_result = await simple_confirm_payment(order_id, payment_token)

                    if payment_confirmation_result:
                        logger.info(f"✅ Simple fallback confirmation successful for order: {order_id}")
                    else:
                        logger.error(f"❌ All confirmation methods failed for order: {order_id}")
            else:
                logger.error(f"❌ Failed to create payment token for order: {order_id}")

        # Return success response that Midtrans expects
        response_data = {
            "status": "success",
            "message": "Notification processed successfully",
            "timestamp": datetime.now().isoformat(),
            "data": result,
            "webhook_processed": True
        }

        # Add payment confirmation info if available
        if payment_token and payment_confirmation_result:
            response_data["payment_confirmation"] = {
                "order_id": order_id,
                "payment_token_preview": payment_token[:30] + "...",
                "confirmation_status": "success",
                "confirmation_result": payment_confirmation_result,
                "confirmed_at": datetime.now().isoformat(),
                "amount": gross_amount,
                "payment_method": notification_data.get('payment_type')
            }
        elif transaction_status in ["settlement", "capture"]:
            # Add detailed error info
            error_detail = "Unknown error"
            if not payment_token:
                error_detail = "Failed to create payment token"
            elif not payment_confirmation_result:
                error_detail = "Failed to confirm payment with transaction-service (all methods failed)"

            response_data["payment_confirmation"] = {
                "order_id": order_id,
                "confirmation_status": "failed",
                "error": error_detail,
                "token_created": payment_token is not None,
                "token_preview": payment_token[:30] + "..." if payment_token else None,
                "amount": gross_amount,
                "payment_method": notification_data.get('payment_type'),
                "transaction_service_error": "HTTP 500 - Failed to confirm payment"
            }

        return response_data

    except Exception as e:
        logger.error(f"💥 Error handling webhook: {e}")
        logger.error(f"📋 Notification data: {notification_data}")

        # Still return 200 to prevent Midtrans from retrying
        return {
            "status": "error",
            "message": f"Failed to process notification: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "webhook_processed": False
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
        "cloudflare_ready": True
    }

@router.get("/health",
    summary="Health check for webhook service",
    description="Check if webhook service and transaction service are reachable")
async def webhook_health_check():
    """Health check endpoint"""
    try:
        TRANSACTION_SERVICE_URL = os.getenv("TRANSACTION_SERVICE_URL", "https://transaction.satria-dev.site")

        # Test transaction service connectivity
        try:
            response = requests.get(f"{TRANSACTION_SERVICE_URL}/health", timeout=10)
            transaction_service_status = {
                "reachable": True,
                "status_code": response.status_code,
                "response": response.text[:100]
            }
        except Exception as e:
            transaction_service_status = {
                "reachable": False,
                "error": str(e)
            }

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "payment-service-webhook",
            "transaction_service": transaction_service_status,
            "cloudflare_domain": TRANSACTION_SERVICE_URL
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
