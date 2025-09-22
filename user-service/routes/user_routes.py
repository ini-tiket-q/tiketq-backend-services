from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def list_users():
    """List all users (placeholder)"""
    return {"message": "Users endpoint", "users": []}

@router.get("/{user_id}")
async def get_user(user_id: int):
    """Get user by ID (placeholder)"""
    return {"message": f"User {user_id}", "user_id": user_id}

@router.post("/")
async def create_user():
    """Create user (placeholder)"""
    return {"message": "User created"}

@router.put("/{user_id}")
async def update_user(user_id: int):
    """Update user (placeholder)"""
    return {"message": f"User {user_id} updated"}

@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """Delete user (placeholder)"""
    return {"message": f"User {user_id} deleted"}
