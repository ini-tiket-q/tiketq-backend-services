from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_dates(date_input: str) -> str:
    """
    Convert date string to Sindo's required yyyyMMdd format.
    Raises ValueError for invalid dates.
    """
    if isinstance(date_input, datetime.date):
        return date_input  # Already a date object, return as-is
    
    if isinstance(date_input, str):
        try:
            # Parse string to date object
            return datetime.datetime.strptime(date_input, '%Y-%m-%d').date()
        except ValueError as e:
            logger.error(f"Error parsing date '{date_input}': {str(e)}")
            raise ValueError("Date must be in YYYY-MM-DD format")
    try:
        date_str = str(date_input)
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        raise ValueError("Invalid date format")