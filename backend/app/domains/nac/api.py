"""
NAC 准入控制域 API。
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse
from app.domains.nac.models import NacPolicy, NacSession, NacAuthLog, VisitorAccount

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schema ====================

class PolicyCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: int = 100
    conditions: dict
    auth_method: str
    actions: dict

class PolicyResponse(BaseModel):
    id: int; name: str; priority: int; is_active: bool
    auth_method: Optional[str] = None; conditions: dict; actions: dict
    created_at: datetime
    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int; mac_address: str; ip_address: Optional[str] = None
    username: Optional[str] = None; auth_method: Optional[str] = None
    vlan_id: Optional[int] = None; switch_ip: Optional[str] = None
    switch_port: Optional[str] = None; ssid: Optional[str] = None
    compliance_status: str; compliance_score: int
    session_start: datetime; is_active: bool
    class Config:
        from_attributes = True

class VisitorCreate(BaseModel):
    visitor_name: str
    visitor_company: Optional[str] = None
    visitor_phone: Optional[str] = None
    sponsor_name: Optional[str] = None
    access_level: str = "internet_only"
    duration_hours: int = Field(24, ge=1, le=720)


# ==================== 策略 API ====================

@router.get("/policies", summary="获取认证策略列表")
def list_policies(db: Session = Depends(get_db)):
    items = db.query(NacPolicy).order_by(NacPolicy.priority).all()
    return APIResponse.success(data={
        "items": [PolicyResponse.model_validate(p).model_dump() for p in items],
        "total": len(items),
    })

@router.post("/policies", status_code=201, summary="创建认证策略")
def create_policy(data: PolicyCreate, db: Session = Depends(get_db)):
    policy = NacPolicy(tenant_id=1, **data.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return APIResponse.success(data=PolicyResponse.model_validate(policy).model_dump(), code=201)


# ==================== 会话 API ====================

@router.get("/sessions", summary="获取在线终端会话")
def list_sessions(
    is_active: bool = True,
    compliance: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(NacSession).filter(NacSession.is_active == is_active)
    if compliance:
        query = query.filter(NacSession.compliance_status == compliance)
    if search:
        query = query.filter(
            (NacSession.mac_address.contains(search)) |
            (NacSession.ip_address.contains(search)) |
            (NacSession.username.contains(search))
        )
    items = query.order_by(NacSession.session_start.desc()).all()
    return APIResponse.success(data={
        "items": [SessionResponse.model_validate(s).model_dump() for s in items],
        "total": len(items),
        "online_count": len([s for s in items if s.is_active]),
    })

@router.post("/sessions/{session_id}/disconnect", summary="强制断开终端")
def disconnect_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(NacSession).filter(NacSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "会话不存在")
    session.is_active = False
    db.commit()
    return APIResponse.success(message="终端已断开")


# ==================== 认证日志 API ====================

@router.get("/auth-logs", summary="获取认证日志")
def list_auth_logs(
    result: Optional[str] = None,
    mac: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(NacAuthLog)
    if result:
        query = query.filter(NacAuthLog.result == result)
    if mac:
        query = query.filter(NacAuthLog.mac_address.contains(mac))
    items = query.order_by(NacAuthLog.created_at.desc()).limit(limit).all()
    total = query.count()
    return APIResponse.success(data={
        "items": [{
            "id": l.id, "mac_address": l.mac_address, "ip_address": l.ip_address,
            "username": l.username, "auth_method": l.auth_method, "result": l.result,
            "failure_reason": l.failure_reason, "switch_ip": l.switch_ip,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        } for l in items],
        "total": total,
    })


# ==================== 访客 API ====================

@router.get("/visitors", summary="获取访客账号列表")
def list_visitors(is_active: bool = True, db: Session = Depends(get_db)):
    query = db.query(VisitorAccount).filter(VisitorAccount.is_active == is_active)
    items = query.order_by(VisitorAccount.created_at.desc()).all()
    return APIResponse.success(data={
        "items": [{
            "id": v.id, "visitor_name": v.visitor_name, "visitor_company": v.visitor_company,
            "username": v.username, "access_level": v.access_level,
            "sponsor_name": v.sponsor_name, "valid_until": v.valid_until.isoformat() if v.valid_until else None,
            "is_active": v.is_active,
        } for v in items],
        "total": len(items),
    })

@router.post("/visitors", status_code=201, summary="创建访客账号")
def create_visitor(data: VisitorCreate, db: Session = Depends(get_db)):
    import secrets
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    username = f"visitor_{secrets.token_hex(4)}"
    password = secrets.token_urlsafe(8)

    visitor = VisitorAccount(
        tenant_id=1,
        visitor_name=data.visitor_name,
        visitor_company=data.visitor_company,
        visitor_phone=data.visitor_phone,
        username=username,
        password_hash=pwd_context.hash(password),
        sponsor_name=data.sponsor_name,
        access_level=data.access_level,
        valid_until=datetime.utcnow() + timedelta(hours=data.duration_hours),
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    return APIResponse.success(data={
        "id": visitor.id, "username": username, "password": password,
        "valid_until": visitor.valid_until.isoformat(),
    }, code=201, message="访客账号创建成功")
