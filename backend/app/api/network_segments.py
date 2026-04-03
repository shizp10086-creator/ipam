"""
ι API - չ档

ܣ
- CIDR ֶ֧
- Ƕײѯ
- CRUD
- ǩɸѡǩ
- ǿɾģʽforce=true Զ IP
- ʹ
- ͳһ APIResponse ʽ
"""
import ipaddress as ip_module
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import APIResponse
from app.models.network_segment import NetworkSegment, SegmentGroup
from app.models.ip_address import IPAddress
from app.models.user import User
from app.schemas.network_segment import (
    NetworkSegmentCreate, NetworkSegmentUpdate, NetworkSegmentResponse,
    NetworkSegmentStatsResponse, SegmentGroupCreate, SegmentGroupResponse,
)
from app.services.log_service import LogService
from app.utils.ip_utils import validate_cidr, calculate_segment_ip_range, calculate_segment_usage
from app.api.deps import require_admin, get_client_ip

logger = logging.getLogger(__name__)
router = APIRouter()


# ====================  CRUD ====================

@router.get("", summary="ȡб")
async def list_segments(
    name: Optional[str] = Query(None, description="ģ"),
    group_id: Optional[int] = Query(None, description="ɸѡ"),
    parent_id: Optional[int] = Query(None, description="ɸѡǶף"),
    tags: Optional[str] = Query(None, description="ǩɸѡŷָǩ AND ϵ"),
    status_filter: Optional[str] = Query(None, alias="status", description="״̬ɸѡ"),
    usage_min: Optional[float] = Query(None, description="ʹСֵ"),
    usage_max: Optional[float] = Query(None, description="ʹֵ"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    sort_by: str = Query("created_at", description="ֶ"),
    sort_order: str = Query("desc", description="asc/desc"),
    include_stats: bool = Query(False, description="ǷͳϢ"),
    db: Session = Depends(get_db),
):
    query = db.query(NetworkSegment).filter(NetworkSegment.deleted_at.is_(None))

    if name:
        query = query.filter(NetworkSegment.name.contains(name))
    if group_id is not None:
        query = query.filter(NetworkSegment.group_id == group_id)
    if parent_id is not None:
        query = query.filter(NetworkSegment.parent_id == parent_id)
    if status_filter:
        query = query.filter(NetworkSegment.status == status_filter)
    if usage_min is not None:
        query = query.filter(NetworkSegment.usage_rate >= usage_min)
    if usage_max is not None:
        query = query.filter(NetworkSegment.usage_rate <= usage_max)

    # ǩɸѡǩ AND ϵ
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tag_list:
            query = query.filter(NetworkSegment.tags.contains(f'"{tag}"'))

    total = query.count()

    #
    if hasattr(NetworkSegment, sort_by):
        col = getattr(NetworkSegment, sort_by)
        query = query.order_by(col.desc() if sort_order == "desc" else col.asc())

    offset = (page - 1) * page_size
    segments = query.offset(offset).limit(page_size).all()

    if include_stats:
        items = []
        for s in segments:
            d = NetworkSegmentResponse.model_validate(s).model_dump()
            try:
                stats = calculate_segment_usage(db, s.id)
                d.update(stats)
            except Exception:
                pass
            items.append(d)
    else:
        items = [NetworkSegmentResponse.model_validate(s).model_dump() for s in segments]

    return APIResponse.success(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    })


@router.post("", status_code=status.HTTP_201_CREATED, summary="")
async def create_segment(
    data: NetworkSegmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    client_ip: Optional[str] = Depends(get_client_ip),
):
    #  CIDR
    network = ip_module.ip_network(data.cidr, strict=False)
    network_addr = str(network.network_address)
    broadcast_addr = str(network.broadcast_address)
    prefix_len = network.prefixlen
    total_hosts = max(network.num_addresses - 2, 0)  # ȥַ͹㲥ַ

    # ظ
    existing = db.query(NetworkSegment).filter(
        NetworkSegment.network == network_addr,
        NetworkSegment.prefix_length == prefix_len,
        NetworkSegment.deleted_at.is_(None),
    ).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, f" {data.cidr} Ѵ")

    # ǶУ
    if data.parent_id:
        parent = db.query(NetworkSegment).filter(NetworkSegment.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "β")
        parent_net = ip_module.ip_network(f"{parent.network}/{parent.prefix_length}", strict=False)
        if not network.subnet_of(parent_net):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f" {data.cidr} ڸ {parent.network}/{parent.prefix_length} Χ")

    segment = NetworkSegment(
        tenant_id=1,  # TODO: ⻧Ļȡ
        name=data.name,
        cidr=data.cidr,
        network=network_addr,
        broadcast=broadcast_addr,
        prefix_length=prefix_len,
        ip_version=network.version,
        gateway=data.gateway,
        description=data.description,
        company=data.company,
        business_group=data.business_group,
        parent_id=data.parent_id,
        group_id=data.group_id,
        tags=data.tags or [],
        custom_fields=data.custom_fields or {},
        total_ips=total_hosts,
        alert_threshold_warning=data.alert_threshold_warning,
        alert_threshold_critical=data.alert_threshold_critical,
        usage_threshold=data.alert_threshold_warning,
        created_by=current_user.id,
    )
    db.add(segment)
    db.commit()
    db.refresh(segment)

    #  IP ַ¼
    try:
        ips = [
            IPAddress(
                segment_id=segment.id,
                ip_address=str(ip),
                status="available",
                is_online=False,
            )
            for ip in network.hosts()
        ]
        if ips:
            db.bulk_save_objects(ips)
            db.commit()
    except Exception as e:
        logger.error(f"IP ʧ: {e}")
        db.rollback()

    # ¼־
    try:
        LogService.log_segment_operation(
            db=db, user_id=current_user.id, username=current_user.username,
            operation_type="create", segment_id=segment.id,
            segment_data={"name": segment.name, "cidr": data.cidr},
            client_ip=client_ip,
        )
    except Exception:
        pass

    logger.info(f"δɹ: {data.cidr} (ID={segment.id})")
    return APIResponse.success(
        data=NetworkSegmentResponse.model_validate(segment).model_dump(),
        code=201, message="δɹ",
    )


