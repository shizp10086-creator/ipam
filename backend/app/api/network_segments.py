"""
网段管理 API - 扩展版。

新增功能：
- CIDR 字段支持
- 子网嵌套查询
- 分组管理（CRUD）
- 标签筛选（多标签组合）
- 强制删除模式（force=true 自动回收所有 IP）
- 使用率排序
- 统一 APIResponse 格式
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


# ==================== 网段 CRUD ====================

@router.get("", summary="获取网段列表")
async def list_segments(
    name: Optional[str] = Query(None, description="按名称模糊搜索"),
    group_id: Optional[int] = Query(None, description="按分组筛选"),
    parent_id: Optional[int] = Query(None, description="按父网段筛选（子网嵌套）"),
    tags: Optional[str] = Query(None, description="按标签筛选（逗号分隔，多标签 AND 关系）"),
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    usage_min: Optional[float] = Query(None, description="使用率最小值"),
    usage_max: Optional[float] = Query(None, description="使用率最大值"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="asc/desc"),
    include_stats: bool = Query(False, description="是否包含统计信息"),
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

    # 标签筛选（多标签 AND 关系）
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tag_list:
            query = query.filter(NetworkSegment.tags.contains(f'"{tag}"'))

    total = query.count()

    # 排序
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


@router.post("", status_code=status.HTTP_201_CREATED, summary="创建网段")
async def create_segment(
    data: NetworkSegmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    client_ip: Optional[str] = Depends(get_client_ip),
):
    # 解析 CIDR
    network = ip_module.ip_network(data.cidr, strict=False)
    network_addr = str(network.network_address)
    broadcast_addr = str(network.broadcast_address)
    prefix_len = network.prefixlen
    total_hosts = max(network.num_addresses - 2, 0)  # 去掉网络地址和广播地址

    # 检查重复
    existing = db.query(NetworkSegment).filter(
        NetworkSegment.network == network_addr,
        NetworkSegment.prefix_length == prefix_len,
        NetworkSegment.deleted_at.is_(None),
    ).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, f"网段 {data.cidr} 已存在")

    # 子网嵌套校验
    if data.parent_id:
        parent = db.query(NetworkSegment).filter(NetworkSegment.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "父网段不存在")
        parent_net = ip_module.ip_network(f"{parent.network}/{parent.prefix_length}", strict=False)
        if not network.subnet_of(parent_net):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"子网 {data.cidr} 不在父网段 {parent.network}/{parent.prefix_length} 范围内")

    segment = NetworkSegment(
        tenant_id=1,  # TODO: 从租户上下文获取
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

    # 批量生成 IP 地址记录
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
        logger.error(f"IP 批量生成失败: {e}")
        db.rollback()

    # 记录操作日志
    try:
        LogService.log_segment_operation(
            db=db, user_id=current_user.id, username=current_user.username,
            operation_type="create", segment_id=segment.id,
            segment_data={"name": segment.name, "cidr": data.cidr},
            client_ip=client_ip,
        )
    except Exception:
        pass

    logger.info(f"网段创建成功: {data.cidr} (ID={segment.id})")
    return APIResponse.success(
        data=NetworkSegmentResponse.model_validate(segment).model_dump(),
        code=201, message="网段创建成功",
    )


@router.get("/{segment_id}", summary="获取网段详情")
async def get_segment(segment_id: int, db: Session = Depends(get_db)):
    segment = db.query(NetworkSegment).filter(
        NetworkSegment.id == segment_id,
        NetworkSegment.deleted_at.is_(None),
    ).first()
    if not segment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "网段不存在")
    return APIResponse.success(data=NetworkSegmentResponse.model_validate(segment).model_dump())


@router.put("/{segment_id}", summary="更新网段")
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
        raise HTTPException(status.HTTP_404_NOT_FOUND, "网段不存在")

    # 乐观锁校验
    if data.version != segment.version:
        raise HTTPException(status.HTTP_409_CONFLICT, "数据已被其他人修改，请刷新后重试")

    update_data = data.model_dump(exclude_unset=True, exclude={"version"})
    old_data = {k: getattr(segment, k) for k in update_data}

    for key, value in update_data.items():
        setattr(segment, key, value)
    segment.version += 1

    db.commit()
    db.refresh(segment)

    # 记录变更差异
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


@router.delete("/{segment_id}", summary="删除网段")
async def delete_segment(
    segment_id: int,
    force: bool = Query(False, description="强制删除（自动回收所有关联 IP）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    client_ip: Optional[str] = Depends(get_client_ip),
):
    segment = db.query(NetworkSegment).filter(
        NetworkSegment.id == segment_id,
        NetworkSegment.deleted_at.is_(None),
    ).first()
    if not segment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "网段不存在")

    allocated_count = db.query(IPAddress).filter(
        IPAddress.segment_id == segment_id,
        IPAddress.status.in_(["used", "reserved"]),
    ).count()

    if allocated_count > 0 and not force:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"网段内存在 {allocated_count} 个已分配的 IP 地址，无法正常删除。"
            f"如需强制删除请使用 force=true 参数",
        )

    if force and allocated_count > 0:
        # 强制删除：回收所有 IP
        db.query(IPAddress).filter(IPAddress.segment_id == segment_id).update(
            {"status": "available", "device_id": None}
        )
        logger.info(f"强制删除网段 {segment.cidr}，已回收 {allocated_count} 个 IP")

    # 软删除
    from datetime import datetime
    segment.deleted_at = datetime.utcnow()
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

    return APIResponse.success(message="网段删除成功")


@router.get("/{segment_id}/stats", summary="获取网段统计信息")
async def get_segment_stats(segment_id: int, db: Session = Depends(get_db)):
    segment = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "网段不存在")
    try:
        usage_stats = calculate_segment_usage(db, segment_id)
        range_info = calculate_segment_ip_range(segment.network, segment.prefix_length)
        return APIResponse.success(data={
            "segment_id": segment_id,
            **usage_stats,
            "network_info": range_info,
        })
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"统计计算失败: {e}")


@router.get("/{segment_id}/children", summary="获取子网列表")
async def get_children_segments(segment_id: int, db: Session = Depends(get_db)):
    """获取指定网段的所有直接子网。"""
    children = db.query(NetworkSegment).filter(
        NetworkSegment.parent_id == segment_id,
        NetworkSegment.deleted_at.is_(None),
    ).all()
    return APIResponse.success(data={
        "items": [NetworkSegmentResponse.model_validate(c).model_dump() for c in children],
        "total": len(children),
    })


# ==================== 网段分组 CRUD ====================

@router.get("/groups/list", summary="获取网段分组列表")
async def list_segment_groups(
    parent_id: Optional[int] = Query(None, description="父分组ID"),
    db: Session = Depends(get_db),
):
    query = db.query(SegmentGroup)
    if parent_id is not None:
        query = query.filter(SegmentGroup.parent_id == parent_id)
    else:
        query = query.filter(SegmentGroup.parent_id.is_(None))  # 顶级分组
    groups = query.order_by(SegmentGroup.sort_order).all()
    return APIResponse.success(data={
        "items": [SegmentGroupResponse.model_validate(g).model_dump() for g in groups],
        "total": len(groups),
    })


@router.post("/groups", status_code=status.HTTP_201_CREATED, summary="创建网段分组")
async def create_segment_group(
    data: SegmentGroupCreate,
    db: Session = Depends(get_db),
):
    group = SegmentGroup(
        tenant_id=1,  # TODO: 从租户上下文获取
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
        code=201, message="分组创建成功",
    )
