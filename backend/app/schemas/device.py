"""
Device Pydantic Schemas
定义设备相关的请求和响应数据模式
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.utils.device_utils import validate_mac_address, normalize_mac_address


class DeviceBase(BaseModel):
    """设备基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="设备名称")
    mac_address: str = Field(..., description="MAC 地址")
    device_type: Optional[str] = Field(None, max_length=50, description="设备类型（服务器/交换机/路由器/终端等）")
    manufacturer: Optional[str] = Field(None, max_length=100, description="制造商")
    model: Optional[str] = Field(None, max_length=100, description="型号")
    owner: str = Field(..., min_length=1, max_length=100, description="责任人")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    location: Optional[str] = Field(None, max_length=200, description="物理位置")
    description: Optional[str] = Field(None, description="描述")
    
    @validator('mac_address')
    def validate_mac(cls, v):
        """验证 MAC 地址格式"""
        is_valid, error = validate_mac_address(v)
        if not is_valid:
            raise ValueError(error)
        # 标准化 MAC 地址格式
        return normalize_mac_address(v)


class DeviceCreate(DeviceBase):
    """创建设备的请求模式"""
    pass


class DeviceUpdate(BaseModel):
    """更新设备的请求模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="设备名称")
    mac_address: Optional[str] = Field(None, description="MAC 地址")
    device_type: Optional[str] = Field(None, max_length=50, description="设备类型")
    manufacturer: Optional[str] = Field(None, max_length=100, description="制造商")
    model: Optional[str] = Field(None, max_length=100, description="型号")
    owner: Optional[str] = Field(None, min_length=1, max_length=100, description="责任人")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    location: Optional[str] = Field(None, max_length=200, description="物理位置")
    description: Optional[str] = Field(None, description="描述")
    
    @validator('mac_address')
    def validate_mac(cls, v):
        """验证 MAC 地址格式"""
        if v is not None:
            is_valid, error = validate_mac_address(v)
            if not is_valid:
                raise ValueError(error)
            # 标准化 MAC 地址格式
            return normalize_mac_address(v)
        return v


class DeviceResponse(DeviceBase):
    """设备响应模式"""
    id: int = Field(..., description="设备 ID")
    created_by: int = Field(..., description="创建人 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceListQuery(BaseModel):
    """设备列表查询参数"""
    keyword: Optional[str] = Field(None, description="搜索关键词（在名称、MAC、责任人中搜索）")
    device_type: Optional[str] = Field(None, description="按设备类型筛选")
    owner: Optional[str] = Field(None, description="按责任人筛选")
    department: Optional[str] = Field(None, description="按部门筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class DeviceWithIPsResponse(DeviceResponse):
    """设备及其关联 IP 的响应模式"""
    ip_addresses: list = Field(default=[], description="关联的 IP 地址列表")
    
    class Config:
        from_attributes = True
