from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
from sqlalchemy.orm import Session

from domain.models import (
    OrderInDB, OrderStatus,
    OrderCreateRequest, OrderStatusUpdateRequest
)
from domain.services import (
    OrderService,
    get_database_session,
    create_order_service,
    require_admin,
    require_user_or_admin
)

router = APIRouter(tags=["orders"])

def get_order_service(db: Session = Depends(get_database_session)) -> OrderService:
    """Dependency injection for OrderService"""
    return create_order_service(db)

# Order Endpoints based on documentation

@router.get(
    "/orders/", 
    response_model=List[OrderInDB],
    summary="List orders",
    description="""
    Retrieve a list of orders based on filters.
    
    ### Access Level: User/Admin
    - Requires authentication
    - Users can only see their own orders
    - Admins can see all orders
    
    ### Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (pagination)
    - status_filter: Optional filter by order status
    """
)
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[OrderStatus] = None,
    current_user = Depends(require_user_or_admin),
    service: OrderService = Depends(get_order_service)
):
    """List orders for the current user - USER/ADMIN access"""
    try:
        if current_user.role == "admin":
            # Admin can see all orders
            orders = service.get_orders(
                skip=skip, 
                limit=limit,
                status=status_filter
            )
        else:
            # Regular users can only see their own orders
            orders = service.get_orders_by_user(
                email=current_user.email,
                status=status_filter,
                skip=skip,
                limit=limit
            )
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve orders {str(e)}"
        )

@router.get(
    "/orders/{order_id}", 
    response_model=OrderInDB,
    summary="Get order by ID",
    description="""
    Retrieve details of a specific order by its ID.
    
    ### Access Level: User/Admin
    - Requires authentication
    - Users can only view their own orders
    - Admins can view any order
    """
)
async def get_order(
    order_id: int,
    current_user = Depends(require_user_or_admin),
    service: OrderService = Depends(get_order_service)
):
    """Get order details by ID - USER/ADMIN access"""
    try:
        order = service.get_order(
            order_id=order_id,
            email=current_user.email
        )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check access rights - users can only see their own orders
        if current_user.role != "admin" and order.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this order"
            )
            
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order {str(e)}"
        )

@router.get(
    "/orders/public/{order_number}", 
    response_model=OrderInDB,
    summary="Get order by order number (public)",
    description="""
    Retrieve order details by order number.
    
    ### Access Level: Public
    - No authentication required
    - Limited information may be shown for public access
    """
)
async def get_order_by_number(
    order_number: str,
    service: OrderService = Depends(get_order_service),
):
    """Get order details by order number - public access"""
    try:
        order = service.get_order_by_number(order_number=order_number)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        return order

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order {str(e)}",
        )

@router.put(
    "/orders/{order_id}/status", 
    response_model=OrderInDB,
    summary="Update order status",
    description="""
    Update the status of an existing order.
    
    ### Access Level: Admin Only
    - Requires admin privileges
    - Used for order status management
    """
)
async def update_order_status(
    order_id: int,
    status_request: OrderStatusUpdateRequest,
    current_user = Depends(require_admin),
    service: OrderService = Depends(get_order_service)
):
    """Update order status - ADMIN access only"""
    try:
        # Admin access already checked by require_admin decorator
        
        # Check if order exists
        existing_order = service.get_order(
            order_id=order_id,
            email=current_user.email  # Admin can access any order
        )
        
        if not existing_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Update order status using validated request model
        updated_order = service.update_order_status(
            order_id=order_id,
            status_request=status_request,
            email=current_user.email
        )
        
        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update order status"
            )
            
        return updated_order
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order status {str(e)}"
        )
