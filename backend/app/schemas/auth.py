"""
Authentication Pydantic Schemas
定义认证相关的请求和响应数据模式
"""
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """用户登录请求模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应模式"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌过期时间（秒）")
    user: Optional[UserResponse] = Field(None, description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求模式"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenPayload(BaseModel):
    """Token 载荷模式"""
    sub: Optional[int] = Field(None, description="用户 ID")
    role: Optional[str] = Field(None, description="用户角色")
    exp: Optional[int] = Field(None, description="过期时间戳")
    type: Optional[str] = Field(None, description="令牌类型")
