import os
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from domain.models import UserCreate, Token, UserInDB
from adapters.db import DBUserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
repo = DBUserRepository()

SECRET_KEY = os.getenv("JWT_SECRET", "secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def register_user(user: UserCreate) -> Token:
    if repo.get_user_by_email(user.email):
        raise ValueError("User already exists")

    hashed = hash_password(user.password)
    user_db = UserInDB(email=user.email, password=user.password, hashed_password=hashed)
    repo.create_user(user_db)
    token = create_token({"sub": user.email})
    return Token(access_token=token)

def login_user(email: str, password: str) -> Token:
    user = repo.get_user_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")

    token = create_token({"sub": user.email})
    return Token(access_token=token)

def verify_token(token: str) -> bool:
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except JWTError:
        return False
