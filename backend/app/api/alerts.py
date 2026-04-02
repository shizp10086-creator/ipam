"""
Alert API Endpoints
告警管理相关的 API 端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import allow_readonly, require_user_or_admin
from app.models.user import User
from app.services.alert_service import AlertService
from app.schemas.alert import (
    AlertResponse,
    AlertListResponse,
    AlertResolveRequest,
    UsageStatsResponse,
    MonitorResultResponse
)
import math

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
def get_alerts(
    segment_id: Optional[int] = Query(None, description="网段 ID 筛选"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_readonly)
):
    skip = (page - 1) * page_size
    alerts, total = AlertService.get_alerts(
        db=db, segment_id=segment_id, is_resolved=is_resolved,
        skip=skip, limit=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return AlertListResponse(
        items=[AlertResponse.model_validate(alert) for alert in alerts],
        total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_readonly)
):
    alert = AlertService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)


@router.put("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin)
):
    success, message, alert = AlertService.resolve_alert_manually(db, alert_id)
    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)
    return AlertResponse.model_validate(alert)


@router.get("/segments/{segment_id}/usage", response_model=UsageStatsResponse)
def get_segment_usage(
    segment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_readonly)
):
    usage_stats = AlertService.calculate_segment_usage(db, segment_id)
    if not usage_stats:
        raise HTTPException(status_code=404, detail="Network segment not found")
    return UsageStatsResponse(**usage_stats)


@router.post("/monitor", response_model=MonitorResultResponse)
def monitor_all_segments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin)
):
    result = AlertService.monitor_all_segments(db)
    return MonitorResultResponse(**result)


@router.post("/segments/{segment_id}/check")
def check_segment_alert(
    segment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin)
):
    created, create_msg, alert = AlertService.check_and_create_alert(db, segment_id)
    if created:
        return {"action": "alert_created", "message": create_msg,
                "alert": AlertResponse.model_validate(alert)}
    resolved, resolve_msg, alert = AlertService.check_and_resolve_alert(db, segment_id)
    if resolved:
        return {"action": "alert_resolved", "message": resolve_msg,
                "alert": AlertResponse.model_validate(alert)}
    usage_stats = AlertService.calculate_segment_usage(db, segment_id)
    if not usage_stats:
        raise HTTPException(status_code=404, detail="Network segment not found")
    return {"action": "no_action", "message": "No alert action needed", "usage_stats": usage_stats}
