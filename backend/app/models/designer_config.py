"""
设计器配置存储模型

所有低代码设计器（表单/流程/报表/仪表盘/大屏/PPT/页面布局）的产物
统一存储在 designer_configs 表中，以 JSON 格式保存设计器定义。
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, JSON,
    Boolean, Enum, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DesignerConfig(Base):
    """设计器配置表"""
    __tablename__ = "designer_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    name = Column(String(200), nullable=False, comment="配置名称")
    description = Column(Text, comment="描述")
    config_type = Column(
        Enum("form", "workflow", "report", "dashboard", "screen", "ppt", "page_layout"),
        nullable=False, index=True,
        comment="设计器类型",
    )

    config_json = Column(JSON, nullable=False, comment="设计器定义JSON")

    status = Column(
        Enum("draft", "published", "archived"),
        default="draft", nullable=False,
        comment="发布状态",
    )
    current_version = Column(Integer, default=1, comment="当前版本号")

    is_template = Column(Boolean, default=False, comment="是否为模板")
    template_category = Column(String(100), comment="模板分类")
    use_count = Column(Integer, default=0, comment="模板使用次数")

    share_token = Column(String(64), unique=True, comment="分享链接Token")
    share_password = Column(String(100), comment="分享密码")
    share_expires_at = Column(DateTime, comment="分享过期时间")

    created_by = Column(BigInteger, comment="创建人ID")
    updated_by = Column(BigInteger, comment="最后更新人ID")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    versions = relationship("DesignerConfigVersion", back_populates="config", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DesignerConfig {self.config_type}:{self.name} v{self.current_version} [{self.status}]>"


class DesignerConfigVersion(Base):
    """设计器配置版本历史"""
    __tablename__ = "designer_config_versions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_id = Column(BigInteger, ForeignKey("designer_configs.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, comment="版本号")
    config_json = Column(JSON, nullable=False, comment="该版本的设计器定义JSON")
    change_note = Column(String(500), comment="版本备注")
    created_by = Column(BigInteger, comment="保存人ID")
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    config = relationship("DesignerConfig", back_populates="versions")

    def __repr__(self):
        return f"<DesignerConfigVersion config={self.config_id} v{self.version}>"
