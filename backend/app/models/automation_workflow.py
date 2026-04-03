"""
自动化工作流模型

基于事件触发的自动化流程引擎，区别于审批流（工单流程）。
支持：数据变更触发、定时触发、Webhook 触发、告警触发。
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, JSON, Boolean, Enum
)
from sqlalchemy.sql import func
from app.core.database import Base


class AutomationWorkflow(Base):
    """自动化工作流定义"""
    __tablename__ = "automation_workflows"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)

    name = Column(String(200), nullable=False, comment="工作流名称")
    description = Column(Text, comment="描述")

    trigger_type = Column(
        Enum("data_change", "schedule", "webhook", "alert", "ticket_status"),
        nullable=False, comment="触发器类型",
    )
    trigger_config = Column(JSON, nullable=False, comment="触发器配置")
    workflow_json = Column(JSON, nullable=False, comment="工作流定义")

    is_active = Column(Boolean, default=True, comment="是否启用")
    version = Column(Integer, default=1, comment="版本号")

    total_runs = Column(Integer, default=0, comment="总执行次数")
    success_runs = Column(Integer, default=0, comment="成功次数")
    last_run_at = Column(DateTime, comment="最后执行时间")
    last_run_result = Column(String(20), comment="最后执行结果")

    created_by = Column(BigInteger, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<AutomationWorkflow {self.name} [{self.trigger_type}]>"
