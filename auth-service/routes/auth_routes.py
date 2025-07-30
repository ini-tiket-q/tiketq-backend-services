from fastapi import APIRouter, HTTPException, status, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm
from domain.services import (
    register_user, 
    login_user, 
    verify_token, 
    decode_token,
    get_user_by_email,
    get_user_by_id,
    get_all_users,
    update_user_role
)
from domain.models import Token, UserCreate, UserResponse, UserRole, TokenData
from typing import Optional

router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)) -> TokenData:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_user_or_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    if current_user.role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User or admin access required"
        )
    return current_user

@router.post("/register", 
    response_model=Token,
    summary="Register a new user",
    description="Register a new user with email, password, and optional role. Default role is 'user'.",
    responses={
        200: {"description": "User registered successfully"},
        400: {"description": "User already exists or invalid data"},
        422: {"description": "Validation error"}
    },
    tags=["Authentication"]
)
def register(user_data: UserCreate):
    """
    Register a new user account.
    
    - **email**: User's email address (must be unique)
    - **password**: User's password (will be hashed)
    - **role**: User's role (optional, defaults to 'user')
    
    Returns a JWT token for authentication.
    """
    try:
        return register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", 
    response_model=Token,
    summary="Login user",
    description="Authenticate user with email and password to receive JWT token.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"}
    },
    tags=["Authentication"]
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with email and password.
    
    - **username**: User's email address
    - **password**: User's password
    
    Returns a JWT token for authentication.
    """
    try:
        return login_user(form_data.username, form_data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/verify-token",
    summary="Verify JWT token",
    description="Verify if a JWT token is valid and not expired.",
    responses={
        200: {"description": "Token is valid"},
        401: {"description": "Token is invalid or expired"}
    },
    tags=["Authentication"]
)
def verify(payload: dict):
    """
    Verify a JWT token.
    
    - **token**: JWT token to verify
    
    Returns validation result.
    """
    token = payload.get("token")
    if not token or not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"valid": True}

@router.get("/me", 
    response_model=UserResponse,
    summary="Get current user information",
    description="Get information about the currently authenticated user.",
    responses={
        200: {"description": "User information retrieved successfully"},
        401: {"description": "Invalid authentication credentials"},
        404: {"description": "User not found"}
    },
    tags=["Authentication"]
)
def get_current_user_info(current_user: TokenData = Depends(require_user_or_admin)):
    """
    Get current user information.
    
    Requires authentication. Returns user details including role.
    """
    user = get_user_by_email(current_user.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.get("/users", 
    response_model=list[UserResponse],
    summary="List all users",
    description="Get a list of all users in the system. Admin access required.",
    responses={
        200: {"description": "List of users retrieved successfully"},
        401: {"description": "Invalid authentication credentials"},
        403: {"description": "Admin access required"}
    },
    tags=["User Management"]
)
def list_all_users(current_user: TokenData = Depends(require_admin)):
    """
    List all users in the system.
    
    Admin access required. Returns list of all users with their roles.
    """
    return get_all_users()

@router.get("/users/{user_id}", 
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get information about a specific user by their ID. Admin access required.",
    responses={
        200: {"description": "User information retrieved successfully"},
        401: {"description": "Invalid authentication credentials"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"}
    },
    tags=["User Management"]
)
def get_user(user_id: int, current_user: TokenData = Depends(require_admin)):
    """
    Get user information by ID.
    
    - **user_id**: ID of the user to retrieve
    
    Admin access required.
    """
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/users/{user_id}/role", 
    response_model=UserResponse,
    summary="Update user role",
    description="Update the role of a specific user. Admin access required.",
    responses={
        200: {"description": "User role updated successfully"},
        401: {"description": "Invalid authentication credentials"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"},
        422: {"description": "Invalid role value"}
    },
    tags=["User Management"]
)
def update_role(user_id: int, role: UserRole, current_user: TokenData = Depends(require_admin)):
    """
    Update user role.
    
    - **user_id**: ID of the user to update
    - **role**: New role for the user (user/admin)
    
    Admin access required.
    """
    updated_user = update_user_role(user_id, role)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user
