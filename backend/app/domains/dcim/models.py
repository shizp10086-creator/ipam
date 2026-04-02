"""
DCIM 域数据模型。

包含：
- DataCenter: 机房（站点>建筑>楼层>机房 树形结构）
- Rack: 机架（U 位管理、功率管理）
- RackInstallation: 设备安装记录（设备与机架 U 位的关联）
- Vlan: VLAN 管理
- CableConnection: 线缆连接（端口间物理连接）

设计思路：
- 机房用 parent_id 自引用实现树形层级（站点>建筑>楼层>机房）
- 机架 U 位用 start_u + u_size 表示设备占用范围，安装时校验连续空闲空间
- VLAN 与网段、设备端口多对多关联
- 线缆连接记录两端设备端口，校验端口不被重复占用
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, JSON,
    Boolean, Numeric, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DataCenter(Base):
    """机房/站点/建筑/楼层（树形层级结构）"""
    __tablename__ = "datacenters"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    name = Column(String(200), nullable=False, comment="名称")
    dc_type = Column(
        Enum("site", "building", "floor", "room"),
        nullable=False, comment="类型：站点/建筑/楼层/机房",
    )
    parent_id = Column(BigInteger, ForeignKey("datacenters.id"), comment="父节点ID")
    location = Column(String(500), comment="地理位置/地址")
    area = Column(Numeric(10, 2), comment="面积（平方米）")
    power_capacity = Column(Numeric(10, 2), comment="额定电力容量（kW）")
    description = Column(Text, comment="描述")
    floor_plan_url = Column(String(500), comment="平面图 URL")
    contact_name = Column(String(100), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    custom_fields = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("DataCenter", remote_side=[id], backref="children")
    racks = relationship("Rack", back_populates="datacenter")

    def __repr__(self):
        return f"<DataCenter [{self.dc_type}] {self.name}>"


class Rack(Base):
    """机架"""
    __tablename__ = "racks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    datacenter_id = Column(BigInteger, ForeignKey("datacenters.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="机架名称")
    total_u = Column(Integer, default=42, nullable=False, comment="总 U 数")
    used_u = Column(Integer, default=0, comment="已用 U 数")
    rated_power = Column(Numeric(10, 2), comment="额定功率（W）")
    current_power = Column(Numeric(10, 2), default=0, comment="当前功耗（W）")
    max_weight = Column(Numeric(10, 2), comment="承重上限（kg）")
    row_number = Column(String(20), comment="排号")
    column_number = Column(String(20), comment="列号")
    description = Column(Text)
    custom_fields = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    datacenter = relationship("DataCenter", back_populates="racks")
    installations = relationship("RackInstallation", back_populates="rack", cascade="all, delete-orphan")

    @property
    def space_usage_rate(self):
        """空间使用率"""
        return round((self.used_u / self.total_u) * 100, 2) if self.total_u > 0 else 0

    @property
    def power_usage_rate(self):
        """功率使用率"""
        if self.rated_power and self.rated_power > 0:
            return round((float(self.current_power or 0) / float(self.rated_power)) * 100, 2)
        return 0

    def __repr__(self):
        return f"<Rack {self.name} {self.used_u}/{self.total_u}U>"


class RackInstallation(Base):
    """设备安装记录（设备在机架中的位置）"""
    __tablename__ = "rack_installations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rack_id = Column(BigInteger, ForeignKey("racks.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    start_u = Column(Integer, nullable=False, comment="起始 U 位（从下往上，1 开始）")
    u_size = Column(Integer, nullable=False, comment="设备占用 U 数")
    face = Column(Enum("front", "rear"), default="front", comment="安装面：正面/背面")
    power_consumption = Column(Numeric(10, 2), comment="设备功耗（W）")
    pdu_port = Column(String(50), comment="PDU 电源端口")
    installed_by = Column(BigInteger, comment="安装人ID")
    installed_at = Column(DateTime, default=datetime.utcnow, comment="安装时间")
    uninstalled_at = Column(DateTime, comment="下架时间")
    status = Column(Enum("installed", "uninstalled"), default="installed")

    rack = relationship("Rack", back_populates="installations")

    @property
    def end_u(self):
        """结束 U 位"""
        return self.start_u + self.u_size - 1

    def __repr__(self):
        return f"<RackInstallation rack={self.rack_id} U{self.start_u}-{self.end_u}>"


class Vlan(Base):
    """VLAN 管理"""
    __tablename__ = "vlans"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    vlan_id = Column(Integer, nullable=False, comment="VLAN ID (1-4094)")
    name = Column(String(200), nullable=False, comment="VLAN 名称")
    description = Column(Text)
    group_name = Column(String(200), comment="VLAN 分组")
    # 关联网段（JSON 存储网段 ID 列表）
    segment_ids = Column(JSON, default=list, comment="关联网段 ID 列表")
    custom_fields = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Vlan {self.vlan_id} {self.name}>"


class CableConnection(Base):
    """线缆连接（设备端口间的物理连接）"""
    __tablename__ = "cable_connections"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    # A 端
    device_a_id = Column(Integer, comment="A 端设备 ID")
    port_a = Column(String(100), nullable=False, comment="A 端端口名称")
    # B 端
    device_b_id = Column(Integer, comment="B 端设备 ID")
    port_b = Column(String(100), nullable=False, comment="B 端端口名称")
    # 线缆信息
    cable_type = Column(Enum("fiber", "copper", "dac"), comment="线缆类型")
    cable_number = Column(String(100), comment="线缆编号")
    cable_length = Column(Numeric(10, 2), comment="线缆长度（米）")
    status = Column(Enum("active", "inactive"), default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Cable {self.port_a} <-> {self.port_b}>"
