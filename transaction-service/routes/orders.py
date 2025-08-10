from fastapi import APIRouter, Depends, HTTPException, status, Body, Header
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from domain.models import OrderInDB, OrderStatus
from domain.services import (
    OrderService,
    get_database_session,
    create_order_service
)

router = APIRouter(tags=["orders"])

def get_current_user(authorization: str = Header(None)):
    """Mock authentication - replace with real auth service integration"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # For now, return a mock user - this should integrate with auth service
    # The API Gateway should handle authentication and pass user info
    return {"id": 1, "role": "user", "email": "test@example.com"}

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
    order_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Create a new order - USER/ADMIN access"""
    try:
        # Note: For now this is a placeholder implementation
        # The actual order creation logic will depend on external services
        # (flights, hotels, ferries, PPOB) which are still under development
        
        # Basic validation
        required_fields = ["service_type", "items"]
        for field in required_fields:
            if field not in order_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Add user_id to order data
        order_data["user_id"] = current_user["id"]
        
        # Placeholder: Create order with basic validation
        # In production, this would integrate with booking services
        order = service.create_order(order_data, current_user["id"])
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order"
            )
            
        return order
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
            detail="Failed to create order"
        )

@router.get(
    "/orders/", 
    response_model=List[OrderInDB]
)
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[OrderStatus] = None,
    current_user: dict = Depends(get_current_user),
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
            detail="Failed to retrieve orders"
        )

@router.get(
    "/orders/{order_id}", 
    response_model=OrderInDB
)
async def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
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
            detail="Failed to retrieve order"
        )

@router.put(
    "/orders/{order_id}/status", 
    response_model=OrderInDB
)
async def update_order_status(
    order_id: int,
    status_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service)
):
    """Update order status - ADMIN access only"""
    try:
        # Check admin access
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for order status updates"
            )
        
        # Validate status field
        if "status" not in status_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status field is required"
            )
        
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
        
        # Update order status
        updated_order = service.update_order_status(
            order_id=order_id,
            order=status_data,
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
            detail="Failed to update order status"
        )