@router.get("/{segment_id}", summary="ȡ")
async def get_segment(segment_id: int, db: Session = Depends(get_db)):
    segment = db.query(NetworkSegment).filter(
        NetworkSegment.id == segment_id,
        NetworkSegment.deleted_at.is_(None),
    ).first()
    if not segment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "β")
    return APIResponse.success(data=NetworkSegmentResponse.model_validate(segment).model_dump())


@router.put("/{segment_id}", summary="")
async def update_segment(
    segment_id: int,
    data: NetworkSegmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    client_ip: Optional[str] = Depends(get_client_ip),
):
    segment = db.query(NetworkSegment).filter(
        NetworkSegment.id == segment_id,
        NetworkSegment.deleted_at.is_(None),
    ).first()
    if not segment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "β")

    # ֹУ
    if data.version != segment.version:
        raise HTTPException(status.HTTP_409_CONFLICT, "ѱ޸ģˢº")

    update_data = data.model_dump(exclude_unset=True, exclude={"version"})
    old_data = {k: getattr(segment, k) for k in update_data}

    for key, value in update_data.items():
        setattr(segment, key, value)
    segment.version += 1

    db.commit()
    db.refresh(segment)

    # ¼
    try:
        LogService.log_segment_operation(
            db=db, user_id=current_user.id, username=current_user.username,
            operation_type="update", segment_id=segment.id,
            segment_data={"old": old_data, "new": update_data},
            client_ip=client_ip,
        )
    except Exception:
        pass

    return APIResponse.success(data=NetworkSegmentResponse.model_validate(segment).model_dump())


@router.delete("/{segment_id}", summary="ɾ")
async def delete_segment(
    segment_id: int,
    force: bool = Query(False, description="ǿɾԶй IP"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    client_ip: Optional[str] = Depends(get_client_ip),
):
    segment = db.query(NetworkSegment).filter(
        NetworkSegment.id == segment_id,
        NetworkSegment.deleted_at.is_(None),
    ).first()
    if not segment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "β")

    allocated_count = db.query(IPAddress).filter(
        IPAddress.segment_id == segment_id,
        IPAddress.status.in_(["used", "reserved"]),
    ).count()

    if allocated_count > 0 and not force:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"ڴ {allocated_count} ѷ IP ַ޷ɾ"
            f"ǿɾʹ force=true ",
        )

    if force and allocated_count > 0:
        # ǿɾ IP
        db.query(IPAddress).filter(IPAddress.segment_id == segment_id).update(
            {"status": "available", "device_id": None}
        )
        logger.info(f"ǿɾ {segment.cidr}ѻ {allocated_count}  IP")

    # ɾ
    from datetime import datetime
    segment.deleted_at = datetime.now()
    db.commit()

    try:
        LogService.log_segment_operation(
            db=db, user_id=current_user.id, username=current_user.username,
            operation_type="delete", segment_id=segment.id,
            segment_data={"name": segment.name, "cidr": segment.cidr, "force": force},
            client_ip=client_ip,
        )
    except Exception:
        pass

    return APIResponse.success(message="ɾɹ")


@router.get("/{segment_id}/stats", summary="ȡͳϢ")
async def get_segment_stats(segment_id: int, db: Session = Depends(get_db)):
    segment = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "β")
    try:
        usage_stats = calculate_segment_usage(db, segment_id)
        range_info = calculate_segment_ip_range(segment.network, segment.prefix_length)
        return APIResponse.success(data={
            "segment_id": segment_id,
            **usage_stats,
            "network_info": range_info,
        })
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"ͳƼʧ: {e}")


@router.get("/{segment_id}/children", summary="ȡб")
async def get_children_segments(segment_id: int, db: Session = Depends(get_db)):
    """ȡָεֱ"""
    children = db.query(NetworkSegment).filter(
        NetworkSegment.parent_id == segment_id,
        NetworkSegment.deleted_at.is_(None),
    ).all()
    return APIResponse.success(data={
        "items": [NetworkSegmentResponse.model_validate(c).model_dump() for c in children],
        "total": len(children),
    })


# ==================== η CRUD ====================

@router.get("/groups/list", summary="ȡηб")
async def list_segment_groups(
    parent_id: Optional[int] = Query(None, description="ID"),
    db: Session = Depends(get_db),
):
    query = db.query(SegmentGroup)
    if parent_id is not None:
        query = query.filter(SegmentGroup.parent_id == parent_id)
    else:
        query = query.filter(SegmentGroup.parent_id.is_(None))  #
    groups = query.order_by(SegmentGroup.sort_order).all()
    return APIResponse.success(data={
        "items": [SegmentGroupResponse.model_validate(g).model_dump() for g in groups],
        "total": len(groups),
    })


@router.post("/groups", status_code=status.HTTP_201_CREATED, summary="η")
async def create_segment_group(
    data: SegmentGroupCreate,
    db: Session = Depends(get_db),
):
    group = SegmentGroup(
        tenant_id=1,  # TODO: ⻧Ļȡ
        name=data.name,
        parent_id=data.parent_id,
        description=data.description,
        sort_order=data.sort_order,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return APIResponse.success(
        data=SegmentGroupResponse.model_validate(group).model_dump(),
        code=201, message="鴴ɹ",
    )
