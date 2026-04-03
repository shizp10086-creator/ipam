"""
User Model - 用户表

扩展说明：
- 新增 tenant_id 支持多租户隔离（默认值 1 = 默认租户，兼容旧数据）
- 新增 department、phone、language、timezone、theme 字段
- role 字段保留原有值，同时支持自定义角色（通过 roles 表关联）
"""
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 多租户
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # 用户基本信息
    username = Column(String(50), nullable=False, index=True, comment="用户名")
    hashed_password = Column(String(255), nullable=False, comment="加密密码(bcrypt)")
    email = Column(String(100), nullable=False, comment="邮箱")
    full_name = Column(String(100), nullable=False, comment="全名")
    department = Column(String(200), comment="部门")
    phone = Column(String(20), comment="手机号")

    # LDAP/企业微信集成
    ldap_dn = Column(String(500), comment="LDAP DN")
    wechat_userid = Column(String(100), comment="企业微信 UserID")

    # 角色和状态
    role = Column(
        String(20),
        nullable=False,
        default="user",
        index=True,
        comment="角色: admin/user/readonly"
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")

    # 个性化设置
    language = Column(String(10), default="zh-CN", comment="界面语言")
    timezone = Column(String(50), default="Asia/Shanghai", comment="时区")
    theme = Column(JSON, comment="主题偏好")

    # 登录信息
    last_login_at = Column(DateTime, comment="最后登录时间")
    last_login_ip = Column(String(45), comment="最后登录IP")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # 唯一约束：同一租户内用户名唯一
    __table_args__ = (
        # UniqueConstraint('tenant_id', 'username', name='uk_tenant_username'),
        {"comment": "用户表"},
    )

    # 关系定义
    network_segments = relationship("NetworkSegment", back_populates="creator", foreign_keys="NetworkSegment.created_by")
    allocated_ips = relationship("IPAddress", back_populates="allocator", foreign_keys="IPAddress.allocated_by")
    devices = relationship("Device", back_populates="creator", foreign_keys="Device.created_by")
    operation_logs = relationship("OperationLog", back_populates="user")
    scan_histories = relationship("ScanHistory", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}', tenant={self.tenant_id})>"
