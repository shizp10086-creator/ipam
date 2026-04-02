"""
IP Address Management API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.core.database import get_db
from app.models.ip_address import IPAddress
from app.models.user import User
from app.schemas.ip_address import (
    IPAddressResponse, IPAddressUpdate, IPAllocateRequest, IPReleaseRequest,
    IPReserveRequest, IPConflictCheckRequest, IPConflictCheckResponse,
    IPScanRequest, ScanHistoryResponse, IPBatchUpdateStatusRequest
)
from app.services.ip_service import IPService
from app.services.log_service import LogService
from app.api.deps import require_user_or_admin, allow_readonly, get_client_ip

router = APIRouter()


@router.get("/", response_model=dict)
async def get_ip_addresses(
    segment_id: Optional[int] = Query(None, description="按网段筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    device_id: Optional[int] = Query(None, description="按设备筛选"),
    is_online: Optional[bool] = Query(None, description="按在线状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db)
):
    if status and status not in ["available", "used", "reserved"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    query = db.query(IPAddress).options(
        joinedload(IPAddress.segment), joinedload(IPAddress.device)
    )
    if segment_id:
        query = query.filter(IPAddress.segment_id == segment_id)
    if status:
        query = query.filter(IPAddress.status == status)
    if device_id:
        query = query.filter(IPAddress.device_id == device_id)
    if is_online is not None:
        query = query.filter(IPAddress.is_online == is_online)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size

    return {
        "code": 200, "message": "Success",
        "data": {
            "items": [IPAddressResponse.from_orm(item) for item in items],
            "total": total, "page": page,
            "page_size": page_size, "total_pages": total_pages
        }
    }


@router.post("/allocate", response_model=dict)
async def allocate_ip(
    request: IPAllocateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    success, message, ip_address = IPService.allocate_ip(
        db=db, ip_address_str=request.ip_address, device_id=request.device_id,
        user_id=current_user.id, segment_id=request.segment_id, skip_conflict_check=False
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    try:
        LogService.log_ip_allocation(
            db=db, user_id=current_user.id, username=current_user.username,
            ip_address=request.ip_address, device_id=request.device_id,
            device_name=ip_address.device.name if ip_address.device else None,
            segment_id=ip_address.segment_id, client_ip=client_ip
        )
    except Exception:
        pass
    return {"code": 200, "message": message, "data": IPAddressResponse.from_orm(ip_address)}


@router.post("/release", response_model=dict)
async def release_ip(
    request: IPReleaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    success, message, ip_address = IPService.release_ip(
        db=db, ip_address_str=request.ip_address,
        ip_id=request.ip_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    try:
        LogService.log_ip_release(
            db=db, user_id=current_user.id, username=current_user.username,
            ip_address=ip_address.ip_address, ip_id=ip_address.id, client_ip=client_ip
        )
    except Exception:
        pass
    return {"code": 200, "message": message, "data": IPAddressResponse.from_orm(ip_address)}


@router.post("/reserve", response_model=dict)
async def reserve_ip(request: IPReserveRequest, db: Session = Depends(get_db)):
    success, message, ip_address = IPService.reserve_ip(
        db=db, ip_address_str=request.ip_address,
        ip_id=request.ip_id, reserve=request.reserve, user_id=1
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"code": 200, "message": message, "data": IPAddressResponse.from_orm(ip_address)}


@router.put("/batch/update-status", response_model=dict)
async def batch_update_ip_status(
    request: IPBatchUpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin)
):
    success_count, failed_count, failed_ips = 0, 0, []
    for ip_id in request.ip_ids:
        try:
            ip_address = db.query(IPAddress).filter(IPAddress.id == ip_id).first()
            if not ip_address:
                failed_count += 1
                failed_ips.append({"ip_id": ip_id, "reason": "IP address not found"})
                continue
            ip_address.status = request.status
            db.commit()
            success_count += 1
        except Exception as e:
            db.rollback()
            failed_count += 1
            failed_ips.append({"ip_id": ip_id, "reason": str(e)})
    return {
        "code": 200,
        "message": f"Batch update: {success_count} succeeded, {failed_count} failed",
        "data": {"success_count": success_count, "failed_count": failed_count, "failed_ips": failed_ips}
    }


@router.post("/check-conflict", response_model=dict)
async def check_ip_conflict(request: IPConflictCheckRequest, db: Session = Depends(get_db)):
    from app.services.conflict_detection import ConflictDetectionService
    result = await ConflictDetectionService.check_ip_conflict(
        db=db, ip_address=request.ip_address, check_ping=request.check_ping,
        check_arp=request.check_arp, ping_timeout=request.ping_timeout, arp_timeout=request.arp_timeout
    )
    response_data = IPConflictCheckResponse(
        has_conflict=result.has_conflict, conflict_type=result.conflict_type,
        message=result.message, details=result.details
    )
    return {"code": 200, "message": "Conflict check completed", "data": response_data.dict()}


@router.post("/scan", response_model=dict)
async def scan_network_segment(request: IPScanRequest, db: Session = Depends(get_db)):
    from app.models.network_segment import NetworkSegment
    from app.services.ping_scanner import PingScanner, ScanResultProcessor
    import time, os

    segment = db.query(NetworkSegment).filter(NetworkSegment.id == request.segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail=f"Network segment {request.segment_id} not found")

    scanner = PingScanner(
        timeout=request.timeout, max_concurrent=request.max_concurrent, ping_count=1,
        use_proxy=os.getenv('USE_PING_PROXY', 'false').lower() == 'true',
        proxy_url=os.getenv('PING_PROXY_URL', 'http://host.docker.internal:8001'),
        source_ip=os.getenv('PING_SOURCE_IP')
    )
    start_time = time.time()
    try:
        scan_results = await scanner.scan_network_segment(
            network=segment.network, prefix_length=segment.prefix_length,
            exclude_network_broadcast=True
        )
        result = await ScanResultProcessor.process_scan_results(
            db=db, segment_id=request.segment_id, scan_results=scan_results,
            scan_duration=time.time() - start_time, user_id=1, scan_type=request.scan_type
        )
        return {"code": 200, "message": "Scan completed successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/scan-history", response_model=dict)
async def get_scan_history(
    segment_id: Optional[int] = Query(None),
    scan_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    from app.models.scan_history import ScanHistory
    if scan_type and scan_type not in ["ping", "arp"]:
        raise HTTPException(status_code=400, detail="Invalid scan type")

    query = db.query(ScanHistory).options(
        joinedload(ScanHistory.segment)
    ).order_by(ScanHistory.created_at.desc())
    if segment_id:
        query = query.filter(ScanHistory.segment_id == segment_id)
    if scan_type:
        query = query.filter(ScanHistory.scan_type == scan_type)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size

    items_data = []
    for item in items:
        item_dict = ScanHistoryResponse.from_orm(item).dict()
        if hasattr(item, 'segment') and item.segment:
            item_dict['segment'] = {
                'id': item.segment.id, 'name': item.segment.name,
                'network': item.segment.network, 'prefix_length': item.segment.prefix_length
            }
        items_data.append(item_dict)

    return {
        "code": 200, "message": "Success",
        "data": {"items": items_data, "total": total, "page": page,
                 "page_size": page_size, "total_pages": total_pages}
    }


@router.get("/scan-history/{scan_id}", response_model=dict)
async def get_scan_history_detail(scan_id: int, db: Session = Depends(get_db)):
    from app.models.scan_history import ScanHistory
    import json
    scan_history = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
    if not scan_history:
        raise HTTPException(status_code=404, detail="Scan history not found")
    results = None
    if scan_history.results:
        try:
            results = json.loads(scan_history.results)
        except Exception:
            pass
    return {
        "code": 200, "message": "Success",
        "data": {
            "id": scan_history.id, "segment_id": scan_history.segment_id,
            "scan_type": scan_history.scan_type, "total_ips": scan_history.total_ips,
            "online_ips": scan_history.online_ips, "duration": scan_history.duration,
            "created_by": scan_history.created_by, "created_at": scan_history.created_at,
            "results": results
        }
    }


@router.get("/{ip_id}", response_model=dict)
async def get_ip_address(ip_id: int, db: Session = Depends(get_db)):
    ip_address = db.query(IPAddress).options(
        joinedload(IPAddress.segment), joinedload(IPAddress.device)
    ).filter(IPAddress.id == ip_id).first()
    if not ip_address:
        raise HTTPException(status_code=404, detail="IP address not found")
    return {"code": 200, "message": "Success", "data": IPAddressResponse.from_orm(ip_address)}


@router.put("/{ip_id}", response_model=dict)
async def update_ip_address(ip_id: int, ip_update: IPAddressUpdate, db: Session = Depends(get_db)):
    ip_address = db.query(IPAddress).filter(IPAddress.id == ip_id).first()
    if not ip_address:
        raise HTTPException(status_code=404, detail="IP address not found")

    update_data = ip_update.dict(exclude_unset=True)
    if "status" in update_data and update_data["status"] not in ["available", "used", "reserved"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    for field, value in update_data.items():
        setattr(ip_address, field, value)
    try:
        db.commit()
        db.refresh(ip_address)
        return {"code": 200, "message": "IP address updated successfully",
                "data": IPAddressResponse.from_orm(ip_address)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update IP address: {str(e)}")
