"""
NetworkSegment Model - 网段表
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class NetworkSegment(Base):
    """
    网段模型
    存储网络段信息，包括网络地址、前缀长度、网关等
    """
    __tablename__ = "network_segments"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 网段基本信息
    name = Column(String(100), nullable=False, comment="网段名称")
    company = Column(String(100), nullable=True, comment="所属公司")
    network = Column(String(45), nullable=False, index=True, comment="网络地址 (如 192.168.1.0)")
    prefix_length = Column(Integer, nullable=False, index=True, comment="前缀长度 (如 24)")
    gateway = Column(String(45), nullable=True, comment="网关地址")
    description = Column(Text, nullable=True, comment="描述")
    
    # 告警配置
    usage_threshold = Column(Integer, default=80, nullable=False, comment="使用率告警阈值（百分比）")
    
    # 外键
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人 ID")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    
    # 关系定义
    # 创建者
    creator = relationship("User", back_populates="network_segments", foreign_keys=[created_by])
    
    # 网段内的 IP 地址
    ip_addresses = relationship("IPAddress", back_populates="segment", cascade="all, delete-orphan")
    
    # 网段的告警
    alerts = relationship("Alert", back_populates="segment", cascade="all, delete-orphan")
    
    # 网段的扫描历史
    scan_histories = relationship("ScanHistory", back_populates="segment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<NetworkSegment(id={self.id}, name='{self.name}', network='{self.network}/{self.prefix_length}')>"
