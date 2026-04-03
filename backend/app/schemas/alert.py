"""
Alert Schemas
告警相关的 Pydantic 数据模式
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AlertBase(BaseModel):
    """告警基础模式"""
    segment_id: int = Field(..., description="网段 ID")
    alert_type: str = Field(..., description="告警类型")
    severity: str = Field(..., description="严重程度: warning/critical")
    message: str = Field(..., description="告警消息")
    current_usage: float = Field(..., description="当前使用率")
    threshold: float = Field(..., description="阈值")


class AlertResponse(AlertBase):
    """告警响应模式"""
    id: int
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """告警列表响应模式"""
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AlertResolveRequest(BaseModel):
    """手动解决告警请求模式"""
    pass  # 不需要额外参数，只需要 alert_id


class UsageStatsResponse(BaseModel):
    """网段使用率统计响应模式"""
    segment_id: int
    segment_name: str
    total_ips: int
    used_ips: int
    available_ips: int
    reserved_ips: int
    usage_rate: float
    threshold: int


class MonitorResultResponse(BaseModel):
    """监控结果响应模式"""
    total_segments: int
    alerts_created: int
    alerts_resolved: int
    segments_checked: list[dict]
