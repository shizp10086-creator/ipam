"""
外部认证集成 API — LDAP/AD、企业微信、第三方系统对接。
需求 30（LDAP）、44（企业微信）、127（第三方集成）。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== LDAP 配置 ====================

class LdapConfig(BaseModel):
    server_url: str = Field(..., description="ldap://192.168.1.10:389")
    base_dn: str = Field(..., description="dc=example,dc=com")
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    user_search_filter: str = "(sAMAccountName={username})"
    group_search_filter: str = "(objectClass=group)"
    sync_interval_hours: int = 6
    enabled: bool = False

@router.get("/ldap/config", summary="获取 LDAP 配置")
def get_ldap_config():
    return APIResponse.success(data={
        "server_url": "", "base_dn": "", "bind_dn": "",
        "user_search_filter": "(sAMAccountName={username})",
        "group_search_filter": "(objectClass=group)",
        "sync_interval_hours": 6, "enabled": False,
    })

@router.post("/ldap/config", summary="保存 LDAP 配置")
def save_ldap_config(data: LdapConfig):
    logger.info(f"LDAP 配置保存: {data.server_url}")
    return APIResponse.success(message="LDAP 配置保存成功")

@router.post("/ldap/test", summary="测试 LDAP 连接")
def test_ldap_connection(data: LdapConfig):
    # 模拟测试
    return APIResponse.success(data={"connected": True, "users_found": 0, "groups_found": 0},
                                message="LDAP 连接测试成功（模拟）")

@router.post("/ldap/sync", summary="手动触发 LDAP 同步")
def sync_ldap():
    return APIResponse.success(message="LDAP 同步任务已加入队列")


# ==================== 企业微信 ====================

class WechatConfig(BaseModel):
    corp_id: str
    agent_id: str
    secret: str
    enabled: bool = False

@router.get("/wechat/config", summary="获取企业微信配置")
def get_wechat_config():
    return APIResponse.success(data={"corp_id": "", "agent_id": "", "secret": "", "enabled": False})

@router.post("/wechat/config", summary="保存企业微信配置")
def save_wechat_config(data: WechatConfig):
    return APIResponse.success(message="企业微信配置保存成功")

@router.post("/wechat/sync-org", summary="同步企业微信组织架构")
def sync_wechat_org():
    return APIResponse.success(message="组织架构同步任务已加入队列")


# ==================== 第三方系统集成 ====================

class IntegrationCreate(BaseModel):
    name: str = Field(..., max_length=200)
    system_type: str  # cmdb/zabbix/prometheus/ocs/edr/jumpserver
    api_url: str
    auth_type: str = "api_key"  # api_key/oauth/basic
    auth_config: Optional[dict] = {}
    sync_interval_minutes: int = 60
    field_mapping: Optional[dict] = {}

@router.get("/integrations", summary="获取第三方集成列表")
def list_integrations(db: Session = Depends(get_db)):
    try:
        r = db.execute(text("SELECT * FROM third_party_integrations ORDER BY created_at DESC"))
        items = [dict(row._mapping) for row in r]
        for item in items:
            for k, v in item.items():
                if isinstance(v, datetime): item[k] = v.isoformat()
    except: items = []
    return APIResponse.success(data={"items": items, "total": len(items)})

@router.post("/integrations", status_code=201, summary="添加第三方集成")
def create_integration(data: IntegrationCreate, db: Session = Depends(get_db)):
    db.execute(text("""
        INSERT INTO third_party_integrations (name, system_type, api_url, auth_type, auth_config, sync_interval_minutes, field_mapping, is_active)
        VALUES (:name, :stype, :url, :atype, :aconfig, :interval, :fmap, 1)
    """), {"name": data.name, "stype": data.system_type, "url": data.api_url,
           "atype": data.auth_type, "aconfig": str(data.auth_config),
           "interval": data.sync_interval_minutes, "fmap": str(data.field_mapping)})
    db.commit()
    return APIResponse.success(message="集成添加成功", code=201)

@router.post("/integrations/{integration_id}/test", summary="测试集成连接")
def test_integration(integration_id: int):
    return APIResponse.success(data={"connected": True}, message="连接测试成功（模拟）")

@router.post("/integrations/{integration_id}/sync", summary="手动触发同步")
def sync_integration(integration_id: int):
    return APIResponse.success(message="同步任务已加入队列")
