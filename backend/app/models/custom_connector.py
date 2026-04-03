"""
自定义连接器模型

通过可视化配置对接外部系统 API/数据库，
供表单、报表、仪表盘等设计器引用作为数据源。
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, String, Text, DateTime, JSON, Boolean, Enum
)
from sqlalchemy.sql import func
from app.core.database import Base


class CustomConnector(Base):
    """自定义连接器"""
    __tablename__ = "custom_connectors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)

    name = Column(String(200), nullable=False, comment="连接器名称")
    description = Column(Text, comment="描述")
    connector_type = Column(
        Enum("rest_api", "database", "ldap", "smtp", "wechat", "dingtalk", "feishu"),
        nullable=False, comment="连接器类型",
    )

    config = Column(JSON, nullable=False, comment="连接配置")

    is_active = Column(Boolean, default=True, comment="是否启用")
    last_test_at = Column(DateTime, comment="最后测试时间")
    last_test_result = Column(Boolean, comment="最后测试结果")

    created_by = Column(BigInteger, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<CustomConnector {self.connector_type}:{self.name}>"
