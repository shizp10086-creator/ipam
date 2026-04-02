"""
Network Segment Management API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress
from app.models.user import User
from app.schemas.network_segment import (
    NetworkSegmentCreate, NetworkSegmentUpdate, NetworkSegmentResponse,
    NetworkSegmentStatsResponse
)
from app.services.log_service import LogService
from app.utils.ip_utils import validate_cidr, calculate_segment_ip_range, calculate_segment_usage
from app.api.deps import require_admin, get_client_ip

router = APIRouter()


@router.get("/", response_model=dict)
async def get_segments(
    name: Optional[str] = Query(None, description="search by name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    include_stats: bool = Query(False),
    db: Session = Depends(get_db)
):
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Sort order must be asc or desc")
    query = db.query(NetworkSegment)
    if name:
        query = query.filter(NetworkSegment.name.like(f"%{name}%"))
    total = query.count()
    if hasattr(NetworkSegment, sort_by):
        col = getattr(NetworkSegment, sort_by)
        query = query.order_by(col.desc() if sort_order == "desc" else col.asc())
    offset = (page - 1) * page_size
    segments = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size
    if include_stats:
        items = []
        for s in segments:
            d = NetworkSegmentResponse.from_orm(s).dict()
            try:
                d.update(calculate_segment_usage(db, s.id))
            except Exception:
                d.update({"total_ips":0,"used_ips":0,"available_ips":0,"reserved_ips":0,"online_ips":0,"offline_ips":0,"usage_rate":0.0})
            items.append(d)
    else:
        items = [NetworkSegmentResponse.from_orm(s) for s in segments]
    return {"code":200,"message":"Success","data":{"items":items,"total":total,"page":page,"page_size":page_size,"total_pages":total_pages}}


@router.post("/", response_model=dict)
async def create_segment(
    segment: NetworkSegmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    cidr = f"{segment.network}/{segment.prefix_length}"
    is_valid, error_msg, parsed = validate_cidr(cidr)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    existing = db.query(NetworkSegment).filter(
        NetworkSegment.network == segment.network,
        NetworkSegment.prefix_length == segment.prefix_length
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Network segment {cidr} already exists")
    try:
        db_segment = NetworkSegment(
            name=segment.name,
            company=getattr(segment, "company", None),
            network=segment.network,
            prefix_length=segment.prefix_length,
            gateway=segment.gateway,
            description=segment.description,
            usage_threshold=segment.usage_threshold,
            created_by=current_user.id
        )
        db.add(db_segment)
        db.commit()
        db.refresh(db_segment)
        try:
            import ipaddress as ip_module
            network = ip_module.ip_network(cidr, strict=False)
            ips = [IPAddress(segment_id=db_segment.id, ip_address=str(ip), status="available", is_online=False) for ip in network.hosts()]
            if ips:
                db.bulk_save_objects(ips)
                db.commit()
        except Exception as e:
            print(f"IP gen failed: {e}")
            db.rollback()
        try:
            LogService.log_segment_operation(db=db, user_id=current_user.id, username=current_user.username, operation_type="create", segment_id=db_segment.id, segment_data={"name":db_segment.name,"cidr":cidr}, client_ip=client_ip)
        except Exception:
            pass
        return {"code":201,"message":"Network segment created successfully","data":NetworkSegmentResponse.from_orm(db_segment)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create network segment: {str(e)}")


@router.get("/{segment_id}", response_model=dict)
async def get_segment(segment_id: int, db: Session = Depends(get_db)):
    segment = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Network segment not found")
    return {"code":200,"message":"Success","data":NetworkSegmentResponse.from_orm(segment)}


@router.put("/{segment_id}", response_model=dict)
async def update_segment(
    segment_id: int,
    segment_update: NetworkSegmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    segment = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Network segment not found")
    update_data = segment_update.dict(exclude_unset=True)
    try:
        for field, value in update_data.items():
            setattr(segment, field, value)
        db.commit()
        db.refresh(segment)
        return {"code":200,"message":"Network segment updated successfully","data":NetworkSegmentResponse.from_orm(segment)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update: {str(e)}")


@router.delete("/{segment_id}", response_model=dict)
async def delete_segment(
    segment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    segment = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Network segment not found")
    allocated = db.query(IPAddress).filter(IPAddress.segment_id == segment_id, IPAddress.status.in_(["used","reserved"])).count()
    if allocated > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete segment with {allocated} allocated IPs")
    try:
        db.delete(segment)
        db.commit()
        return {"code":200,"message":"Network segment deleted successfully","data":None}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@router.get("/{segment_id}/stats", response_model=dict)
async def get_segment_stats(segment_id: int, db: Session = Depends(get_db)):
    segment = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Network segment not found")
    try:
        usage_stats = calculate_segment_usage(db, segment_id)
        range_info = calculate_segment_ip_range(segment.network, segment.prefix_length)
        stats_response = NetworkSegmentStatsResponse(
            segment_id=segment_id,
            total_ips=usage_stats["total_ips"],
            used_ips=usage_stats["used_ips"],
            available_ips=usage_stats["available_ips"],
            reserved_ips=usage_stats["reserved_ips"],
            online_ips=usage_stats["online_ips"],
            offline_ips=usage_stats["offline_ips"],
            usage_rate=usage_stats["usage_rate"],
            network_info=range_info
        )
        return {"code":200,"message":"Success","data":stats_response.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate stats: {str(e)}")