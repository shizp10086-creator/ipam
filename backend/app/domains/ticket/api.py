"""
工单与流程引擎 API。
"""
import logging
import secrets
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse
from app.domains.ticket.models import Ticket, WorkflowDefinition, WorkflowInstance

logger = logging.getLogger(__name__)
router = APIRouter()


class TicketCreate(BaseModel):
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    ticket_type: str
    priority: str = "medium"
    form_data: Optional[dict] = {}
    related_ip: Optional[str] = None
    related_device_id: Optional[int] = None
    related_segment_id: Optional[int] = None

class TicketResponse(BaseModel):
    id: int; ticket_no: str; title: str; ticket_type: str
    priority: str; status: str
    applicant_name: Optional[str] = None; assignee_name: Optional[str] = None
    sla_status: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("/tickets", summary="获取工单列表")
def list_tickets(
    status: Optional[str] = None,
    ticket_type: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if ticket_type:
        query = query.filter(Ticket.ticket_type == ticket_type)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if search:
        query = query.filter((Ticket.title.contains(search)) | (Ticket.ticket_no.contains(search)))
    total = query.count()
    items = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

    # 统计
    pending = db.query(Ticket).filter(Ticket.status == "pending").count()
    in_progress = db.query(Ticket).filter(Ticket.status == "in_progress").count()

    return APIResponse.success(data={
        "items": [TicketResponse.model_validate(t).model_dump() for t in items],
        "total": total,
        "stats": {"pending": pending, "in_progress": in_progress},
    })


@router.post("/tickets", status_code=201, summary="创建工单")
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    ticket_no = f"WO-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
    ticket = Ticket(
        tenant_id=1,
        ticket_no=ticket_no,
        title=data.title,
        description=data.description,
        ticket_type=data.ticket_type,
        priority=data.priority,
        status="pending",
        applicant_id=1,  # TODO: 从当前用户获取
        applicant_name="admin",
        form_data=data.form_data,
        related_ip=data.related_ip,
        related_device_id=data.related_device_id,
        related_segment_id=data.related_segment_id,
        submitted_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return APIResponse.success(data=TicketResponse.model_validate(ticket).model_dump(), code=201, message="工单创建成功")


@router.get("/tickets/{ticket_id}", summary="获取工单详情")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "工单不存在")
    return APIResponse.success(data={
        **TicketResponse.model_validate(ticket).model_dump(),
        "description": ticket.description,
        "form_data": ticket.form_data,
        "related_ip": ticket.related_ip,
        "applicant_department": ticket.applicant_department,
    })


@router.put("/tickets/{ticket_id}/approve", summary="审批通过")
def approve_ticket(ticket_id: int, comment: str = "", db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "工单不存在")
    ticket.status = "approved"
    ticket.completed_at = datetime.utcnow()
    db.commit()
    return APIResponse.success(message="审批通过")


@router.put("/tickets/{ticket_id}/reject", summary="审批驳回")
def reject_ticket(ticket_id: int, reason: str = "", db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "工单不存在")
    ticket.status = "rejected"
    ticket.completed_at = datetime.utcnow()
    db.commit()
    return APIResponse.success(message="已驳回")


# ==================== 流程定义 ====================

@router.get("/workflows", summary="获取流程定义列表")
def list_workflows(db: Session = Depends(get_db)):
    items = db.query(WorkflowDefinition).filter(WorkflowDefinition.is_active == True).all()
    return APIResponse.success(data={
        "items": [{"id": w.id, "name": w.name, "trigger_type": w.trigger_type,
                    "version": w.version, "is_active": w.is_active} for w in items],
        "total": len(items),
    })

@router.post("/workflows", status_code=201, summary="创建流程定义")
def create_workflow(name: str, trigger_type: str, definition_json: dict, db: Session = Depends(get_db)):
    wf = WorkflowDefinition(tenant_id=1, name=name, trigger_type=trigger_type, definition_json=definition_json)
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return APIResponse.success(message="流程定义创建成功", code=201)
