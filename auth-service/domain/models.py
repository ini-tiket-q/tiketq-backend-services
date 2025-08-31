from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER

class UserInDB(UserCreate):
    hashed_password: str
    id: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None

class UserResponse(BaseModel):
    id: int
    email: str
    role: UserRole
