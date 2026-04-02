"""
变更窗口管理 API（需求 65）。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class ChangeWindowCreate(BaseModel):
    title: str = Field(..., max_length=200)
    start_time: str
    end_time: str
    scope: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None


@router.get("/change-windows", summary="变更窗口列表")
def list_change_windows(db: Session = Depends(get_db)):
    try:
        r = db.execute(text("SELECT * FROM change_windows ORDER BY start_time DESC"))
        items = [dict(row._mapping) for row in r]
        for item in items:
            for k, v in item.items():
                if isinstance(v, datetime):
                    item[k] = v.isoformat()
    except Exception:
        items = []
    return APIResponse.success(data={"items": items, "total": len(items)})


@router.post("/change-windows", status_code=201, summary="创建变更窗口")
def create_change_window(data: ChangeWindowCreate, db: Session = Depends(get_db)):
    db.execute(text("""
        INSERT INTO change_windows (title, start_time, end_time, scope, owner, description, status)
        VALUES (:title, :start, :end, :scope, :owner, :desc, 'scheduled')
    """), {
        "title": data.title, "start": data.start_time, "end": data.end_time,
        "scope": data.scope, "owner": data.owner, "desc": data.description,
    })
    db.commit()
    return APIResponse.success(message="变更窗口创建成功", code=201)
