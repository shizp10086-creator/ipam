"""
Operation Log Schemas
操作日志的 Pydantic 数据模式
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OperationLogResponse(BaseModel):
    """
    操作日志响应模式
    """
    id: int
    user_id: int
    username: str
    operation_type: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True


class OperationLogListQuery(BaseModel):
    """
    操作日志列表查询参数
    """
    user_id: Optional[int] = Field(None, description="按操作人 ID 筛选")
    username: Optional[str] = Field(None, description="按操作人用户名筛选")
    operation_type: Optional[str] = Field(None, description="按操作类型筛选")
    resource_type: Optional[str] = Field(None, description="按资源类型筛选")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
