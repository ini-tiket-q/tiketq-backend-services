from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserCreate):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
