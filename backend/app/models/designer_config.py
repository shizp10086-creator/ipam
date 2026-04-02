"""
设计器配置存储模型。

所有低代码设计器（表单/流程/报表/仪表盘/大屏/PPT/页面布局）的产物
统一存储在 designer_configs 表中，以 JSON 格式保存设计器定义。

设计思路：
- 统一存储而非每种设计器一张表，因为它们的元数据结构相同（名称/类型/版本/JSON 定义）
- config_json 字段存储设计器产物（组件列表/布局/数据绑定/样式等）
- 支持版本管理：每次保存自动创建新版本（designer_config_versions 表）
- 支持模板库：is_template=True 的记录可被其他用户克隆使用
- 支持发布状态：draft（草稿）→ published（已发布）→ archived（已归档）
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
    """设计器配置表 — 所有设计器产物的统一存储"""
    __tablename__ = "designer_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # 基本信息
    name = Column(String(200), nullable=False, comment="配置名称")
    description = Column(Text, comment="描述")
    config_type = Column(
        Enum("form", "workflow", "report", "dashboard", "screen", "ppt", "page_layout"),
        nullable=False, index=True,
        comment="设计器类型",
    )

    # 设计器产物（JSON）
    config_json = Column(JSON, nullable=False, comment="设计器定义 JSON")

    # 状态与版本
    status = Column(
        Enum("draft", "published", "archived"),
        default="draft", nullable=False,
        comment="发布状态",
    )
    current_version = Column(Integer, default=1, comment="当前版本号")

    # 模板相关
    is_template = Column(Boolean, default=False, comment="是否为模板")
    template_category = Column(String(100), comment="模板分类")
    use_count = Column(Integer, default=0, comment="模板使用次数")

    # 分享
    share_token = Column(String(64), unique=True, comment="分享链接 Token")
    share_password = Column(String(100), comment="分享密码")
    share_expires_at = Column(DateTime, comment="分享过期时间")

    # 创建信息
    created_by = Column(BigInteger, comment="创建人ID")
    updated_by = Column(BigInteger, comment="最后更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    versions = relationship("DesignerConfigVersion", back_populates="config", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DesignerConfig {self.config_type}:{self.name} v{self.current_version} [{self.status}]>"


class DesignerConfigVersion(Base):
    """设计器配置版本历史"""
    __tablename__ = "designer_config_versions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_id = Column(BigInteger, ForeignKey("designer_configs.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, comment="版本号")
    config_json = Column(JSON, nullable=False, comment="该版本的设计器定义 JSON")
    change_note = Column(String(500), comment="版本备注")
    created_by = Column(BigInteger, comment="保存人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    config = relationship("DesignerConfig", back_populates="versions")

    def __repr__(self):
        return f"<DesignerConfigVersion config={self.config_id} v{self.version}>"
