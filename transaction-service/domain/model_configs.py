"""
Model configuration and examples for Pydantic models.
This file contains reusable model configurations, examples, and validation schemas
that can be used across different models to maintain consistency.
"""

from typing import Dict, Any, List


class ModelExamples:
    """
    Centralized examples for Pydantic models.
    This class contains example data that can be reused across models.
    """
    
    # Transaction Item Examples
    FLIGHT_TICKET_ITEM = {
        "name": "Jakarta to Bali Flight",
        "price": 1200000,
        "quantity": 1,
        "description": "Economy class ticket",
        "metadata": {
            "flight_number": "GA123",
            "departure": "CGK",
            "arrival": "DPS",
            "departure_time": "2025-08-25T08:00:00Z"
        }
    }
    
    AIRPORT_TAX_ITEM = {
        "name": "Airport Tax",
        "price": 300000,
        "quantity": 1,
        "description": "Airport departure tax",
        "metadata": {
            "tax_type": "departure_tax"
        }
    }
    
    HOTEL_BOOKING_ITEM = {
        "name": "Hotel Room Booking",
        "price": 850000,
        "quantity": 2,
        "description": "Deluxe room for 2 nights",
        "metadata": {
            "hotel_name": "Grand Indonesia Hotel",
            "room_type": "deluxe",
            "check_in": "2025-08-25",
            "check_out": "2025-08-27",
            "nights": 2
        }
    }
    
    FERRY_TICKET_ITEM = {
        "name": "Ferry Ticket",
        "price": 450000,
        "quantity": 1,
        "description": "Economy class ferry ticket",
        "metadata": {
            "route": "Jakarta - Lampung",
            "departure_port": "Merak",
            "arrival_port": "Bakauheni",
            "departure_time": "2025-08-25T09:00:00Z"
        }
    }
    
    # Transaction Metadata Examples
    FLIGHT_BOOKING_METADATA = {
        "booking_reference": "TQ-FL-20250825-001",
        "passenger_name": "John Doe",
        "passenger_email": "johndoe@example.com",
        "special_requests": "Window seat"
    }
    
    HOTEL_BOOKING_METADATA = {
        "booking_reference": "TQ-HT-20250825-002",
        "guest_name": "Jane Smith",
        "guest_email": "janesmith@example.com",
        "special_requests": "Late checkout"
    }
    
    FERRY_BOOKING_METADATA = {
        "booking_reference": "TQ-FR-20250825-003",
        "passenger_name": "Bob Johnson",
        "passenger_email": "bob@example.com",
        "vehicle_type": "car"
    }


