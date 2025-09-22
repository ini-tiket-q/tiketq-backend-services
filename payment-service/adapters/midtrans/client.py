import json
import logging
import base64
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MidtransClient:
    """Midtrans HTTP client for all API operations"""

    def __init__(self, server_key: str, client_key: str, is_production: bool = False):
        self.server_key = server_key
        self.client_key = client_key
        self.is_production = is_production

        # Set base URLs
        if is_production:
            self.api_url = "https://api.midtrans.com/v2"
            self.snap_url = "https://app.midtrans.com/snap/v1/transactions"
        else:
            self.api_url = "https://api.sandbox.midtrans.com/v2"
            self.snap_url = "https://app.sandbox.midtrans.com/snap/v1/transactions"

        # Setup authorization
        auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def create_transaction(self, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Create transaction via Snap API"""
        try:
            logger.info(f"Creating transaction with payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                self.snap_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=timeout
            )

            logger.info(f"Snap API response: {response.status_code}")

            if response.status_code != 201:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('error_messages', [error_detail])
                except:
                    pass
                raise Exception(f"Snap API error: {response.status_code} - {error_detail}")

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Failed to create transaction: {str(e)}")

    def get_transaction_status(self, transaction_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get transaction status"""
        try:
            status_url = f"{self.api_url}/{transaction_id}/status"

            response = requests.get(
                status_url,
                headers=self.headers,
                timeout=timeout
            )

            logger.info(f"Status API response: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Transaction not found: {transaction_id}")
                return {"transaction_status": "pending"}
            else:
                logger.warning(f"Failed to get status: {response.status_code}")
                return {"transaction_status": "pending"}

        except requests.RequestException as e:
            logger.error(f"Status request failed: {e}")
            return {"transaction_status": "pending"}

    def cancel_transaction(self, transaction_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Cancel transaction"""
        try:
            cancel_url = f"{self.api_url}/{transaction_id}/cancel"

            response = requests.post(
                cancel_url,
                headers=self.headers,
                timeout=timeout
            )

            if response.status_code not in [200, 201]:
                raise Exception(f"Cancel API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Cancel request failed: {e}")
            raise Exception(f"Failed to cancel transaction: {str(e)}")

    def refund_transaction(self, transaction_id: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Refund transaction"""
        try:
            refund_url = f"{self.api_url}/{transaction_id}/refund"

            response = requests.post(
                refund_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=timeout
            )

            if response.status_code not in [200, 201]:
                raise Exception(f"Refund API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Refund request failed: {e}")
            raise Exception(f"Failed to refund transaction: {str(e)}")