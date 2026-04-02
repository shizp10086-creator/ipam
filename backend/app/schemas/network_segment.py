"""
网段 Pydantic Schema - 扩展版。

新增：cidr 字段、parent_id 子网嵌套、group_id 分组、tags 标签、
多级告警阈值、tenant_id、自定义字段、强制删除参数。
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.utils.ip_utils import validate_cidr


class NetworkSegmentCreate(BaseModel):
    """创建网段请求"""
    name: str = Field(..., min_length=1, max_length=100, description="网段名称")
    cidr: str = Field(..., description="CIDR 表示法（如 192.168.1.0/24）")
    gateway: Optional[str] = Field(None, description="网关地址")
    description: Optional[str] = Field(None, description="描述")
    company: Optional[str] = Field(None, max_length=100, description="所属公司")
    business_group: Optional[str] = Field(None, max_length=200, description="所属业务组")
    parent_id: Optional[int] = Field(None, description="父网段ID（子网嵌套）")
    group_id: Optional[int] = Field(None, description="所属分组ID")
    tags: Optional[list[str]] = Field(default=[], description="标签列表")
    custom_fields: Optional[dict] = Field(default={}, description="自定义字段")
    alert_threshold_warning: int = Field(80, ge=0, le=100, description="警告阈值")
    alert_threshold_critical: int = Field(90, ge=0, le=100, description="严重阈值")

    @field_validator("cidr")
    @classmethod
    def validate_cidr_format(cls, v):
        is_valid, error_msg, _ = validate_cidr(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

    @field_validator("gateway")
    @classmethod
    def validate_gateway(cls, v):
        if v is None:
            return v
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("网关地址格式无效")
        return v


class NetworkSegmentUpdate(BaseModel):
    """更新网段请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    gateway: Optional[str] = None
    description: Optional[str] = None
    company: Optional[str] = None
    business_group: Optional[str] = None
    group_id: Optional[int] = None
    tags: Optional[list[str]] = None
    custom_fields: Optional[dict] = None
    alert_threshold_warning: Optional[int] = Field(None, ge=0, le=100)
    alert_threshold_critical: Optional[int] = Field(None, ge=0, le=100)
    version: int = Field(..., description="当前版本号（乐观锁）")

    @field_validator("gateway")
    @classmethod
    def validate_gateway(cls, v):
        if v is None:
            return v
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("网关地址格式无效")
        return v


class NetworkSegmentResponse(BaseModel):
    """网段响应"""
    id: int
    tenant_id: int = 1
    name: str
    cidr: Optional[str] = None
    network: str
    broadcast: Optional[str] = None
    prefix_length: int
    ip_version: int = 4
    gateway: Optional[str] = None
    description: Optional[str] = None
    company: Optional[str] = None
    business_group: Optional[str] = None
    parent_id: Optional[int] = None
    group_id: Optional[int] = None
    tags: Optional[list] = []
    custom_fields: Optional[dict] = {}
    total_ips: int = 0
    used_ips: int = 0
    reserved_ips: int = 0
    temporary_ips: int = 0
    usage_rate: float = 0.0
    alert_threshold_warning: int = 80
    alert_threshold_critical: int = 90
    status: str = "active"
    version: int = 1
    usage_threshold: int = 80
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NetworkSegmentWithStats(NetworkSegmentResponse):
    """带统计信息的网段响应"""
    available_ips: int = 0
    online_ips: int = 0
    offline_ips: int = 0
    children_count: int = 0


class NetworkSegmentStatsResponse(BaseModel):
    """网段统计信息"""
    segment_id: int
    total_ips: int = 0
    used_ips: int = 0
    available_ips: int = 0
    reserved_ips: int = 0
    online_ips: int = 0
    offline_ips: int = 0
    usage_rate: float = 0.0
    network_info: dict = {}


class SegmentGroupCreate(BaseModel):
    """创建网段分组"""
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0


class SegmentGroupResponse(BaseModel):
    """网段分组响应"""
    id: int
    tenant_id: int
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
