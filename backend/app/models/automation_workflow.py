"""
自动化工作流模型。

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
    """自动化工作流定义表"""
    __tablename__ = "automation_workflows"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)

    name = Column(String(200), nullable=False, comment="工作流名称")
    description = Column(Text, comment="描述")

    # 触发器配置
    trigger_type = Column(
        Enum("data_change", "schedule", "webhook", "alert", "ticket_status"),
        nullable=False, comment="触发器类型",
    )
    trigger_config = Column(JSON, nullable=False, comment="触发器配置")
    # 示例:
    # data_change: {"model": "ip_addresses", "field": "status", "old_value": "available", "new_value": "used"}
    # schedule: {"cron": "0 8 * * 1"}
    # webhook: {"path": "/webhook/auto-001", "secret": "..."}
    # alert: {"alert_type": "segment_usage", "level": "critical"}

    # 条件和动作（流程定义 JSON）
    workflow_json = Column(JSON, nullable=False, comment="工作流定义（条件+动作链）")
    # 示例:
    # {"conditions": [{"field": "usage_rate", "op": ">", "value": 90}],
    #  "actions": [{"type": "send_notification", "config": {...}}, {"type": "create_ticket", "config": {...}}]}

    is_active = Column(Boolean, default=True, comment="是否启用")
    version = Column(Integer, default=1, comment="版本号")

    # 执行统计
    total_runs = Column(Integer, default=0, comment="总执行次数")
    success_runs = Column(Integer, default=0, comment="成功次数")
    last_run_at = Column(DateTime, comment="最后执行时间")
    last_run_result = Column(String(20), comment="最后执行结果")

    created_by = Column(BigInteger, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AutomationWorkflow {self.name} [{self.trigger_type}]>"
