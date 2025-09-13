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
     
            
# def validate_dates(depart_date: Union[str, date], return_date: Optional[Union[str, date]] = None) -> None:
#     """
#     Validate that dates are in the correct order.
#     This version accepts both strings (YYYY-MM-DD) and date objects.
#     """
#     # Convert to date objects if they're strings
#     if isinstance(depart_date, str):
#         depart_date = datetime.strptime(depart_date, "%Y-%m-%d").date()
    
#     if return_date and isinstance(return_date, str):
#         return_date = datetime.strptime(return_date, "%Y-%m-%d").date()
    
#     today = date.today()
    
#     if depart_date < today:
#         raise ValueError("Departure date cannot be in the past")
    
#     if return_date and return_date < depart_date:
#         raise ValueError("Return date cannot be before departure date")