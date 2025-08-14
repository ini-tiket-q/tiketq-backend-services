import json
import logging  # Fix: ganti import logger dengan import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
import base64

from domain.models import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentMethod,
    PaymentNotification
)
from domain.repository import PaymentRepository

# Setup logger
logger = logging.getLogger(__name__)


class MidtransAdapter(PaymentRepository):
    """
    Adapter implementation for Midtrans payment gateway.
    Implements the PaymentRepository interface (port).
    """

    def __init__(
        self,
        server_key: str,
        client_key: str,
        is_production: bool = False
    ):
        """
        Initialize Midtrans adapter with API keys
        """
        self.server_key = server_key
        self.client_key = client_key
        self.is_production = is_production

        # Set base URLs based on environment
        if is_production:
            self.api_url = "https://api.midtrans.com/v2"
            self.snap_url = "https://app.midtrans.com/snap/v1/transactions"
        else:
            self.api_url = "https://api.sandbox.midtrans.com/v2"
            self.snap_url = "https://app.sandbox.midtrans.com/snap/v1/transactions"

        # Setup authorization header
        auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _map_payment_method(self, payment_method: PaymentMethod) -> Dict[str, Any]:
        """Map payment method to Midtrans enabled payments"""
        # Return enabled payments instead of specific configuration
        if payment_method == PaymentMethod.CREDIT_CARD:
            return {
                "enabled_payments": ["credit_card"],
                "credit_card": {"secure": True}
            }
        elif payment_method == PaymentMethod.BANK_TRANSFER:
            return {
                "enabled_payments": ["bank_transfer"],
                "bank_transfer": {"bank": "bca"}
            }
        elif payment_method == PaymentMethod.E_WALLET:
            return {
                "enabled_payments": ["gopay"],
                "gopay": {"enable_callback": True}
            }
        elif payment_method == PaymentMethod.QRIS:
            return {
                "enabled_payments": ["qris"],
                "qris": {"acquirer": "gopay"}
            }
        elif payment_method == PaymentMethod.RETAIL:
            return {
                "enabled_payments": ["cstore"],
                "cstore": {"store": "indomaret"}
            }
        else:
            # Default: enable all payment methods
            return {
                "enabled_payments": [
                    "credit_card", "bank_transfer", "gopay", "shopeepay",
                    "qris", "cstore", "bca_va", "bni_va", "bri_va"
                ]
            }

    async def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Create a payment transaction with Midtrans"""
        transaction_time = datetime.now()

        # Validate required fields
        if not payment_request.order_id:
            raise ValueError("Order ID is required")
        if not payment_request.amount or payment_request.amount <= 0:
            raise ValueError("Amount must be greater than 0")

        # Build transaction payload
        payload = {
            "transaction_details": {
                "order_id": payment_request.order_id,
                "gross_amount": int(payment_request.amount)
            },
            "customer_details": payment_request.customer_details,
            "item_details": payment_request.item_details
        }

        # Add expiry if specified
        if payment_request.expiry_duration:
            payload["expiry"] = {
                "unit": "hour",
                "duration": payment_request.expiry_duration
            }

        # Add payment method configuration
        payment_config = self._map_payment_method(payment_request.payment_method)
        payload.update(payment_config)

        try:
            print(f"Sending payload to Midtrans: {json.dumps(payload, indent=2)}")

            # Make request to Midtrans Snap API
            response = requests.post(
                self.snap_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )

            print(f"Midtrans response status: {response.status_code}")
            print(f"Midtrans response: {response.text}")

            if response.status_code != 201:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('error_messages', [error_detail])
                except:
                    pass
                raise ValueError(f"Midtrans API error: {response.status_code} - {error_detail}")

            result = response.json()

            # Calculate expiry time
            expiry_time = None
            if payment_request.expiry_duration:
                expiry_time = transaction_time + timedelta(hours=payment_request.expiry_duration)

            # Create comprehensive metadata
            metadata = {
                "token": result.get("token"),
                "redirect_url": result.get("redirect_url"),
                "midtrans_response": result,
                "payment_config": payment_config,
                "expiry_duration": payment_request.expiry_duration
            }

            return PaymentResponse(
                id=f"payment-{payment_request.order_id}",
                order_id=payment_request.order_id,
                transaction_id=payment_request.order_id,
                amount=payment_request.amount,
                status=PaymentStatus.PENDING,
                payment_method=payment_request.payment_method,
                payment_url=result.get("redirect_url"),  # This is the key field that was missing
                created_at=transaction_time,
                updated_at=transaction_time,
                metadata=metadata
            )

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to create payment with Midtrans: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error creating payment: {str(e)}")

    async def get_payment_status(self, transaction_id: str) -> PaymentStatus:
        """Get payment status from Midtrans"""
        try:
            # Midtrans API to check transaction status
            status_url = f"{self.api_url}/{transaction_id}/status"

            response = requests.get(
                status_url,
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                transaction_status = result.get('transaction_status')
                fraud_status = result.get('fraud_status')

                # Map status
                if fraud_status == "deny":
                    return PaymentStatus.FAILED

                status_mapping = {
                    "capture": PaymentStatus.SUCCESS,
                    "settlement": PaymentStatus.SUCCESS,
                    "pending": PaymentStatus.PENDING,
                    "deny": PaymentStatus.FAILED,
                    "cancel": PaymentStatus.CANCELED,
                    "expire": PaymentStatus.EXPIRED,
                    "refund": PaymentStatus.REFUNDED,
                }

                return status_mapping.get(transaction_status, PaymentStatus.PENDING)

            else:
                logger.warning(f"Failed to get status from Midtrans: {response.status_code}")
                return PaymentStatus.PENDING

        except Exception as e:
            logger.error(f"Error getting payment status from Midtrans: {e}")
            return PaymentStatus.PENDING

    async def cancel_payment(self, transaction_id: str, reason: Optional[str] = None) -> PaymentResponse:
        """
        Cancel a payment with Midtrans

        Args:
            transaction_id: Midtrans transaction ID
            reason: Cancellation reason

        Returns:
            PaymentResponse: Updated payment details
        """
        try:
            response = requests.post(
                f"{self.api_url}/{transaction_id}/cancel",
                headers=self.headers
            )
            response.raise_for_status()

            result = response.json()

            return PaymentResponse(
                id=f"payment-{transaction_id}",
                order_id=result.get("order_id", transaction_id),
                transaction_id=transaction_id,
                amount=float(result.get("gross_amount", 0)),
                status=PaymentStatus.CANCELED,
                payment_method=PaymentMethod.CREDIT_CARD,  # Default, should be retrieved from DB
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=result
            )

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to cancel payment: {str(e)}")

    async def refund_payment(self, transaction_id: str, amount: Optional[float] = None, reason: str = None) -> PaymentResponse:
        """
        Refund a payment with Midtrans

        Args:
            transaction_id: Midtrans transaction ID
            amount: Amount to refund (if None, full refund)
            reason: Refund reason

        Returns:
            PaymentResponse: Updated payment details
        """
        try:
            # If no amount specified, get transaction details for full refund
            if amount is None:
                status_response = requests.get(
                    f"{self.api_url}/{transaction_id}/status",
                    headers=self.headers
                )
                status_response.raise_for_status()
                status_result = status_response.json()
                amount = float(status_result.get("gross_amount", 0))

            refund_payload = {
                "refund_key": f"refund-{transaction_id}-{int(datetime.now().timestamp())}",
                "amount": int(amount),
                "reason": reason or "Customer requested refund"
            }

            response = requests.post(
                f"{self.api_url}/{transaction_id}/refund",
                headers=self.headers,
                data=json.dumps(refund_payload)
            )
            response.raise_for_status()

            result = response.json()

            return PaymentResponse(
                id=f"payment-{transaction_id}",
                order_id=result.get("order_id", transaction_id),
                transaction_id=transaction_id,
                amount=amount,
                status=PaymentStatus.REFUNDED,
                payment_method=PaymentMethod.CREDIT_CARD,  # Default, should be retrieved from DB
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=result
            )

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to refund payment: {str(e)}")

    async def handle_webhook(self, notification_data: dict) -> PaymentResponse:
        """
        Process payment notification from payment gateway

        Args:
            notification_data: Raw notification data from Midtrans

        Returns:
            PaymentResponse: Updated payment details
        """
        try:
            transaction_id = notification_data.get("transaction_id", "")
            order_id = notification_data.get("order_id", "")
            transaction_status = notification_data.get("transaction_status", "")
            gross_amount = float(notification_data.get("gross_amount", 0))

            # Map status
            status_mapping = {
                "pending": PaymentStatus.PENDING,
                "capture": PaymentStatus.SUCCESS,
                "settlement": PaymentStatus.SUCCESS,
                "deny": PaymentStatus.FAILED,
                "cancel": PaymentStatus.CANCELED,
                "expire": PaymentStatus.EXPIRED,
                "refund": PaymentStatus.REFUNDED,
                "partial_refund": PaymentStatus.REFUNDED
            }

            status = status_mapping.get(transaction_status.lower(), PaymentStatus.PENDING)

            return PaymentResponse(
                id=f"payment-{transaction_id}",
                order_id=order_id,
                transaction_id=transaction_id,
                amount=gross_amount,
                status=status,
                payment_method=PaymentMethod.CREDIT_CARD,  # Default
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=notification_data
            )

        except Exception as e:
            raise ValueError(f"Failed to process webhook: {str(e)}")

    async def handle_notification(self, notification_data: dict) -> PaymentNotification:
        """
        Process payment notification and return PaymentNotification

        Args:
            notification_data: Raw notification data from Midtrans

        Returns:
            PaymentNotification: Processed notification
        """
        try:
            transaction_id = notification_data.get("transaction_id", "")
            order_id = notification_data.get("order_id", "")
            transaction_status = notification_data.get("transaction_status", "")
            gross_amount = float(notification_data.get("gross_amount", 0))
            payment_type = notification_data.get("payment_type", "")

            # Map status
            status_mapping = {
                "pending": PaymentStatus.PENDING,
                "capture": PaymentStatus.SUCCESS,
                "settlement": PaymentStatus.SUCCESS,
                "deny": PaymentStatus.FAILED,
                "cancel": PaymentStatus.CANCELED,
                "expire": PaymentStatus.EXPIRED,
                "refund": PaymentStatus.REFUNDED,
                "partial_refund": PaymentStatus.REFUNDED
            }

            status = status_mapping.get(transaction_status.lower(), PaymentStatus.PENDING)

            return PaymentNotification(
                transaction_id=transaction_id,
                order_id=order_id,
                status=status,
                amount=gross_amount,
                payment_type=payment_type,
                processed_at=datetime.now()
            )

        except Exception as e:
            raise ValueError(f"Failed to process notification: {str(e)}")

        transaction_details = {
            "order_id": payment_request.order_id,
            "gross_amount": payment_request.amount
        }

        customer_details = {
            "first_name": payment_request.customer_name,
            "email": payment_request.customer_email,
            "phone": payment_request.customer_phone or ""
        }

        item_details = payment_request.items or [{
            "id": "default",
            "price": payment_request.amount,
            "quantity": 1,
            "name": payment_request.description or "Payment"
        }]

        payment_type_config = self._map_payment_method(payment_request.payment_method)

        transaction_data = {
            "transaction_details": transaction_details,
            "customer_details": customer_details,
            "item_details": item_details,
            "expiry": {
                "unit": "hour",
                "duration": payment_request.expiry_duration
            }
        }

        if payment_type_config:
            transaction_data.update(payment_type_config)

        try:
            response = self.snap.create_transaction(transaction_data)

            payment_id = response.get("transaction_id", "")
            token = response.get("token", "")
            redirect_url = response.get("redirect_url", "")
            payment_response = PaymentResponse(
                payment_id=payment_id,
                order_id=payment_request.order_id,
                status=PaymentStatus.PENDING,
                amount=payment_request.amount,
                payment_method=payment_request.payment_method,
                transaction_time=transaction_time,
                expiry_time=expiry_time,
                payment_url=f"https://app.midtrans.com/snap/v2/vtweb/{token}",
                token=token,
                redirect_url=redirect_url
            )

            return payment_response

        except Exception as e:
            raise ValueError(f"Failed to create payment: {str(e)}")

    async def get_payment_status(self, order_id: str) -> PaymentStatus:
        """Get payment status from Midtrans using order_id"""
        try:
            # Midtrans API to check transaction status
            status_url = f"{self.api_url}/{order_id}/status"

            logger.info(f"Checking payment status at: {status_url}")

            response = requests.get(
                status_url,
                headers=self.headers,
                timeout=30
            )

            logger.info(f"Midtrans status response: {response.status_code}")
            logger.info(f"Midtrans status response body: {response.text}")

            if response.status_code == 200:
                result = response.json()
                transaction_status = result.get('transaction_status')
                fraud_status = result.get('fraud_status')

                logger.info(f"Transaction status: {transaction_status}, Fraud status: {fraud_status}")

                # Handle fraud status first
                if fraud_status == "deny":
                    return PaymentStatus.FAILED

                # Map transaction status
                status_mapping = {
                    "capture": PaymentStatus.SUCCESS,
                    "settlement": PaymentStatus.SUCCESS,
                    "pending": PaymentStatus.PENDING,
                    "deny": PaymentStatus.FAILED,
                    "cancel": PaymentStatus.CANCELED,
                    "expire": PaymentStatus.EXPIRED,
                    "refund": PaymentStatus.REFUNDED,
                    "partial_refund": PaymentStatus.REFUNDED,
                }

                mapped_status = status_mapping.get(transaction_status, PaymentStatus.PENDING)
                logger.info(f"Mapped status: {mapped_status}")
                return mapped_status

            elif response.status_code == 404:
                logger.warning(f"Transaction not found in Midtrans: {order_id}")
                return PaymentStatus.PENDING
            else:
                logger.warning(f"Failed to get status from Midtrans: {response.status_code} - {response.text}")
                return PaymentStatus.PENDING

        except Exception as e:
            logger.error(f"Error getting payment status from Midtrans: {e}")
            return PaymentStatus.PENDING

    # Clean up duplicate methods - remove the extra ones at the end of file
