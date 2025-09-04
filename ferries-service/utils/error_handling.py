from fastapi import HTTPException
from functools import wraps
import logging
from requests.exceptions import RequestException

# Set up logging
logger = logging.getLogger(__name__)

class SindoAPIError(Exception):
    """Custom exception for Sindo API errors"""
    pass

def handle_sync_api_errors(endpoint_name: str = "API endpoint"):
    """
    Decorator to handle errors for synchronous API endpoints.
    
    Args:
        endpoint_name (str): Descriptive name of the endpoint for error messages
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions (they're intentional)
                raise
            except RequestException as e:
                # Handle API request errors specifically
                logger.error(f"Network error in {endpoint_name}: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=503,
                    detail=f"Service temporarily unavailable. Please try again later."
                )
            except ValueError as e:
                # Handle data validation errors
                logger.error(f"Data validation error in {endpoint_name}: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid request data: {str(e)}"
                )
            except SindoAPIError as e:
                # Handle Sindo API errors specifically
                logger.error(f"Sindo API error in {endpoint_name}: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=502,
                    detail=f"Error communicating with ferry service provider: {str(e)}"
                )
            except Exception as e:
                # Handle all other errors
                logger.error(f"Unexpected error in {endpoint_name}: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected error processing your request. Please try again later."
                )
        return wrapper
    return decorator