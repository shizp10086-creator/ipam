"""
User Model - 用户表
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """
    用户模型
    存储系统用户信息，包括认证和授权相关数据
    """
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 用户基本信息
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    email = Column(String(100), nullable=False, comment="邮箱")
    full_name = Column(String(100), nullable=False, comment="全名")
    
    # 角色和状态
    role = Column(
        String(20), 
        nullable=False, 
        default="user", 
        index=True,
        comment="角色: admin/user/readonly"
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    
    # 关系定义
    # 用户创建的网段
    network_segments = relationship("NetworkSegment", back_populates="creator", foreign_keys="NetworkSegment.created_by")
    
    # 用户分配的 IP 地址
    allocated_ips = relationship("IPAddress", back_populates="allocator", foreign_keys="IPAddress.allocated_by")
    
    # 用户创建的设备
    devices = relationship("Device", back_populates="creator", foreign_keys="Device.created_by")
    
    # 用户的操作日志
    operation_logs = relationship("OperationLog", back_populates="user")
    
    # 用户发起的扫描
    scan_histories = relationship("ScanHistory", back_populates="creator")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
