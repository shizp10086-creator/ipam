"""
网段模型 - 扩展版。

相比原版新增：
- tenant_id 多租户隔离
- cidr 字段（CIDR 表示法，如 192.168.1.0/24）
- parent_id 子网嵌套（树形结构）
- group_id 网段分组
- vlan_id 关联 VLAN
- tags JSON 标签
- custom_fields JSON 自定义字段
- 使用率统计字段（total_ips/used_ips/reserved_ips/temporary_ips/usage_rate）
- 多级告警阈值（warning/critical）
- 乐观锁 version
- 软删除 deleted_at

设计思路：
- CIDR 用 ipaddress 库解析，network/broadcast/total_ips 在创建时自动计算
- 子网嵌套用 parent_id 自引用外键，查询时递归或用 CTE
- 使用率在 IP 分配/回收时实时更新（而非查询时计算），避免大网段查询慢
- tags 用 JSON 存储（比关联表简单，标签数量不多）
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, ForeignKey,
    JSON, Enum, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SegmentGroup(Base):
    """网段分组表（支持嵌套分组）"""
    __tablename__ = "segment_groups"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, nullable=False, index=True, comment="租户ID")
    name = Column(String(200), nullable=False, comment="分组名称")
    parent_id = Column(BigInteger, ForeignKey("segment_groups.id"), comment="父分组ID")
    description = Column(Text, comment="分组描述")
    sort_order = Column(Integer, default=0, comment="排序序号")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    parent = relationship("SegmentGroup", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<SegmentGroup {self.name}>"


class NetworkSegment(Base):
    """
    网段模型。
    支持 CIDR 表示法、子网嵌套、分组管理、标签、多级告警。
    """
    __tablename__ = "network_segments"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 多租户
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # 网段基本信息
    name = Column(String(100), nullable=False, comment="网段名称")
    cidr = Column(String(43), nullable=False, index=True, comment="CIDR 表示法（如 192.168.1.0/24）")
    network = Column(String(45), nullable=False, index=True, comment="网络地址")
    broadcast = Column(String(45), comment="广播地址")
    prefix_length = Column(Integer, nullable=False, index=True, comment="前缀长度")
    ip_version = Column(Integer, default=4, comment="IP 版本（4 或 6）")
    gateway = Column(String(45), comment="网关地址")
    description = Column(Text, comment="描述（支持富文本）")
    company = Column(String(100), comment="所属公司")
    business_group = Column(String(200), comment="所属业务组")

    # 子网嵌套
    parent_id = Column(Integer, ForeignKey("network_segments.id"), comment="父网段ID（子网嵌套）")

    # 分组
    group_id = Column(BigInteger, ForeignKey("segment_groups.id"), comment="所属分组ID")

    # 标签和自定义字段
    tags = Column(JSON, default=list, comment="自定义标签列表")
    custom_fields = Column(JSON, default=dict, comment="自定义字段")

    # 使用率统计（实时更新，非查询时计算）
    total_ips = Column(Integer, default=0, nullable=False, comment="可用 IP 总数")
    used_ips = Column(Integer, default=0, nullable=False, comment="已用 IP 数")
    reserved_ips = Column(Integer, default=0, nullable=False, comment="保留 IP 数")
    temporary_ips = Column(Integer, default=0, nullable=False, comment="临时 IP 数")
    usage_rate = Column(Numeric(5, 2), default=0, comment="使用率（百分比）")

    # 多级告警阈值
    usage_threshold = Column(Integer, default=80, nullable=False, comment="使用率告警阈值-警告（百分比）")
    alert_threshold_warning = Column(Integer, default=80, comment="警告阈值")
    alert_threshold_critical = Column(Integer, default=90, comment="严重阈值")

    # 状态
    status = Column(Enum("active", "archived"), default="active", comment="网段状态")

    # 乐观锁
    version = Column(Integer, default=1, nullable=False, comment="乐观锁版本号")

    # 外键
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, comment="软删除时间")

    # 关系
    creator = relationship("User", back_populates="network_segments", foreign_keys=[created_by])
    parent = relationship("NetworkSegment", remote_side=[id], backref="children")
    group = relationship("SegmentGroup", backref="segments")
    ip_addresses = relationship("IPAddress", back_populates="segment", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="segment", cascade="all, delete-orphan")
    scan_histories = relationship("ScanHistory", back_populates="segment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<NetworkSegment {self.cidr} [{self.status}] usage={self.usage_rate}%>"

    def recalculate_usage(self):
        """重新计算使用率。在 IP 分配/回收后调用。"""
        if self.total_ips > 0:
            used = self.used_ips + self.reserved_ips + self.temporary_ips
            self.usage_rate = round((used / self.total_ips) * 100, 2)
        else:
            self.usage_rate = 0
