"""
终端管理 API。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse
from app.domains.asset.terminal_models import Terminal, TerminalGroup

logger = logging.getLogger(__name__)
router = APIRouter()


class TerminalResponse(BaseModel):
    id: int; hostname: Optional[str] = None; ip_address: Optional[str] = None
    mac_address: Optional[str] = None; terminal_type: str
    os_type: Optional[str] = None; manufacturer: Optional[str] = None
    user_name: Optional[str] = None; user_department: Optional[str] = None
    status: str; is_online: bool; compliance_score: int
    compliance_status: str; approval_status: str
    tags: Optional[list] = []; created_at: datetime
    class Config:
        from_attributes = True


@router.get("/terminals", summary="获取终端列表")
def list_terminals(
    terminal_type: Optional[str] = None,
    status: Optional[str] = None,
    is_online: Optional[bool] = None,
    compliance: Optional[str] = None,
    approval: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Terminal)
    if terminal_type:
        query = query.filter(Terminal.terminal_type == terminal_type)
    if status:
        query = query.filter(Terminal.status == status)
    if is_online is not None:
        query = query.filter(Terminal.is_online == is_online)
    if compliance:
        query = query.filter(Terminal.compliance_status == compliance)
    if approval:
        query = query.filter(Terminal.approval_status == approval)
    if search:
        query = query.filter(
            (Terminal.hostname.contains(search)) |
            (Terminal.ip_address.contains(search)) |
            (Terminal.mac_address.contains(search)) |
            (Terminal.user_name.contains(search))
        )
    total = query.count()
    items = query.order_by(Terminal.updated_at.desc()).offset(skip).limit(limit).all()

    # 统计
    online_count = db.query(Terminal).filter(Terminal.is_online == True).count()
    compliant_count = db.query(Terminal).filter(Terminal.compliance_status == "compliant").count()
    all_count = db.query(Terminal).count()

    return APIResponse.success(data={
        "items": [TerminalResponse.model_validate(t).model_dump() for t in items],
        "total": total,
        "stats": {
            "total": all_count,
            "online": online_count,
            "offline": all_count - online_count,
            "compliant": compliant_count,
            "online_rate": round((online_count / all_count * 100), 1) if all_count > 0 else 0,
            "compliance_rate": round((compliant_count / all_count * 100), 1) if all_count > 0 else 0,
        }
    })


@router.get("/terminals/{terminal_id}", summary="获取终端画像")
def get_terminal_profile(terminal_id: int, db: Session = Depends(get_db)):
    t = db.query(Terminal).filter(Terminal.id == terminal_id).first()
    if not t:
        raise HTTPException(404, "终端不存在")
    return APIResponse.success(data={
        "basic": {
            "hostname": t.hostname, "ip_address": t.ip_address, "mac_address": t.mac_address,
            "terminal_type": t.terminal_type, "os_type": t.os_type, "os_version": t.os_version,
            "manufacturer": t.manufacturer, "model": t.model,
        },
        "hardware": {"cpu": t.cpu_info, "memory_gb": float(t.memory_gb) if t.memory_gb else None, "disk_gb": float(t.disk_gb) if t.disk_gb else None},
        "network": {"switch_ip": t.switch_ip, "switch_port": t.switch_port, "vlan_id": t.vlan_id},
        "user": {"name": t.user_name, "department": t.user_department},
        "security": {
            "compliance_score": t.compliance_score, "compliance_status": t.compliance_status,
            "antivirus": t.antivirus_installed, "antivirus_updated": t.antivirus_updated,
            "firewall": t.firewall_enabled, "os_patched": t.os_patched,
        },
        "status": {"is_online": t.is_online, "status": t.status, "approval": t.approval_status,
                    "last_online": t.last_online_at.isoformat() if t.last_online_at else None,
                    "offline_days": t.offline_days},
    })


@router.put("/terminals/{terminal_id}/approve", summary="审核终端（纳管/拉黑）")
def approve_terminal(terminal_id: int, action: str = Query(..., description="approved/blacklisted"), db: Session = Depends(get_db)):
    t = db.query(Terminal).filter(Terminal.id == terminal_id).first()
    if not t:
        raise HTTPException(404, "终端不存在")
    t.approval_status = action
    db.commit()
    return APIResponse.success(message=f"终端已{'纳管' if action == 'approved' else '拉黑'}")


# ==================== 终端分组 ====================

@router.get("/terminal-groups", summary="获取终端分组列表")
def list_groups(db: Session = Depends(get_db)):
    items = db.query(TerminalGroup).all()
    return APIResponse.success(data={
        "items": [{"id": g.id, "name": g.name, "group_type": g.group_type,
                    "terminal_count": g.terminal_count, "description": g.description} for g in items],
        "total": len(items),
    })

@router.post("/terminal-groups", status_code=201, summary="创建终端分组")
def create_group(name: str, group_type: str = "static", description: str = None, db: Session = Depends(get_db)):
    g = TerminalGroup(tenant_id=1, name=name, group_type=group_type, description=description)
    db.add(g)
    db.commit()
    db.refresh(g)
    return APIResponse.success(message="分组创建成功", code=201)
