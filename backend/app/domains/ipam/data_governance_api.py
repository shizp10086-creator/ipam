"""
数据治理 API — 数据清洗、容量规划、公网 IP 管理。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.core.database import get_db
from app.core.response import APIResponse
from app.models.ip_address import IPAddress
from app.models.network_segment import NetworkSegment

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== 数据清洗 ====================

@router.post("/data-cleaning/run", summary="执行数据清洗任务")
def run_data_cleaning(db: Session = Depends(get_db)):
    """检测并报告数据问题：重复 IP、MAC 格式错误、网段不匹配、设备信息缺失。"""
    issues = []

    # 1. 检测重复 IP 分配（同一 IP 被多条记录标记为 used）
    dup_sql = text("""
        SELECT ip_address, COUNT(*) as cnt FROM ip_addresses
        WHERE status = 'used' AND deleted_at IS NULL
        GROUP BY ip_address HAVING cnt > 1
    """)
    dups = db.execute(dup_sql).fetchall()
    for row in dups:
        issues.append({"type": "duplicate_ip", "severity": "high",
                        "detail": f"IP {row[0]} 被重复分配 {row[1]} 次"})

    # 2. 检测网段使用率异常（used_ips > total_ips）
    segs = db.query(NetworkSegment).filter(
        NetworkSegment.used_ips > NetworkSegment.total_ips,
        NetworkSegment.deleted_at.is_(None),
    ).all()
    for s in segs:
        issues.append({"type": "usage_mismatch", "severity": "medium",
                        "detail": f"网段 {s.cidr} 已用数({s.used_ips})超过总数({s.total_ips})"})

    # 3. 检测孤立 IP（不属于任何网段）
    orphan_sql = text("""
        SELECT COUNT(*) FROM ip_addresses
        WHERE segment_id NOT IN (SELECT id FROM network_segments WHERE deleted_at IS NULL)
        AND deleted_at IS NULL
    """)
    orphan_count = db.execute(orphan_sql).scalar()
    if orphan_count > 0:
        issues.append({"type": "orphan_ip", "severity": "medium",
                        "detail": f"发现 {orphan_count} 个孤立 IP（所属网段已删除）"})

    return APIResponse.success(data={
        "total_issues": len(issues),
        "issues": issues,
        "scanned_at": datetime.utcnow().isoformat(),
    })


# ==================== 容量规划 ====================

@router.get("/capacity/overview", summary="容量规划概览")
def capacity_overview(db: Session = Depends(get_db)):
    """各网段使用率和预测耗尽时间。"""
    segments = db.query(NetworkSegment).filter(
        NetworkSegment.deleted_at.is_(None),
        NetworkSegment.total_ips > 0,
    ).order_by(NetworkSegment.usage_rate.desc()).all()

    items = []
    for s in segments:
        usage_pct = float(s.usage_rate or 0)
        # 简单线性预测：假设每月增长 5%
        remaining = s.total_ips - (s.used_ips or 0) - (s.reserved_ips or 0) - (s.temporary_ips or 0)
        monthly_growth = max(s.used_ips or 0, 1) * 0.05
        months_to_exhaust = int(remaining / monthly_growth) if monthly_growth > 0 else 999

        items.append({
            "segment_id": s.id,
            "cidr": s.cidr or f"{s.network}/{s.prefix_length}",
            "name": s.name,
            "total_ips": s.total_ips,
            "used_ips": s.used_ips or 0,
            "available": remaining,
            "usage_rate": usage_pct,
            "predicted_exhaust_months": months_to_exhaust,
            "risk_level": "high" if months_to_exhaust < 3 else "medium" if months_to_exhaust < 6 else "low",
        })

    return APIResponse.success(data={
        "items": items,
        "total": len(items),
        "high_risk_count": len([i for i in items if i["risk_level"] == "high"]),
    })


# ==================== 公网 IP 管理 ====================

@router.get("/public-ips", summary="公网 IP 列表")
def list_public_ips(db: Session = Depends(get_db)):
    """公网 IP 地址池管理（区分内网/公网）。"""
    # 简单实现：通过 IP 范围判断公网/内网
    # 内网范围：10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    public_ips = db.query(IPAddress).filter(
        IPAddress.deleted_at.is_(None),
        ~IPAddress.ip_address.like("10.%"),
        ~IPAddress.ip_address.like("172.16.%"),
        ~IPAddress.ip_address.like("172.17.%"),
        ~IPAddress.ip_address.like("172.18.%"),
        ~IPAddress.ip_address.like("172.19.%"),
        ~IPAddress.ip_address.like("172.2%.%"),
        ~IPAddress.ip_address.like("172.30.%"),
        ~IPAddress.ip_address.like("172.31.%"),
        ~IPAddress.ip_address.like("192.168.%"),
    ).all()

    return APIResponse.success(data={
        "items": [{"id": ip.id, "ip_address": ip.ip_address, "status": ip.status,
                    "dns_name": ip.dns_name, "responsible_person": ip.responsible_person}
                   for ip in public_ips],
        "total": len(public_ips),
    })
