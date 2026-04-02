"""
Dashboard API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import allow_readonly
from app.models.user import User
from app.services.statistics_service import get_statistics_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(current_user: User = Depends(allow_readonly), db: Session = Depends(get_db)):
    try:
        stats_service = get_statistics_service(db)
        return {"code": 200, "message": "Success", "data": stats_service.get_overview_stats()}
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")


@router.get("/charts")
async def get_dashboard_charts(days: int = Query(default=30, ge=1, le=365), current_user: User = Depends(allow_readonly), db: Session = Depends(get_db)):
    try:
        stats_service = get_statistics_service(db)
        return {
            "code": 200, "message": "Success",
            "data": {
                "segment_usage_distribution": stats_service.get_segment_usage_distribution(),
                "ip_status_distribution": stats_service.get_ip_status_distribution(),
                "device_statistics": stats_service.get_device_statistics(days=days)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard charts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard chart data")


@router.get("/recent-activities")
async def get_recent_activities(limit: int = Query(default=10, ge=1, le=50), current_user: User = Depends(allow_readonly), db: Session = Depends(get_db)):
    try:
        stats_service = get_statistics_service(db)
        return {"code": 200, "message": "Success", "data": stats_service.get_recent_activities(limit=limit)}
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent activities")


@router.get("/time-range-stats")
async def get_time_range_stats(start_date: Optional[datetime] = Query(default=None), end_date: Optional[datetime] = Query(default=None), current_user: User = Depends(allow_readonly), db: Session = Depends(get_db)):
    try:
        stats_service = get_statistics_service(db)
        return {"code": 200, "message": "Success", "data": stats_service.get_time_range_stats(start_date=start_date, end_date=end_date)}
    except Exception as e:
        logger.error(f"Error fetching time range stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch time range statistics")


@router.get("/segment-usage/{segment_id}")
async def get_segment_usage_detail(segment_id: int, current_user: User = Depends(allow_readonly), db: Session = Depends(get_db)):
    try:
        stats_service = get_statistics_service(db)
        all_segments = stats_service.get_segment_usage_distribution()
        segment_stats = next((s for s in all_segments if s["segment_id"] == segment_id), None)
        if not segment_stats:
            raise HTTPException(status_code=404, detail=f"Network segment {segment_id} not found")
        return {"code": 200, "message": "Success", "data": segment_stats}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching segment usage detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch segment usage detail")