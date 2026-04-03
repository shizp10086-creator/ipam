"""
Global Search API
全局搜索功能
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.core.database import get_db
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress
from app.models.device import Device
from app.api.deps import allow_readonly

router = APIRouter()


@router.get("/", dependencies=[Depends(allow_readonly)])
async def global_search(
    q: str = Query(..., min_length=1, description="search keyword"),
    limit: int = Query(10, ge=1, le=50, description="max results per category"),
    db: Session = Depends(get_db)
):
    """
    全局搜索

    在网段、IP 地址和设备中搜索匹配的记?

    - **q**: 搜索关键词（必填?
    - **limit**: 每个类别返回的最大结果数（默?10?

    返回格式?
    ```json
    {
        "segments": [...],
        "ips": [...],
        "devices": [...],
        "total": 总结果数
    }
    ```
    """
    search_term = f"%{q}%"

    # 搜索网段
    segments = db.query(NetworkSegment).filter(
        or_(
            NetworkSegment.name.like(search_term),
            NetworkSegment.network.like(search_term),
            NetworkSegment.description.like(search_term)
        )
    ).limit(limit).all()

    # 搜索 IP 地址
    ips = db.query(IPAddress).filter(
        IPAddress.ip_address.like(search_term)
    ).limit(limit).all()

    # 搜索设备
    devices = db.query(Device).filter(
        or_(
            Device.name.like(search_term),
            Device.mac_address.like(search_term),
            Device.owner.like(search_term),
            Device.location.like(search_term),
            Device.description.like(search_term)
        )
    ).limit(limit).all()

    # 格式化结?
    segment_results = []
    for segment in segments:
        segment_results.append({
            "id": segment.id,
            "type": "segment",
            "name": segment.name,
            "network": segment.network,
            "prefix_length": segment.prefix_length,
            "cidr": f"{segment.network}/{segment.prefix_length}",
            "description": segment.description,
            "created_at": segment.created_at.isoformat() if segment.created_at else None
        })

    ip_results = []
    for ip in ips:
        # 获取关联的网段信?
        segment = db.query(NetworkSegment).filter(
            NetworkSegment.id == ip.segment_id
        ).first()

        ip_results.append({
            "id": ip.id,
            "type": "ip",
            "ip_address": ip.ip_address,
            "status": ip.status,
            "segment_name": segment.name if segment else None,
            "segment_cidr": f"{segment.network}/{segment.prefix_length}" if segment else None,
            "device_id": ip.device_id,
            "is_online": ip.is_online
        })

    device_results = []
    for device in devices:
        device_results.append({
            "id": device.id,
            "type": "device",
            "name": device.name,
            "mac_address": device.mac_address,
            "device_type": device.device_type,
            "owner": device.owner,
            "location": device.location,
            "description": device.description
        })

    total = len(segment_results) + len(ip_results) + len(device_results)

    return {
        "code": 200,
        "message": "Success",
        "data": {
            "query": q,
            "segments": segment_results,
            "ips": ip_results,
            "devices": device_results,
            "total": total,
            "counts": {
                "segments": len(segment_results),
                "ips": len(ip_results),
                "devices": len(device_results)
            }
        }
    }
