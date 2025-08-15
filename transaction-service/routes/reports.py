from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import logging

from domain.models import (
    TransactionReportRequest, TransactionReportResponse,
    RevenueReportRequest, RevenueReportResponse,
    RefundReportRequest, RefundReportResponse,
    ReportDateRange
)
from domain.services import get_reports_service, ReportsService, require_admin

# Create router
router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)

@router.get("/transactions", 
    response_model=TransactionReportResponse,
    summary="Generate transaction report",
    description="Generate detailed transaction report with filtering options. Admin access required.",
    responses={
        200: {"description": "Transaction report generated successfully"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        422: {"description": "Validation error"}
    },
    tags=["Reports"]
)
async def get_transaction_report(
    start_date: str = Query(..., description="Report start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Report end date (YYYY-MM-DD)"),
    status_filter: Optional[str] = Query(None, description="Filter by transaction status"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    min_amount: Optional[float] = Query(None, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(None, description="Maximum transaction amount"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    payment_gateway: Optional[str] = Query(None, description="Filter by payment gateway"),
    admin_user=Depends(require_admin),
    reports_service: ReportsService = Depends(get_reports_service)
) -> TransactionReportResponse:
    """
    Generate transaction report with filtering options.
    
    **Required Parameters:**
    - **date_range**: Start and end dates for the report (max 365 days)
    
    **Optional Filters:**
    - **status_filter**: Filter by transaction status
    - **transaction_type_filter**: Filter by transaction type
    - **min_amount** / **max_amount**: Amount range filter
    - **user_id**: Filter by specific user
    - **currency**: Currency filter (default: IDR)
    
    **Returns:**
    - Summary statistics (total count, amount, breakdowns)
    - Detailed transaction list
    - Report metadata
    
    **Admin access required.**
    """
    try:
        # Build request object from query parameters
        date_range = ReportDateRange(start_date=start_date, end_date=end_date)
        report_request = TransactionReportRequest(
            date_range=date_range,
            status_filter=status_filter,
            transaction_type=transaction_type,
            min_amount=min_amount,
            max_amount=max_amount,
            payment_method=payment_method,
            payment_gateway=payment_gateway
        )
        
        logger.info(f"Generating transaction report for date range: {start_date} to {end_date}")
        
        # Generate report using service layer validation
        report = reports_service.generate_transaction_report(report_request)
        
        logger.info(f"Transaction report generated successfully with {report.total_count} transactions")
        return report
        
    except ValueError as e:
        logger.error(f"Validation error in transaction report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error generating transaction report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate transaction report"
        )


@router.get("/revenue", 
    response_model=RevenueReportResponse,
    summary="Generate revenue analytics report",
    description="Generate revenue analytics with time-series data. Admin access required.",
    responses={
        200: {"description": "Revenue report generated successfully"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        422: {"description": "Validation error"}
    },
    tags=["Reports"]
)
async def get_revenue_report(
    start_date: str = Query(..., description="Report start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Report end date (YYYY-MM-DD)"),
    group_by: Optional[str] = Query("day", description="Time grouping (day/week/month)"),
    currency: Optional[str] = Query("IDR", description="Currency filter"),
    service_type_filter: Optional[str] = Query(None, description="Filter by service type"),
    include_refunds: Optional[bool] = Query(True, description="Include refunds in calculation"),
    admin_user=Depends(require_admin),
    reports_service: ReportsService = Depends(get_reports_service)
) -> RevenueReportResponse:
    """
    Generate revenue analytics report with time-series data.
    
    **Required Parameters:**
    - **date_range**: Start and end dates for the report (max 365 days)
    
    **Optional Parameters:**
    - **group_by**: Time grouping (day/week/month) - default: day
    - **currency**: Currency filter (default: IDR)
    - **service_type_filter**: Filter by service types
    - **include_refunds**: Include refunds in calculation (default: true)
    
    **Returns:**
    - Revenue summary statistics
    - Time-series revenue data points
    - Transaction counts and refund information
    
    **Admin access required.**
    """
    try:
        # Build request object from query parameters
        date_range = ReportDateRange(start_date=start_date, end_date=end_date)
        report_request = RevenueReportRequest(
            date_range=date_range,
            group_by=group_by,
            currency=currency,
            service_type_filter=service_type_filter,
            include_refunds=include_refunds
        )
        
        logger.info(f"Generating revenue report for date range: {start_date} to {end_date}")
        
        # Generate report using service layer validation
        report = reports_service.generate_revenue_report(report_request)
        
        logger.info(f"Revenue report generated successfully with total revenue: {report.total_revenue}")
        return report
        
    except ValueError as e:
        logger.error(f"Validation error in revenue report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error generating revenue report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate revenue report"
        )


@router.get("/refunds", 
    response_model=RefundReportResponse,
    summary="Generate refund report",
    description="Generate detailed refund report with filtering options. Admin access required.",
    responses={
        200: {"description": "Refund report generated successfully"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        422: {"description": "Validation error"}
    },
    tags=["Reports"]
)
async def get_refund_report(
    start_date: str = Query(..., description="Report start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Report end date (YYYY-MM-DD)"),
    status_filter: Optional[str] = Query(None, description="Filter by refund status"),
    min_amount: Optional[float] = Query(None, description="Minimum refund amount"),
    max_amount: Optional[float] = Query(None, description="Maximum refund amount"),
    reason_filter: Optional[str] = Query(None, description="Filter by refund reason keyword"),
    processed_by: Optional[int] = Query(None, description="Filter by admin who processed refund"),
    admin_user=Depends(require_admin),
    reports_service: ReportsService = Depends(get_reports_service)
) -> RefundReportResponse:
    """
    Generate refund report with filtering options.
    
    **Required Parameters:**
    - **date_range**: Start and end dates for the report (max 365 days)
    
    **Optional Filters:**
    - **status_filter**: Filter by refund status
    - **min_amount** / **max_amount**: Amount range filter
    - **reason_filter**: Filter by refund reason keyword
    - **processed_by**: Filter by admin who processed refund
    
    **Returns:**
    - Refund summary statistics
    - Detailed refund list
    - Status and reason breakdowns
    
    **Admin access required.**
    """
    try:
        # Build request object from query parameters
        date_range = ReportDateRange(start_date=start_date, end_date=end_date)
        report_request = RefundReportRequest(
            date_range=date_range,
            status_filter=status_filter,
            min_amount=min_amount,
            max_amount=max_amount,
            reason_filter=reason_filter,
            processed_by=processed_by
        )
        
        logger.info(f"Generating refund report for date range: {start_date} to {end_date}")
        
        # Generate report using service layer validation
        report = reports_service.generate_refund_report(report_request)
        
        logger.info(f"Refund report generated successfully with {report.total_count} refunds")
        return report
        
    except ValueError as e:
        logger.error(f"Validation error in refund report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error generating refund report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate refund report"
        )