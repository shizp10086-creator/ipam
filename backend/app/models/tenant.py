"""
租户模型。
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, JSON, Enum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="租户名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="租户编码")
    description = Column(Text, comment="租户描述")
    status = Column(
        Enum("active", "disabled"),
        default="active",
        nullable=False,
        comment="租户状态",
    )
    config = Column(JSON, default=dict, comment="租户级配置")
    contact_name = Column(String(100), comment="联系人姓名")
    contact_email = Column(String(200), comment="联系人邮箱")
    contact_phone = Column(String(20), comment="联系人电话")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<Tenant {self.code} [{self.status}]>"
