"""
Operation Log API Endpoints
提供操作日志的查询 API 接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.operation_log import OperationLog
from app.models.user import User
from app.schemas.operation_log import OperationLogResponse
from app.api.deps import allow_readonly

router = APIRouter()


@router.get("/", response_model=dict)
async def get_logs(
    user_id: Optional[int] = Query(None, description="按操作人 ID 筛选"),
    username: Optional[str] = Query(None, description="按操作人用户名筛选"),
    operation_type: Optional[str] = Query(None, description="按操作类型筛选"),
    resource_type: Optional[str] = Query(None, description="按资源类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_readonly)
):
    if operation_type:
        valid_types = ["create", "update", "delete", "allocate", "release"]
        if operation_type not in valid_types:
            raise HTTPException(status_code=400,
                detail=f"Invalid operation type. Must be one of: {', '.join(valid_types)}")

    if resource_type:
        valid_resources = ["ip", "device", "segment", "user"]
        if resource_type not in valid_resources:
            raise HTTPException(status_code=400,
                detail=f"Invalid resource type. Must be one of: {', '.join(valid_resources)}")

    query = db.query(OperationLog)
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if username:
        query = query.filter(OperationLog.username.like(f"%{username}%"))
    if operation_type:
        query = query.filter(OperationLog.operation_type == operation_type)
    if resource_type:
        query = query.filter(OperationLog.resource_type == resource_type)
    if start_date:
        query = query.filter(OperationLog.created_at >= start_date)
    if end_date:
        query = query.filter(OperationLog.created_at <= end_date)

    query = query.order_by(OperationLog.created_at.desc())
    total = query.count()
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size

    return {
        "code": 200, "message": "Success",
        "data": {
            "items": [OperationLogResponse.from_orm(log) for log in logs],
            "total": total, "page": page,
            "page_size": page_size, "total_pages": total_pages
        }
    }


@router.get("/{log_id}", response_model=dict)
async def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_readonly)
):
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Operation log not found")
    return {"code": 200, "message": "Success", "data": OperationLogResponse.from_orm(log)}
