"""
Authentication API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserResponse
from app.api.deps import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    token_data = {"sub": user.id, "role": user.role, "username": user.username}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    user_response = UserResponse(id=user.id, username=user.username, email=user.email, full_name=user.full_name, role=user.role, is_active=user.is_active, created_at=user.created_at, updated_at=user.updated_at)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, user=user_response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = verify_token(refresh_data.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token", headers={"WWW-Authenticate": "Bearer"})
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format", headers={"WWW-Authenticate": "Bearer"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    token_data = {"sub": user.id, "role": user.role, "username": user.username}
    access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    return {"code": 200, "message": "Logged out successfully", "data": {"username": current_user.username}}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user