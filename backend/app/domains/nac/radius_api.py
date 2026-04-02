"""
RADIUS 管理 API。

管理 FreeRADIUS 的用户、NAS 设备、MAC 白名单。
FreeRADIUS 通过 SQL 模块直接读取这些表做认证，
IPAM 后端通过这些 API 管理数据。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schema ====================

class RadiusUserCreate(BaseModel):
    username: str = Field(..., max_length=100)
    password: str = Field(..., min_length=4)
    user_type: str = "employee"
    real_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    vlan_id: Optional[int] = None
    acl_name: Optional[str] = None
    bandwidth_up: Optional[int] = None
    bandwidth_down: Optional[int] = None
    expire_at: Optional[str] = None

class MacAuthCreate(BaseModel):
    mac_address: str = Field(..., max_length=17, description="格式 AA:BB:CC:DD:EE:FF")
    device_name: Optional[str] = None
    device_type: str = "other"
    location: Optional[str] = None
    vlan_id: Optional[int] = None
    acl_name: Optional[str] = None

class NasDeviceCreate(BaseModel):
    name: str = Field(..., max_length=200)
    ip_address: str = Field(..., max_length=45)
    secret: str = Field(..., min_length=6)
    nas_type: str = "huawei"
    description: Optional[str] = None


# ==================== RADIUS 用户管理 ====================

@router.get("/radius/users", summary="获取 RADIUS 用户列表")
def list_radius_users(
    user_type: Optional[str] = None,
    search: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
):
    sql = "SELECT * FROM radius_users WHERE is_active = :active"
    params = {"active": is_active}
    if user_type:
        sql += " AND user_type = :utype"
        params["utype"] = user_type
    if search:
        sql += " AND (username LIKE :s OR real_name LIKE :s)"
        params["s"] = f"%{search}%"
    sql += " ORDER BY created_at DESC"

    result = db.execute(text(sql), params)
    items = [dict(row._mapping) for row in result]
    # 脱敏：不返回密码
    for item in items:
        item.pop("password", None)
        for k, v in item.items():
            if isinstance(v, datetime):
                item[k] = v.isoformat()

    return APIResponse.success(data={"items": items, "total": len(items)})


@router.post("/radius/users", status_code=201, summary="创建 RADIUS 用户")
def create_radius_user(data: RadiusUserCreate, db: Session = Depends(get_db)):
    # 检查用户名唯一
    existing = db.execute(text("SELECT id FROM radius_users WHERE username = :u"), {"u": data.username}).first()
    if existing:
        raise HTTPException(409, f"用户名 '{data.username}' 已存在")

    db.execute(text("""
        INSERT INTO radius_users (username, password, user_type, real_name, department, phone, vlan_id, acl_name, bandwidth_up, bandwidth_down, expire_at)
        VALUES (:username, :password, :user_type, :real_name, :department, :phone, :vlan_id, :acl_name, :bw_up, :bw_down, :expire_at)
    """), {
        "username": data.username, "password": data.password, "user_type": data.user_type,
        "real_name": data.real_name, "department": data.department, "phone": data.phone,
        "vlan_id": data.vlan_id, "acl_name": data.acl_name,
        "bw_up": data.bandwidth_up, "bw_down": data.bandwidth_down,
        "expire_at": data.expire_at,
    })

    # 自动创建 RADIUS 回复属性（VLAN 下发）
    if data.vlan_id:
        for attr, val in [
            ("Tunnel-Type", "VLAN"),
            ("Tunnel-Medium-Type", "IEEE-802"),
            ("Tunnel-Private-Group-Id", str(data.vlan_id)),
        ]:
            db.execute(text("""
                INSERT INTO radius_reply (username, attribute, op, value)
                VALUES (:u, :attr, ':=', :val)
            """), {"u": data.username, "attr": attr, "val": val})

    db.commit()
    logger.info(f"RADIUS 用户创建: {data.username} VLAN={data.vlan_id}")
    return APIResponse.success(message=f"RADIUS 用户 '{data.username}' 创建成功", code=201)


@router.delete("/radius/users/{username}", summary="禁用 RADIUS 用户")
def disable_radius_user(username: str, db: Session = Depends(get_db)):
    db.execute(text("UPDATE radius_users SET is_active = 0 WHERE username = :u"), {"u": username})
    db.execute(text("UPDATE radius_reply SET is_active = 0 WHERE username = :u"), {"u": username})
    db.commit()
    return APIResponse.success(message=f"用户 '{username}' 已禁用")


# ==================== MAC 白名单管理 ====================

@router.get("/radius/mac-auth", summary="获取 MAC 白名单")
def list_mac_auth(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM radius_mac_auth WHERE is_active = 1 ORDER BY created_at DESC"))
    items = [dict(row._mapping) for row in result]
    for item in items:
        for k, v in item.items():
            if isinstance(v, datetime):
                item[k] = v.isoformat()
    return APIResponse.success(data={"items": items, "total": len(items)})


@router.post("/radius/mac-auth", status_code=201, summary="添加 MAC 白名单")
def add_mac_auth(data: MacAuthCreate, db: Session = Depends(get_db)):
    mac = data.mac_address.upper().replace("-", ":")
    existing = db.execute(text("SELECT id FROM radius_mac_auth WHERE mac_address = :m"), {"m": mac}).first()
    if existing:
        raise HTTPException(409, f"MAC {mac} 已存在")

    db.execute(text("""
        INSERT INTO radius_mac_auth (mac_address, device_name, device_type, location, vlan_id, acl_name)
        VALUES (:mac, :name, :dtype, :loc, :vlan, :acl)
    """), {"mac": mac, "name": data.device_name, "dtype": data.device_type,
           "loc": data.location, "vlan": data.vlan_id, "acl": data.acl_name})
    db.commit()
    return APIResponse.success(message=f"MAC {mac} 已添加到白名单", code=201)


# ==================== NAS 设备管理 ====================

@router.get("/radius/nas", summary="获取 NAS 设备列表")
def list_nas_devices(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM radius_nas_devices WHERE is_active = 1 ORDER BY created_at DESC"))
    items = [dict(row._mapping) for row in result]
    # 脱敏：secret 只显示前 4 位
    for item in items:
        if item.get("secret"):
            item["secret"] = item["secret"][:4] + "****"
        for k, v in item.items():
            if isinstance(v, datetime):
                item[k] = v.isoformat()
    return APIResponse.success(data={"items": items, "total": len(items)})


@router.post("/radius/nas", status_code=201, summary="注册 NAS 设备")
def register_nas(data: NasDeviceCreate, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT id FROM radius_nas_devices WHERE ip_address = :ip"), {"ip": data.ip_address}).first()
    if existing:
        raise HTTPException(409, f"NAS 设备 {data.ip_address} 已注册")

    db.execute(text("""
        INSERT INTO radius_nas_devices (name, ip_address, secret, nas_type, description)
        VALUES (:name, :ip, :secret, :nas_type, :desc)
    """), {"name": data.name, "ip": data.ip_address, "secret": data.secret,
           "nas_type": data.nas_type, "desc": data.description})
    db.commit()

    # TODO: 自动更新 FreeRADIUS clients.conf 并重启容器
    logger.info(f"NAS 设备注册: {data.name} ({data.ip_address})")
    return APIResponse.success(message=f"NAS 设备 '{data.name}' 注册成功。请重启 FreeRADIUS 容器生效。", code=201)


# ==================== 认证日志 ====================

@router.get("/radius/auth-logs", summary="获取 RADIUS 认证日志")
def list_radius_auth_logs(
    username: Optional[str] = None,
    result_filter: Optional[str] = Query(None, alias="result"),
    limit: int = 100,
    db: Session = Depends(get_db),
):
    sql = "SELECT * FROM radius_auth_log WHERE 1=1"
    params = {}
    if username:
        sql += " AND username LIKE :u"
        params["u"] = f"%{username}%"
    if result_filter:
        sql += " AND auth_result = :r"
        params["r"] = result_filter
    sql += " ORDER BY auth_time DESC LIMIT :lim"
    params["lim"] = limit

    result = db.execute(text(sql), params)
    items = [dict(row._mapping) for row in result]
    for item in items:
        for k, v in item.items():
            if isinstance(v, datetime):
                item[k] = v.isoformat()
    return APIResponse.success(data={"items": items, "total": len(items)})


# ==================== 在线会话 ====================

@router.get("/radius/sessions", summary="获取 RADIUS 在线会话")
def list_radius_sessions(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT * FROM radius_accounting
        WHERE status = 'start' AND stop_time IS NULL
        ORDER BY start_time DESC
    """))
    items = [dict(row._mapping) for row in result]
    for item in items:
        for k, v in item.items():
            if isinstance(v, datetime):
                item[k] = v.isoformat()
    return APIResponse.success(data={"items": items, "total": len(items)})
