"""
IP 地址模型 - 扩展版。

新增：
- tenant_id 多租户
- ip_numeric 数值（用于范围查询和排序）
- ip_version IPv4/IPv6 双栈
- status 新增 temporary 状态
- mac_address/hostname/responsible_person/department 关联信息
- reservation_reason/reservation_expires_at 保留信息
- temporary_expires_at 临时 IP 过期时间
- dns_name DNS 关联
- tags/custom_fields 标签和自定义字段
- version 乐观锁
- deleted_at 软删除
- idempotency_key 幂等键

设计思路：
- ip_numeric 用于范围查询（如查找连续空闲 IP），比字符串比较快得多
- status 四种状态：available/used/reserved/temporary，状态机校验在 Service 层
- 临时 IP 有 temporary_expires_at，Celery 定时任务检查过期自动回收
- 保留 IP 有 reservation_expires_at，到期自动转为 available
"""
import ipaddress as ip_module
from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime, ForeignKey,
    Boolean, JSON, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class IPAddress(Base):
    """IP 地址模型"""
    __tablename__ = "ip_addresses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 多租户
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # IP 地址信息
    ip_address = Column(String(45), nullable=False, index=True, comment="IP 地址")
    ip_numeric = Column(BigInteger, index=True, comment="IP 数值（用于范围查询）")
    ip_version = Column(Integer, default=4, comment="IP 版本（4 或 6）")

    # 状态
    status = Column(
        Enum("available", "used", "reserved", "temporary"),
        nullable=False, default="available", index=True,
        comment="状态: available/used/reserved/temporary",
    )

    # 外键
    segment_id = Column(Integer, ForeignKey("network_segments.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    allocated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 关联信息
    mac_address = Column(String(17), index=True, comment="MAC 地址")
    hostname = Column(String(255), comment="主机名")
    responsible_person = Column(String(100), comment="责任人")
    department = Column(String(200), comment="所属部门")
    allocation_reason = Column(Text, comment="分配原因")

    # 保留信息
    reservation_reason = Column(Text, comment="保留原因")
    reservation_expires_at = Column(DateTime, comment="保留过期时间")

    # 临时 IP 过期
    temporary_expires_at = Column(DateTime, comment="临时 IP 过期时间")

    # DNS 关联
    dns_name = Column(String(255), comment="DNS 域名")

    # 标签和自定义字段
    tags = Column(JSON, default=list, comment="标签列表")
    custom_fields = Column(JSON, default=dict, comment="自定义字段")

    # 扫描信息
    is_online = Column(Boolean, default=False, nullable=False, comment="是否在线")
    last_seen = Column(DateTime, comment="最后在线时间")
    last_scan_at = Column(DateTime, comment="最后扫描时间")
    response_time_ms = Column(Integer, comment="最后响应时间(ms)")

    # 时间戳
    allocated_at = Column(DateTime, comment="分配时间")
    released_at = Column(DateTime, comment="回收时间")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, comment="软删除时间")

    # 乐观锁
    version = Column(Integer, default=1, nullable=False, comment="乐观锁版本号")

    # 幂等键
    idempotency_key = Column(String(64), comment="幂等键（防重复操作）")

    # 关系
    segment = relationship("NetworkSegment", back_populates="ip_addresses")
    device = relationship("Device", back_populates="ip_addresses")
    allocator = relationship("User", back_populates="allocated_ips", foreign_keys=[allocated_by])

    def __repr__(self):
        return f"<IPAddress {self.ip_address} [{self.status}]>"

    @staticmethod
    def ip_to_numeric(ip_str: str) -> int:
        """将 IP 地址转换为数值，用于范围查询。"""
        return int(ip_module.ip_address(ip_str))


class IPLifecycleLog(Base):
    """
    IP 地址生命周期日志。
    
    记录 IP 的每一次状态变更（分配/回收/保留/标签修改等），
    用于完整的使用历史追溯。
    """
    __tablename__ = "ip_lifecycle_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    ip_address_id = Column(Integer, nullable=False, index=True, comment="IP 记录 ID")
    ip_address = Column(String(45), nullable=False, index=True, comment="IP 地址")
    action = Column(
        Enum("allocate", "release", "reserve", "unreserve", "status_change", "tag_change"),
        nullable=False, comment="操作类型",
    )
    old_status = Column(String(20), comment="变更前状态")
    new_status = Column(String(20), comment="变更后状态")
    device_id = Column(Integer, comment="关联设备ID")
    operator_id = Column(Integer, comment="操作人ID")
    operator_name = Column(String(100), comment="操作人姓名")
    reason = Column(Text, comment="操作原因")
    details = Column(JSON, comment="变更详情（前后差异）")
    client_ip = Column(String(45), comment="操作来源IP")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<IPLifecycleLog {self.ip_address} [{self.action}]>"
