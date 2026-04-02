"""
Network Segment Pydantic Schemas
定义网段相关的请求和响应数据模式
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.utils.ip_utils import validate_cidr


class NetworkSegmentBase(BaseModel):
    """网段基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="网段名称")
    company: Optional[str] = Field(None, max_length=100, description="所属公司")
    network: str = Field(..., description="网络地址 (如 192.168.1.0)")
    prefix_length: int = Field(..., ge=8, le=30, description="前缀长度 (如 24)")
    gateway: Optional[str] = Field(None, description="网关地址")
    description: Optional[str] = Field(None, description="描述")
    usage_threshold: int = Field(80, ge=0, le=100, description="使用率告警阈值（百分比）")
    
    @field_validator('network', 'gateway')
    @classmethod
    def validate_ip_format(cls, v):
        """验证 IP 地址格式"""
        if v is None:
            return v
        
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f'Invalid IP address format')
        return v


class NetworkSegmentCreate(NetworkSegmentBase):
    """创建网段的请求模式"""
    
    @field_validator('prefix_length')
    @classmethod
    def validate_cidr_format(cls, v, info):
        """验证 CIDR 格式的完整性"""
        # 当两个字段都存在时，验证 CIDR 格式
        if 'network' in info.data:
            cidr = f"{info.data['network']}/{v}"
            is_valid, error_msg, _ = validate_cidr(cidr)
            if not is_valid:
                raise ValueError(error_msg)
        return v


class NetworkSegmentUpdate(BaseModel):
    """更新网段的请求模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="网段名称")
    company: Optional[str] = Field(None, max_length=100, description="所属公司")
    gateway: Optional[str] = Field(None, description="网关地址")
    description: Optional[str] = Field(None, description="描述")
    usage_threshold: Optional[int] = Field(None, ge=0, le=100, description="使用率告警阈值（百分比）")
    
    @field_validator('gateway')
    @classmethod
    def validate_gateway_format(cls, v):
        """验证网关地址格式"""
        if v is None:
            return v
        
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid gateway IP address format')
        return v


class NetworkSegmentResponse(NetworkSegmentBase):
    """网段响应模式"""
    id: int = Field(..., description="网段 ID")
    created_by: int = Field(..., description="创建人 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class NetworkSegmentWithStats(NetworkSegmentResponse):
    """带统计信息的网段响应模式"""
    total_ips: int = Field(..., description="总 IP 数量")
    used_ips: int = Field(..., description="已用 IP 数量")
    available_ips: int = Field(..., description="可用 IP 数量")
    reserved_ips: int = Field(..., description="保留 IP 数量")
    usage_rate: float = Field(..., description="使用率（百分比）")


class NetworkSegmentStatsResponse(BaseModel):
    """网段统计信息响应模式"""
    segment_id: int = Field(..., description="网段 ID")
    total_ips: int = Field(..., description="总 IP 数量")
    used_ips: int = Field(..., description="已用 IP 数量")
    available_ips: int = Field(..., description="可用 IP 数量")
    reserved_ips: int = Field(..., description="保留 IP 数量")
    online_ips: int = Field(..., description="在线 IP 数量")
    offline_ips: int = Field(..., description="离线 IP 数量")
    usage_rate: float = Field(..., description="使用率（百分比）")
    network_info: dict = Field(..., description="网段范围信息")


class NetworkSegmentListQuery(BaseModel):
    """网段列表查询参数"""
    name: Optional[str] = Field(None, description="按名称模糊搜索")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序顺序: asc/desc")
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        """验证排序顺序"""
        if v not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v
