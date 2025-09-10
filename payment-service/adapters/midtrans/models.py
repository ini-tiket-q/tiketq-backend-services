from typing import Dict, Any
from datetime import datetime
from domain.models import PaymentMethod, PaymentStatus


class MidtransMapper:
    """Maps domain models to/from Midtrans API formats"""

    @staticmethod
    def map_payment_method_to_config(payment_method: PaymentMethod) -> Dict[str, Any]:
        """Map payment method to Midtrans enabled payments configuration"""
        if payment_method == PaymentMethod.CREDIT_CARD:
            return {
                "enabled_payments": ["credit_card"],
                "credit_card": {"secure": True}
            }
        elif payment_method == PaymentMethod.BANK_TRANSFER:
            return {
                "enabled_payments": ["bank_transfer", "bca_va", "bni_va", "bri_va"],  # Tambahkan VA banks
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

    @staticmethod
    def map_status_from_midtrans(transaction_status: str, fraud_status: str = None) -> PaymentStatus:
        """Map Midtrans transaction status to domain PaymentStatus"""
        # Handle fraud status first
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
            "partial_refund": PaymentStatus.REFUNDED,
        }

        return status_mapping.get(transaction_status.lower(), PaymentStatus.PENDING)

    @staticmethod
    def determine_payment_method_from_notification(notification_data: Dict[str, Any]) -> PaymentMethod:
        """Determine payment method from Midtrans notification data"""
        payment_type = notification_data.get("payment_type", "").lower()

        if "credit_card" in payment_type:
            return PaymentMethod.CREDIT_CARD
        elif "bank_transfer" in payment_type or "_va" in payment_type:
            return PaymentMethod.BANK_TRANSFER
        elif "gopay" in payment_type or "shopeepay" in payment_type:
            return PaymentMethod.E_WALLET
        elif "qris" in payment_type:
            return PaymentMethod.QRIS
        elif "cstore" in payment_type:
            return PaymentMethod.RETAIL
        else:
            return PaymentMethod.CREDIT_CARD  # Default fallback