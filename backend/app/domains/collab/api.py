"""
运维协作域 API — 知识库、值班排班。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse
from app.domains.collab.models import KnowledgeArticle, DutySchedule

logger = logging.getLogger(__name__)
router = APIRouter()


class ArticleCreate(BaseModel):
    title: str = Field(..., max_length=300)
    content: str
    category: Optional[str] = None
    tags: Optional[list[str]] = []
    symptom: Optional[str] = None
    root_cause: Optional[str] = None
    solution: Optional[str] = None
    related_ips: Optional[list[str]] = []
    related_device_ids: Optional[list[int]] = []

class ArticleResponse(BaseModel):
    id: int; title: str; category: Optional[str]=None; tags: list=[]
    view_count: int=0; author_name: Optional[str]=None; status: str
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("/knowledge", summary="获取知识库文章列表")
def list_articles(
    category: Optional[str]=None, search: Optional[str]=None,
    skip: int=0, limit: int=20, db: Session=Depends(get_db),
):
    query = db.query(KnowledgeArticle).filter(KnowledgeArticle.status != "archived")
    if category:
        query = query.filter(KnowledgeArticle.category == category)
    if search:
        query = query.filter(
            (KnowledgeArticle.title.contains(search)) |
            (KnowledgeArticle.content.contains(search))
        )
    total = query.count()
    items = query.order_by(KnowledgeArticle.updated_at.desc()).offset(skip).limit(limit).all()
    return APIResponse.success(data={
        "items": [ArticleResponse.model_validate(a).model_dump() for a in items],
        "total": total,
    })

@router.post("/knowledge", status_code=201, summary="创建知识库文章")
def create_article(data: ArticleCreate, db: Session=Depends(get_db)):
    article = KnowledgeArticle(
        tenant_id=1, status="published", author_name="admin",
        **data.model_dump()
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return APIResponse.success(data=ArticleResponse.model_validate(article).model_dump(), code=201)

@router.get("/knowledge/{article_id}", summary="获取文章详情")
def get_article(article_id: int, db: Session=Depends(get_db)):
    a = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not a:
        raise HTTPException(404, "文章不存在")
    a.view_count += 1
    db.commit()
    return APIResponse.success(data={
        **ArticleResponse.model_validate(a).model_dump(),
        "content": a.content, "symptom": a.symptom,
        "root_cause": a.root_cause, "solution": a.solution,
        "related_ips": a.related_ips, "related_device_ids": a.related_device_ids,
    })


# ==================== 值班排班 ====================

@router.get("/duty", summary="获取值班排班")
def list_duty(month: Optional[str]=None, db: Session=Depends(get_db)):
    query = db.query(DutySchedule)
    if month:
        query = query.filter(DutySchedule.date.like(f"{month}%"))
    items = query.order_by(DutySchedule.date).all()
    return APIResponse.success(data={
        "items": [{"id": d.id, "date": d.date.isoformat() if d.date else None,
                    "shift": d.shift, "primary": d.primary_user_name,
                    "backup": d.backup_user_name, "confirmed": d.is_confirmed} for d in items],
        "total": len(items),
    })

@router.post("/duty", status_code=201, summary="创建值班记录")
def create_duty(date: str, primary_name: str, backup_name: str = None, shift: str = "all_day", db: Session=Depends(get_db)):
    d = DutySchedule(
        tenant_id=1, date=datetime.fromisoformat(date), shift=shift,
        primary_user_id=1, primary_user_name=primary_name,
        backup_user_name=backup_name,
    )
    db.add(d)
    db.commit()
    return APIResponse.success(message="值班记录创建成功", code=201)
