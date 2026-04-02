"""
租户 Pydantic Schema。
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    """创建租户请求"""
    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    code: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$", description="租户编码")
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    config: Optional[dict] = None


class TenantUpdate(BaseModel):
    """更新租户请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(active|disabled)$")
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    config: Optional[dict] = None


class TenantResponse(BaseModel):
    """租户响应"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    status: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    config: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
