from fastapi import APIRouter, Depends, HTTPException, status
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
    require_user_or_admin
)

router = APIRouter(tags=["orders"])

def get_order_service(db: Session = Depends(get_database_session)) -> OrderService:
    """Dependency injection for OrderService"""
    return create_order_service(db)

# Order Endpoints based on documentation
@router.post(
    "/orders/", 
    response_model=OrderInDB,
    status_code=status.HTTP_201_CREATED
)
async def create_order(
    order_request: OrderCreateRequest,
    current_user: dict = Depends(require_user_or_admin),
    service: OrderService = Depends(get_order_service)
):
    """Create a new order - USER/ADMIN access"""
    try:
        # Create order using validated request model
        order = service.create_order(order_request, current_user["id"])
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order"
            )
            
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order {str(e)}"
        )

@router.get(
    "/orders/", 
    response_model=List[OrderInDB]
)
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[OrderStatus] = None,
    current_user: dict = Depends(require_user_or_admin),
    service: OrderService = Depends(get_order_service)
):
    """List orders for the current user - USER/ADMIN access"""
    try:
        if current_user["role"] == "admin":
            # Admin can see all orders
            orders = service.get_orders(
                skip=skip, 
                limit=limit,
                status=status_filter
            )
        else:
            # Regular users can only see their own orders
            orders = service.get_orders_by_user(
                user_id=current_user["id"],
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
    response_model=OrderInDB
)
async def get_order(
    order_id: int,
    current_user: dict = Depends(require_user_or_admin),
    service: OrderService = Depends(get_order_service)
):
    """Get order details by ID - USER/ADMIN access"""
    try:
        order = service.get_order(
            order_id=order_id,
            user_id=current_user["id"]
        )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check access rights - users can only see their own orders
        if current_user["role"] != "admin" and order.user_id != current_user["id"]:
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

@router.put(
    "/orders/{order_id}/status", 
    response_model=OrderInDB
)
async def update_order_status(
    order_id: int,
    status_request: OrderStatusUpdateRequest,
    current_user: dict = Depends(require_user_or_admin),
    service: OrderService = Depends(get_order_service)
):
    """Update order status - ADMIN access only"""
    try:
        # Admin access already checked by require_admin decorator
        
        # Check if order exists
        existing_order = service.get_order(
            order_id=order_id,
            user_id=current_user["id"]  # Admin can access any order
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
            user_id=current_user["id"]
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
