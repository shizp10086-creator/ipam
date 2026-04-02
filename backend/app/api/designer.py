"""
设计器配置 API。

统一管理所有低代码设计器（表单/流程/报表/仪表盘/大屏/PPT/页面布局）的配置。
设计器产物以 JSON 格式存储，运行态渲染引擎读取 JSON 动态渲染页面。
"""
import logging
import secrets
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse
from app.models.designer_config import DesignerConfig, DesignerConfigVersion

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schema ====================

class DesignerConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    config_type: str = Field(..., description="form/workflow/report/dashboard/screen/ppt/page_layout")
    config_json: dict = Field(..., description="设计器定义 JSON")
    is_template: bool = False
    template_category: Optional[str] = None


class DesignerConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[dict] = None
    status: Optional[str] = None
    is_template: Optional[bool] = None
    template_category: Optional[str] = None
    change_note: Optional[str] = Field(None, description="版本备注")


class DesignerConfigResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: Optional[str] = None
    config_type: str
    config_json: dict
    status: str
    current_version: int
    is_template: bool
    template_category: Optional[str] = None
    use_count: int = 0
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== API ====================

@router.get("", summary="获取设计器配置列表")
def list_configs(
    config_type: Optional[str] = Query(None, description="按类型筛选"),
    status_filter: Optional[str] = Query(None, alias="status"),
    is_template: Optional[bool] = Query(None, description="只看模板"),
    template_category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(DesignerConfig)
    if config_type:
        query = query.filter(DesignerConfig.config_type == config_type)
    if status_filter:
        query = query.filter(DesignerConfig.status == status_filter)
    if is_template is not None:
        query = query.filter(DesignerConfig.is_template == is_template)
    if template_category:
        query = query.filter(DesignerConfig.template_category == template_category)
    if search:
        query = query.filter(DesignerConfig.name.contains(search))

    total = query.count()
    items = query.order_by(DesignerConfig.updated_at.desc()).offset(skip).limit(limit).all()
    return APIResponse.success(data={
        "items": [DesignerConfigResponse.model_validate(c).model_dump() for c in items],
        "total": total,
    })


@router.post("", status_code=201, summary="创建设计器配置")
def create_config(data: DesignerConfigCreate, db: Session = Depends(get_db)):
    config = DesignerConfig(
        tenant_id=1,
        name=data.name,
        description=data.description,
        config_type=data.config_type,
        config_json=data.config_json,
        is_template=data.is_template,
        template_category=data.template_category,
    )
    db.add(config)
    db.flush()

    # 创建初始版本
    version = DesignerConfigVersion(
        config_id=config.id,
        version=1,
        config_json=data.config_json,
        change_note="初始版本",
    )
    db.add(version)
    db.commit()
    db.refresh(config)

    return APIResponse.success(
        data=DesignerConfigResponse.model_validate(config).model_dump(),
        code=201, message="创建成功",
    )


@router.get("/{config_id}", summary="获取设计器配置详情")
def get_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(DesignerConfig).filter(DesignerConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    return APIResponse.success(data=DesignerConfigResponse.model_validate(config).model_dump())


@router.put("/{config_id}", summary="更新设计器配置（自动保存版本）")
def update_config(config_id: int, data: DesignerConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(DesignerConfig).filter(DesignerConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")

    update_data = data.model_dump(exclude_none=True, exclude={"change_note"})
    for key, value in update_data.items():
        setattr(config, key, value)

    # 如果 config_json 有变更，自动保存新版本
    if data.config_json is not None:
        config.current_version += 1
        version = DesignerConfigVersion(
            config_id=config.id,
            version=config.current_version,
            config_json=data.config_json,
            change_note=data.change_note or f"版本 {config.current_version}",
        )
        db.add(version)

    db.commit()
    db.refresh(config)
    return APIResponse.success(data=DesignerConfigResponse.model_validate(config).model_dump())


@router.post("/{config_id}/publish", summary="发布设计器配置")
def publish_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(DesignerConfig).filter(DesignerConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    config.status = "published"
    db.commit()
    return APIResponse.success(message="发布成功")


@router.get("/{config_id}/versions", summary="获取版本历史")
def list_versions(config_id: int, db: Session = Depends(get_db)):
    versions = db.query(DesignerConfigVersion).filter(
        DesignerConfigVersion.config_id == config_id
    ).order_by(DesignerConfigVersion.version.desc()).all()
    return APIResponse.success(data={
        "items": [{"id": v.id, "version": v.version, "change_note": v.change_note,
                    "created_at": v.created_at.isoformat() if v.created_at else None} for v in versions],
        "total": len(versions),
    })


@router.post("/{config_id}/share", summary="生成分享链接")
def share_config(config_id: int, password: Optional[str] = None, db: Session = Depends(get_db)):
    config = db.query(DesignerConfig).filter(DesignerConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    config.share_token = secrets.token_urlsafe(32)
    config.share_password = password
    db.commit()
    return APIResponse.success(data={"share_token": config.share_token})


@router.delete("/{config_id}", summary="删除设计器配置")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(DesignerConfig).filter(DesignerConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    db.delete(config)
    db.commit()
    return APIResponse.success(message="删除成功")
