"""
租户管理 API。

仅超级管理员可操作。
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import APIResponse
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", summary="获取租户列表")
def list_tenants(
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Tenant)
    if status_filter:
        query = query.filter(Tenant.status == status_filter)
    if search:
        query = query.filter(
            (Tenant.name.contains(search)) | (Tenant.code.contains(search))
        )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return APIResponse.success(data={
        "items": [TenantResponse.model_validate(t).model_dump() for t in items],
        "total": total,
    })


@router.post("", status_code=status.HTTP_201_CREATED, summary="创建租户")
def create_tenant(
    data: TenantCreate,
    db: Session = Depends(get_db),
):
    # 检查编码唯一性
    existing = db.query(Tenant).filter(Tenant.code == data.code).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, f"租户编码 '{data.code}' 已存在")

    tenant = Tenant(**data.model_dump(exclude_none=True))
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    logger.info(f"租户创建成功: {tenant.code}")
    return APIResponse.success(
        data=TenantResponse.model_validate(tenant).model_dump(),
        code=201,
        message="租户创建成功",
    )


@router.get("/{tenant_id}", summary="获取租户详情")
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "租户不存在")
    return APIResponse.success(data=TenantResponse.model_validate(tenant).model_dump())


@router.put("/{tenant_id}", summary="更新租户")
def update_tenant(
    tenant_id: int,
    data: TenantUpdate,
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "租户不存在")

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)
    db.commit()
    db.refresh(tenant)
    logger.info(f"租户更新成功: {tenant.code}")
    return APIResponse.success(data=TenantResponse.model_validate(tenant).model_dump())


@router.delete("/{tenant_id}", summary="删除租户")
def delete_tenant(tenant_id: int, db: Session = Depends(get_db)):
    if tenant_id == 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "默认租户不可删除")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "租户不存在")
    db.delete(tenant)
    db.commit()
    logger.info(f"租户删除成功: {tenant.code}")
    return APIResponse.success(message="租户删除成功")
