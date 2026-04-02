"""
运维协作域模型 — 知识库、值班排班。
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, JSON, Boolean, Enum
)
from sqlalchemy.sql import func
from app.core.database import Base


class KnowledgeArticle(Base):
    """知识库文章"""
    __tablename__ = "knowledge_articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False, comment="富文本内容")
    category = Column(String(100), index=True, comment="分类：故障案例/配置手册/运维规范/FAQ")
    tags = Column(JSON, default=list)
    # 关联资源
    related_ips = Column(JSON, default=list, comment="关联 IP 地址列表")
    related_device_ids = Column(JSON, default=list, comment="关联设备 ID 列表")
    related_segment_ids = Column(JSON, default=list, comment="关联网段 ID 列表")
    # 故障案例模板字段
    symptom = Column(Text, comment="故障现象")
    root_cause = Column(Text, comment="根因分析")
    solution = Column(Text, comment="解决方案")
    # 统计
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    author_id = Column(BigInteger)
    author_name = Column(String(100))
    status = Column(Enum("draft", "published", "archived"), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Article {self.title[:30]}>"


class DutySchedule(Base):
    """值班排班"""
    __tablename__ = "duty_schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True, comment="值班日期")
    shift = Column(Enum("day", "night", "all_day"), default="all_day", comment="班次")
    primary_user_id = Column(BigInteger, nullable=False, comment="主值班人")
    primary_user_name = Column(String(100))
    backup_user_id = Column(BigInteger, comment="备班人")
    backup_user_name = Column(String(100))
    handover_notes = Column(Text, comment="交接备注")
    is_confirmed = Column(Boolean, default=False, comment="接班人是否确认")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Duty {self.date} {self.primary_user_name}>"
