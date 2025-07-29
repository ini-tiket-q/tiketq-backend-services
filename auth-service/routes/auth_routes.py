from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from domain.services import register_user, login_user, verify_token
from domain.models import Token, UserCreate

router = APIRouter()

@router.post("/register", response_model=Token)
def register(user_data: UserCreate):
    return register_user(user_data)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return login_user(form_data.username, form_data.password)

@router.post("/verify-token")
def verify(payload: dict):
    token = payload.get("token")
    if not token or not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"valid": True}