class ModelConfigs:
    """
    Centralized model configurations for Pydantic models.
    This class contains reusable model_config dictionaries.
    """
    
    @staticmethod
    def transaction_item_config() -> Dict[str, Any]:
        """Configuration for TransactionItem model"""
        return {
            "json_schema_extra": {
                "examples": [
                    ModelExamples.FLIGHT_TICKET_ITEM,
                    ModelExamples.HOTEL_BOOKING_ITEM,
                    ModelExamples.FERRY_TICKET_ITEM
                ]
            }
        }
    
    @staticmethod
    def transaction_create_config() -> Dict[str, Any]:
        """Configuration for TransactionCreateRequest model"""
        return {
            "json_schema_extra": {
                "examples": [
                    {
                        "transaction_type": "BOOKING",
                        "amount": 1565000,
                        "currency": "IDR",
                        "service_type": "FLIGHTS",
                        "items": [
                            ModelExamples.FLIGHT_TICKET_ITEM,
                            ModelExamples.AIRPORT_TAX_ITEM
                        ],
                        "subtotal": 1500000,
                        "tax": 165000,
                        "discount": 100000,
                        "total": 1565000,
                        "payment_method": "CREDIT_CARD",
                        "payment_gateway": "MIDTRANS",
                        "metadata": ModelExamples.FLIGHT_BOOKING_METADATA
                    },
                    {
                        "transaction_type": "BOOKING",
                        "amount": 1870000,
                        "currency": "IDR",
                        "service_type": "HOTELS",
                        "items": [
                            ModelExamples.HOTEL_BOOKING_ITEM
                        ],
                        "subtotal": 1700000,
                        "tax": 187000,
                        "discount": 17000,
                        "total": 1870000,
                        "payment_method": "BANK_TRANSFER",
                        "payment_gateway": "MIDTRANS",
                        "metadata": ModelExamples.HOTEL_BOOKING_METADATA
                    },
                    {
                        "transaction_type": "BOOKING",
                        "amount": 495000,
                        "currency": "IDR",
                        "service_type": "FERRIES",
                        "items": [
                            ModelExamples.FERRY_TICKET_ITEM
                        ],
                        "subtotal": 450000,
                        "tax": 45000,
                        "discount": 0,
                        "total": 495000,
                        "payment_method": "E_WALLET",
                        "payment_gateway": "GOPAY",
                        "metadata": ModelExamples.FERRY_BOOKING_METADATA
                    }
                ]
            }
        }
    
    @staticmethod
    def order_create_config() -> Dict[str, Any]:
        """Configuration for OrderCreateRequest model"""
        return {
            "json_schema_extra": {
                "examples": [
                    {
                        "service_type": "FLIGHTS",
                        "items": [
                            ModelExamples.FLIGHT_TICKET_ITEM,
                            ModelExamples.AIRPORT_TAX_ITEM
                        ],
                        "tax": 165000,
                        "discount": 100000,
                        "metadata": ModelExamples.FLIGHT_BOOKING_METADATA
                    },
                    {
                        "service_type": "HOTELS",
                        "items": [
                            ModelExamples.HOTEL_BOOKING_ITEM
                        ],
                        "tax": 187000,
                        "discount": 17000,
                        "metadata": ModelExamples.HOTEL_BOOKING_METADATA
                    }
                ]
            }
        }
    
    @staticmethod
    def payment_create_config() -> Dict[str, Any]:
        """Configuration for PaymentCreateRequest model"""
        return {
            "json_schema_extra": {
                "examples": [
                    {
                        "transaction_id": 1,
                        "amount": 1565000,
                        "currency": "IDR",
                        "payment_method": "CREDIT_CARD",
                        "payment_gateway": "MIDTRANS",
                        "gateway_transaction_id": "TXN-MIDTRANS-20250825-001",
                        "metadata": {
                            "card_type": "visa",
                            "card_last_digits": "1234",
                            "bank_name": "BCA"
                        }
                    },
                    {
                        "transaction_id": 2,
                        "amount": 495000,
                        "currency": "IDR",
                        "payment_method": "E_WALLET",
                        "payment_gateway": "GOPAY",
                        "gateway_transaction_id": "TXN-GOPAY-20250825-002",
                        "metadata": {
                            "wallet_phone": "+62812345678",
                            "promo_code": "SAVE10"
                        }
                    }
                ]
            }
        }


class ValidationMessages:
    """
    Centralized validation error messages.
    This class contains reusable validation messages for consistency.
    """
    
    # Amount validation messages
    AMOUNT_POSITIVE = "Amount must be greater than 0"
    AMOUNT_MAX_EXCEEDED = "Amount exceeds maximum allowed value"
    
    # Currency validation messages
    CURRENCY_INVALID_LENGTH = "Currency must be a 3-character code"
    
    # Date validation messages
    DATE_RANGE_INVALID = "End date must be after start date"
    DATE_RANGE_TOO_LONG = "Date range cannot exceed 365 days"
    
    # Item validation messages
    ITEMS_EMPTY = "Items cannot be empty"
    ITEM_NAME_EMPTY = "Item name cannot be empty"
    ITEM_PRICE_POSITIVE = "Item price must be greater than 0"
    
    # Calculation validation messages
    TOTAL_MISMATCH = "Total amount does not match the calculated total"
    SUBTOTAL_MISMATCH = "Subtotal does not match the sum of item prices"
    
    # Gateway validation messages
    GATEWAY_ID_EMPTY = "Gateway transaction ID cannot be empty"
    
    # Refund validation messages
    REFUND_REASON_EMPTY = "Refund reason cannot be empty"
    REFUND_AMOUNT_POSITIVE = "Refund amount must be greater than 0"


# Example usage functions for documentation
def get_example_transaction_request() -> Dict[str, Any]:
    """
    Get a complete example transaction request.
    Useful for testing and documentation.
    """
    return ModelConfigs.transaction_create_config()["json_schema_extra"]["examples"][0]


def get_example_hotel_booking() -> Dict[str, Any]:
    """
    Get a complete example hotel booking request.
    Useful for testing hotel-specific functionality.
    """
    return ModelConfigs.transaction_create_config()["json_schema_extra"]["examples"][1]


def get_example_ferry_booking() -> Dict[str, Any]:
    """
    Get a complete example ferry booking request.
    Useful for testing ferry-specific functionality.
    """
    return ModelConfigs.transaction_create_config()["json_schema_extra"]["examples"][2]
