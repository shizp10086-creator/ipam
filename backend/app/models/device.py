"""
Device Model - 设备表
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Device(Base):
    """
    设备模型
    存储网络设备信息，包括设备名称、MAC 地址、责任人等
    """
    __tablename__ = "devices"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 设备基本信息
    name = Column(String(100), nullable=False, index=True, comment="设备名称")
    mac_address = Column(String(17), unique=True, nullable=False, index=True, comment="MAC 地址")
    device_type = Column(String(50), nullable=True, comment="设备类型（服务器/交换机/路由器/终端等）")
    manufacturer = Column(String(100), nullable=True, comment="制造商")
    model = Column(String(100), nullable=True, comment="型号")

    # 责任人信息
    owner = Column(String(100), nullable=False, index=True, comment="责任人")
    department = Column(String(100), nullable=True, comment="部门")
    location = Column(String(200), nullable=True, comment="物理位置")

    # 描述
    description = Column(Text, nullable=True, comment="描述")

    # 外键
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人 ID")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # 关系定义
    # 创建者
    creator = relationship("User", back_populates="devices", foreign_keys=[created_by])

    # 设备关联的 IP 地址
    ip_addresses = relationship("IPAddress", back_populates="device")

    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.name}', mac='{self.mac_address}')>"
