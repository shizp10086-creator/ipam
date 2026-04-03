"""
User Pydantic Schemas
定义用户相关的请求和响应数据模式
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: str = Field(..., min_length=1, max_length=100, description="全名")
    role: str = Field(..., description="角色: admin/user/readonly")
    is_active: bool = Field(True, description="是否激活")

    @validator('role')
    def validate_role(cls, v):
        """验证角色值"""
        valid_roles = ['admin', 'user', 'readonly']
        if v not in valid_roles:
            raise ValueError(f"角色必须是以下之一: {', '.join(valid_roles)}")
        return v


class UserCreate(UserBase):
    """创建用户的请求模式"""
    password: str = Field(..., min_length=6, max_length=100, description="密码（至少6个字符）")

    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError("密码长度至少为6个字符")
        return v


class UserUpdate(BaseModel):
    """更新用户的请求模式"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="全名")
    role: Optional[str] = Field(None, description="角色: admin/user/readonly")
    is_active: Optional[bool] = Field(None, description="是否激活")

    @validator('role')
    def validate_role(cls, v):
        """验证角色值"""
        if v is not None:
            valid_roles = ['admin', 'user', 'readonly']
            if v not in valid_roles:
                raise ValueError(f"角色必须是以下之一: {', '.join(valid_roles)}")
        return v


class UserResponse(BaseModel):
    """用户响应模式"""
    id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: str = Field(..., description="全名")
    role: str = Field(..., description="角色")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class UserListQuery(BaseModel):
    """用户列表查询参数"""
    keyword: Optional[str] = Field(None, description="搜索关键词（在用户名、邮箱、全名中搜索）")
    role: Optional[str] = Field(None, description="按角色筛选")
    is_active: Optional[bool] = Field(None, description="按激活状态筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class PasswordChangeRequest(BaseModel):
    """修改密码的请求模式"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码（至少6个字符）")

    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        if len(v) < 6:
            raise ValueError("新密码长度至少为6个字符")
        return v
