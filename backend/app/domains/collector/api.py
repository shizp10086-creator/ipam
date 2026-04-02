"""
数据采集域 API — 采集任务管理、凭证管理、执行日志。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse
from app.domains.collector.models import CollectorCredential, CollectorTask, CollectorTaskLog

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schema ====================

class CredentialCreate(BaseModel):
    name: str = Field(..., max_length=200)
    credential_type: str
    credential_data: dict
    description: Optional[str] = None

class TaskCreate(BaseModel):
    name: str = Field(..., max_length=200)
    protocol: str
    targets: list
    credential_id: Optional[int] = None
    config: Optional[dict] = {}
    interval_seconds: int = 300
    timeout_seconds: int = 30
    priority: int = 5

class TaskResponse(BaseModel):
    id: int; name: str; protocol: str; targets: list
    is_active: bool; interval_seconds: int
    last_run_at: Optional[datetime] = None; last_run_status: Optional[str] = None
    total_runs: int; success_runs: int; fail_runs: int
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== 凭证 API ====================

@router.get("/credentials", summary="获取凭证列表")
def list_credentials(db: Session = Depends(get_db)):
    items = db.query(CollectorCredential).all()
    # 脱敏：不返回 credential_data 中的密码
    result = []
    for c in items:
        result.append({
            "id": c.id, "name": c.name, "credential_type": c.credential_type,
            "description": c.description, "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return APIResponse.success(data={"items": result, "total": len(result)})

@router.post("/credentials", status_code=201, summary="创建凭证")
def create_credential(data: CredentialCreate, db: Session = Depends(get_db)):
    cred = CollectorCredential(tenant_id=1, **data.model_dump())
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return APIResponse.success(message="凭证创建成功", code=201)


# ==================== 采集任务 API ====================

@router.get("/tasks", summary="获取采集任务列表")
def list_tasks(
    protocol: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(CollectorTask)
    if protocol:
        query = query.filter(CollectorTask.protocol == protocol)
    if is_active is not None:
        query = query.filter(CollectorTask.is_active == is_active)
    items = query.order_by(CollectorTask.priority.desc()).all()
    return APIResponse.success(data={
        "items": [TaskResponse.model_validate(t).model_dump() for t in items],
        "total": len(items),
    })

@router.post("/tasks", status_code=201, summary="创建采集任务")
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = CollectorTask(tenant_id=1, **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return APIResponse.success(data=TaskResponse.model_validate(task).model_dump(), code=201)

@router.post("/tasks/{task_id}/run", summary="手动触发采集任务")
def run_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(CollectorTask).filter(CollectorTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    # TODO: 通过 Celery 异步执行采集任务
    task.last_run_at = datetime.utcnow()
    task.last_run_status = "queued"
    task.total_runs += 1
    db.commit()
    return APIResponse.success(message="采集任务已加入队列")

@router.put("/tasks/{task_id}/toggle", summary="启用/禁用采集任务")
def toggle_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(CollectorTask).filter(CollectorTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    task.is_active = not task.is_active
    db.commit()
    return APIResponse.success(message=f"任务已{'启用' if task.is_active else '禁用'}")

@router.get("/tasks/{task_id}/logs", summary="获取任务执行日志")
def list_task_logs(task_id: int, limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(CollectorTaskLog).filter(
        CollectorTaskLog.task_id == task_id
    ).order_by(CollectorTaskLog.created_at.desc()).limit(limit).all()
    return APIResponse.success(data={
        "items": [{"id": l.id, "status": l.status, "duration_ms": l.duration_ms,
                    "success_count": l.success_count, "fail_count": l.fail_count,
                    "error_message": l.error_message,
                    "created_at": l.created_at.isoformat() if l.created_at else None} for l in logs],
        "total": len(logs),
    })
