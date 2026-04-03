"""
IP Address Pydantic Schemas
定义 IP 地址相关的请求和响应数据模式
"""
from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional
from datetime import datetime
import ipaddress


class IPAddressBase(BaseModel):
    """IP 地址基础模式"""
    ip_address: str = Field(..., description="IP 地址")
    status: str = Field(default="available", description="状态: available/used/reserved")

    @validator('ip_address')
    def validate_ip(cls, v):
        """验证 IP 地址格式"""
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address format')
        return v

    @validator('status')
    def validate_status(cls, v):
        """验证状态值"""
        valid_statuses = ["available", "used", "reserved"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class IPAddressCreate(IPAddressBase):
    """创建 IP 地址的请求模式"""
    segment_id: int = Field(..., description="所属网段 ID")
    device_id: Optional[int] = Field(None, description="关联设备 ID")


class IPAddressUpdate(BaseModel):
    """更新 IP 地址的请求模式"""
    status: Optional[str] = Field(None, description="状态: available/used/reserved")
    device_id: Optional[int] = Field(None, description="关联设备 ID")

    @validator('status')
    def validate_status(cls, v):
        """验证状态值"""
        if v is not None:
            valid_statuses = ["available", "used", "reserved"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class IPAddressResponse(IPAddressBase):
    """IP 地址响应模式"""
    id: int = Field(..., description="IP 地址 ID")
    segment_id: int = Field(..., description="所属网段 ID")
    device_id: Optional[int] = Field(None, description="关联设备 ID")
    allocated_by: Optional[int] = Field(None, description="分配人 ID")
    allocated_at: Optional[datetime] = Field(None, description="分配时间")
    last_seen: Optional[datetime] = Field(None, description="最后扫描时间")
    is_online: bool = Field(default=False, description="是否在线")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 关联对象
    segment: Optional[dict] = Field(None, description="所属网段信息")
    device: Optional[dict] = Field(None, description="关联设备信息")

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """从 ORM 对象创建响应"""
        data = {
            "id": obj.id,
            "ip_address": obj.ip_address,
            "status": obj.status,
            "segment_id": obj.segment_id,
            "device_id": obj.device_id,
            "allocated_by": obj.allocated_by,
            "allocated_at": obj.allocated_at,
            "last_seen": obj.last_seen,
            "is_online": obj.is_online,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }

        # 添加关联的网段信息
        if hasattr(obj, 'segment') and obj.segment:
            data["segment"] = {
                "id": obj.segment.id,
                "name": obj.segment.name,
                "network": obj.segment.network,
                "prefix_length": obj.segment.prefix_length,
                "gateway": obj.segment.gateway,
            }

        # 添加关联的设备信息
        if hasattr(obj, 'device') and obj.device:
            data["device"] = {
                "id": obj.device.id,
                "name": obj.device.name,
                "mac_address": obj.device.mac_address,
                "device_type": obj.device.device_type,
                "manufacturer": obj.device.manufacturer,
                "model": obj.device.model,
                "owner": obj.device.owner,
                "department": obj.device.department,
                "location": obj.device.location,
            }

        return cls(**data)


class IPAllocateRequest(BaseModel):
    """IP 分配请求模式"""
    ip_address: str = Field(..., description="要分配的 IP 地址")
    device_id: int = Field(..., description="关联设备 ID")
    segment_id: Optional[int] = Field(None, description="所属网段 ID（可选，系统会自动查找）")

    @validator('ip_address')
    def validate_ip(cls, v):
        """验证 IP 地址格式"""
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address format')
        return v


class IPReleaseRequest(BaseModel):
    """IP 回收请求模式"""
    ip_address: Optional[str] = Field(None, description="要回收的 IP 地址")
    ip_id: Optional[int] = Field(None, description="要回收的 IP ID")

    @validator('ip_address')
    def validate_ip(cls, v):
        """验证 IP 地址格式"""
        if v is not None:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v

    def __init__(self, **data):
        super().__init__(**data)
        # 确保至少提供一个标识符
        if not self.ip_address and not self.ip_id:
            raise ValueError("Either ip_address or ip_id must be provided")


class IPReserveRequest(BaseModel):
    """IP 保留请求模式"""
    ip_address: Optional[str] = Field(None, description="要保留的 IP 地址")
    ip_id: Optional[int] = Field(None, description="要保留的 IP ID")
    reserve: bool = Field(True, description="True=保留, False=取消保留")

    @validator('ip_address')
    def validate_ip(cls, v):
        """验证 IP 地址格式"""
        if v is not None:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v

    def __init__(self, **data):
        super().__init__(**data)
        # 确保至少提供一个标识符
        if not self.ip_address and not self.ip_id:
            raise ValueError("Either ip_address or ip_id must be provided")


class IPBatchUpdateStatusRequest(BaseModel):
    """批量更新 IP 状态请求模式"""
    ip_ids: list[int] = Field(..., description="IP 地址 ID 列表")
    status: str = Field(..., description="目标状态: available/used/reserved")

    @validator('status')
    def validate_status(cls, v):
        """验证状态值"""
        valid_statuses = ["available", "used", "reserved"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @validator('ip_ids')
    def validate_ip_ids(cls, v):
        """验证 IP ID 列表"""
        if not v:
            raise ValueError("ip_ids cannot be empty")
        return v


class IPConflictCheckRequest(BaseModel):
    """IP 冲突检测请求模式"""
    ip_address: str = Field(..., description="要检查的 IP 地址")
    check_ping: bool = Field(True, description="是否执行 Ping 检测")
    check_arp: bool = Field(False, description="是否执行 ARP 检测")
    ping_timeout: int = Field(2, ge=1, le=10, description="Ping 超时时间（秒）")
    arp_timeout: int = Field(2, ge=1, le=10, description="ARP 超时时间（秒）")

    @validator('ip_address')
    def validate_ip(cls, v):
        """验证 IP 地址格式"""
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address format')
        return v


class IPConflictCheckResponse(BaseModel):
    """IP 冲突检测响应模式"""
    has_conflict: bool = Field(..., description="是否存在冲突")
    conflict_type: Optional[str] = Field(None, description="冲突类型 (logical/physical)")
    message: str = Field(..., description="检测结果消息")
    details: dict = Field(default_factory=dict, description="详细信息")


class IPListQuery(BaseModel):
    """IP 地址列表查询参数"""
    segment_id: Optional[int] = Field(None, description="按网段筛选")
    status: Optional[str] = Field(None, description="按状态筛选")
    device_id: Optional[int] = Field(None, description="按设备筛选")
    is_online: Optional[bool] = Field(None, description="按在线状态筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

    @validator('status')
    def validate_status(cls, v):
        """验证状态值"""
        if v is not None:
            valid_statuses = ["available", "used", "reserved"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v



class IPScanRequest(BaseModel):
    """IP 扫描请求模式"""
    segment_id: int = Field(..., description="要扫描的网段 ID")
    scan_type: str = Field("ping", description="扫描类型: ping/arp")
    timeout: int = Field(2, ge=1, le=10, description="超时时间（秒）")
    max_concurrent: int = Field(50, ge=1, le=200, description="最大并发数")

    @validator('scan_type')
    def validate_scan_type(cls, v):
        """验证扫描类型"""
        valid_types = ["ping", "arp"]
        if v not in valid_types:
            raise ValueError(f"Scan type must be one of: {', '.join(valid_types)}")
        return v


class IPScanProgressResponse(BaseModel):
    """IP 扫描进度响应模式"""
    total_ips: int = Field(..., description="总 IP 数量")
    scanned_ips: int = Field(..., description="已扫描 IP 数量")
    online_ips: int = Field(..., description="在线 IP 数量")
    offline_ips: int = Field(..., description="离线 IP 数量")
    progress_percentage: float = Field(..., description="进度百分比")
    elapsed_time: float = Field(..., description="已用时间（秒）")
    estimated_remaining_time: Optional[float] = Field(None, description="预计剩余时间（秒）")


class IPScanResultResponse(BaseModel):
    """IP 扫描结果响应模式"""
    scan_history_id: int = Field(..., description="扫描历史记录 ID")
    report: dict = Field(..., description="扫描报告")
    update_stats: dict = Field(..., description="更新统计信息")


class ScanHistoryResponse(BaseModel):
    """扫描历史响应模式"""
    id: int = Field(..., description="扫描历史 ID")
    segment_id: int = Field(..., description="网段 ID")
    scan_type: str = Field(..., description="扫描类型")
    total_ips: int = Field(..., description="扫描 IP 总数")
    online_ips: int = Field(..., description="在线 IP 数量")
    offline_ips: int = Field(..., description="离线 IP 数量")
    duration: float = Field(..., description="扫描耗时（秒）")
    created_by: int = Field(..., description="发起人 ID")
    created_at: datetime = Field(..., description="扫描时间")

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """从 ORM 对象创建响应"""
        offline_ips = obj.total_ips - obj.online_ips
        return cls(
            id=obj.id,
            segment_id=obj.segment_id,
            scan_type=obj.scan_type,
            total_ips=obj.total_ips,
            online_ips=obj.online_ips,
            offline_ips=offline_ips,
            duration=obj.duration,
            created_by=obj.created_by,
            created_at=obj.created_at
        )


# ==================== 扩展 Schema ====================

class IPAllocateRequestV2(BaseModel):
    """IP 分配请求 - 扩展版（支持自动分配和标签）"""
    segment_id: int = Field(..., description="所属网段 ID")
    ip_address: Optional[str] = Field(None, description="指定 IP 地址（不填则自动分配）")
    auto_allocate: bool = Field(False, description="是否自动分配（优先连续空闲 IP）")
    device_id: Optional[int] = Field(None, description="关联设备 ID")
    responsible_person: Optional[str] = Field(None, description="责任人")
    department: Optional[str] = Field(None, description="所属部门")
    reason: Optional[str] = Field(None, description="分配原因")
    dns_name: Optional[str] = Field(None, description="DNS 域名")
    tags: Optional[list[str]] = Field(default=[], description="标签列表")
    # 临时 IP
    is_temporary: bool = Field(False, description="是否为临时 IP")
    temporary_hours: Optional[int] = Field(None, ge=1, description="临时 IP 有效时长（小时）")

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v):
        if v is not None:
            import ipaddress as ip_mod
            try:
                ip_mod.ip_address(v)
            except ValueError:
                raise ValueError("IP 地址格式无效")
        return v


class IPBatchAllocateRequest(BaseModel):
    """批量分配 IP 请求"""
    segment_id: int = Field(..., description="所属网段 ID")
    count: int = Field(..., ge=1, le=256, description="分配数量")
    device_ids: Optional[list[int]] = Field(None, description="关联设备 ID 列表（与 count 对应）")
    responsible_person: Optional[str] = None
    department: Optional[str] = None
    reason: Optional[str] = None
    tags: Optional[list[str]] = Field(default=[])


class IPReleaseRequestV2(BaseModel):
    """IP 回收请求 - 扩展版"""
    ip_id: Optional[int] = Field(None, description="IP 记录 ID")
    ip_address: Optional[str] = Field(None, description="IP 地址")
    reason: Optional[str] = Field(None, description="回收原因")


class IPStatusChangeRequest(BaseModel):
    """IP 状态变更请求"""
    status: str = Field(..., description="目标状态: available/used/reserved/temporary")
    reason: Optional[str] = Field(None, description="变更原因")
    reservation_reason: Optional[str] = Field(None, description="保留原因（status=reserved 时）")
    reservation_expires_at: Optional[str] = Field(None, description="保留过期时间（ISO 格式）")
    temporary_hours: Optional[int] = Field(None, ge=1, description="临时有效时长（小时）")
    version: int = Field(..., description="当前版本号（乐观锁）")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid = {"available", "used", "reserved", "temporary"}
        if v not in valid:
            raise ValueError(f"状态必须是: {', '.join(valid)}")
        return v


class IPLifecycleLogResponse(BaseModel):
    """IP 生命周期日志响应"""
    id: int
    ip_address: str
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    operator_name: Optional[str] = None
    reason: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IPMatrixItem(BaseModel):
    """IP 矩阵视图单元格"""
    ip_address: str
    status: str
    device_name: Optional[str] = None
    responsible_person: Optional[str] = None
    hostname: Optional[str] = None
    allocated_at: Optional[datetime] = None
    is_online: bool = False
