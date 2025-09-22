class MidtransException(Exception):
    """Base exception for all Midtrans operations"""
    pass


class MidtransAPIException(MidtransException):
    """Exception for Midtrans API errors"""

    def __init__(self, status_code: int, message: str, error_detail: str = None):
        self.status_code = status_code
        self.message = message
        self.error_detail = error_detail
        super().__init__(f"Midtrans API error {status_code}: {message}")


class MidtransValidationException(MidtransException):
    """Exception for validation errors"""
    pass


class MidtransNetworkException(MidtransException):
    """Exception for network-related errors"""
    pass


class MidtransTransactionException(MidtransException):
    """Exception for transaction-specific errors"""
    pass