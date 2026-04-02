"""
租户模型。

多租户架构的核心，每个租户拥有独立的：
- 网段、IP 资源
- 设备资产
- 权限范围
- 配置参数

设计思路：
- 采用共享数据库 + 行级隔离方案（tenant_id 字段），而非独立数据库。
  原因：181 条需求中大量跨租户汇总统计（如超级管理员全局视图），
  独立数据库方案会让跨租户查询非常复杂。
- 默认创建一个 ID=1 的"默认租户"，兼容现有无租户的数据。
- config 字段存储租户级配置（告警阈值、扫描策略等），
  覆盖系统全局配置，实现租户级个性化。
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
    code = Column(String(50), unique=True, nullable=False, index=True, comment="租户编码（唯一标识）")
    description = Column(Text, comment="租户描述")
    status = Column(
        Enum("active", "disabled"),
        default="active",
        nullable=False,
        comment="租户状态",
    )
    # 租户级配置（覆盖全局配置）
    config = Column(JSON, default=dict, comment="租户级配置（告警阈值/扫描策略等）")
    # 联系人信息
    contact_name = Column(String(100), comment="联系人姓名")
    contact_email = Column(String(200), comment="联系人邮箱")
    contact_phone = Column(String(20), comment="联系人电话")
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Tenant {self.code} [{self.status}]>"
