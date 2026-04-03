"""
工单与流程引擎域模型

包含
- Ticket: 工单
- WorkflowDefinition: 流程定义（审批流模板
- WorkflowInstance: 流程实例（运行中的审批流
- WorkflowNode: 流程节点实例（每个审批节点的状态）
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, JSON,
    Boolean, Enum
)
from sqlalchemy.sql import func
from app.core.database import Base


class Ticket(Base):
    """工单"""
    __tablename__ = "tickets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    ticket_no = Column(String(50), unique=True, nullable=False, comment="工单编号")
    title = Column(String(300), nullable=False)
    description = Column(Text)
    ticket_type = Column(
        Enum("ip_apply", "ip_change", "ip_recycle", "device_onboard", "device_repair",
             "permission_apply", "change_request", "incident", "other"),
        nullable=False, index=True,
    )
    priority = Column(Enum("low", "medium", "high", "urgent"), default="medium")
    status = Column(
        Enum("draft", "pending", "in_progress", "approved", "rejected", "completed", "cancelled"),
        default="draft", nullable=False, index=True,
    )
    # 申请
    applicant_id = Column(BigInteger, nullable=False)
    applicant_name = Column(String(100))
    applicant_department = Column(String(200))
    # 当前处理
    assignee_id = Column(BigInteger)
    assignee_name = Column(String(100))
    # 关联资源
    related_ip = Column(String(45))
    related_device_id = Column(Integer)
    related_segment_id = Column(Integer)
    # 表单数据
    form_data = Column(JSON, default=dict, comment="工单表单数据")
    # 流程
    workflow_definition_id = Column(BigInteger, comment="关联流程定义")
    workflow_instance_id = Column(BigInteger, comment="关联流程实例")
    # SLA
    sla_deadline = Column(DateTime, comment="SLA 截止时间")
    sla_status = Column(Enum("normal", "warning", "overdue"), default="normal")
    # 时间
    submitted_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Ticket {self.ticket_no} [{self.status}]>"


class WorkflowDefinition(Base):
    """流程定义（审批流模板"""
    __tablename__ = "workflow_definitions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(50), comment="触发类型: ip_apply/device_onboard ")
    # 流程定义 JSON（节点列+ 连线 + 条件分支
    definition_json = Column(JSON, nullable=False, comment="流程定义")
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<WorkflowDef {self.name} v{self.version}>"


class WorkflowInstance(Base):
    """流程实例（运行中的审批流"""
    __tablename__ = "workflow_instances"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    definition_id = Column(BigInteger, nullable=False, index=True)
    ticket_id = Column(BigInteger, nullable=False, index=True)
    status = Column(Enum("running", "completed", "rejected", "cancelled"), default="running")
    current_node_id = Column(String(100), comment="当前节点 ID")
    history = Column(JSON, default=list, comment="审批历史")
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<WorkflowInstance def={self.definition_id} [{self.status}]>"
