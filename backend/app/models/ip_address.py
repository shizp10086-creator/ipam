"""
IPAddress Model - IP 地址表
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class IPAddress(Base):
    """
    IP 地址模型
    存储 IP 地址信息，包括状态、关联设备、分配信息等
    """
    __tablename__ = "ip_addresses"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # IP 地址信息
    ip_address = Column(String(45), unique=True, nullable=False, index=True, comment="IP 地址")
    status = Column(
        String(20), 
        nullable=False, 
        default="available", 
        index=True,
        comment="状态: available/used/reserved"
    )
    
    # 外键
    segment_id = Column(Integer, ForeignKey("network_segments.id"), nullable=False, index=True, comment="所属网段 ID")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True, comment="关联设备 ID")
    allocated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="分配人 ID")
    
    # 分配和扫描信息
    allocated_at = Column(DateTime, nullable=True, comment="分配时间")
    last_seen = Column(DateTime, nullable=True, comment="最后扫描时间")
    is_online = Column(Boolean, default=False, nullable=False, comment="是否在线（最后扫描结果）")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    
    # 关系定义
    # 所属网段
    segment = relationship("NetworkSegment", back_populates="ip_addresses")
    
    # 关联设备
    device = relationship("Device", back_populates="ip_addresses")
    
    # 分配人
    allocator = relationship("User", back_populates="allocated_ips", foreign_keys=[allocated_by])
    
    def __repr__(self):
        return f"<IPAddress(id={self.id}, ip='{self.ip_address}', status='{self.status}')>"
