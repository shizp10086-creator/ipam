"""
NAC 准入控制域模型。

包含：
- NacPolicy: 认证策略（802.1X/Portal/MAC/PPSK 规则链）
- NacSession: 终端在线会话
- NacAuthLog: 认证日志
- VisitorAccount: 访客临时账号
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, JSON,
    Boolean, Enum
)
from sqlalchemy.sql import func
from app.core.database import Base


class NacPolicy(Base):
    """认证策略"""
    __tablename__ = "nac_policies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=100, comment="优先级（数字越小越优先）")
    is_active = Column(Boolean, default=True)
    # 匹配条件
    conditions = Column(JSON, nullable=False, comment="匹配条件（终端类型/接入方式/部门/时间等）")
    # 动作
    auth_method = Column(Enum("802.1x", "portal", "mac", "ppsk", "bypass"), comment="认证方式")
    actions = Column(JSON, nullable=False, comment="动作（分配VLAN/下发ACL/限速/MFA等）")
    version = Column(Integer, default=1)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NacPolicy {self.name} pri={self.priority}>"


class NacSession(Base):
    """终端在线会话"""
    __tablename__ = "nac_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    mac_address = Column(String(17), nullable=False, index=True)
    ip_address = Column(String(45), index=True)
    username = Column(String(100))
    auth_method = Column(String(20), comment="认证方式")
    vlan_id = Column(Integer)
    switch_ip = Column(String(45), comment="接入交换机 IP")
    switch_port = Column(String(50), comment="接入端口")
    ssid = Column(String(100), comment="无线 SSID")
    compliance_status = Column(Enum("compliant", "non_compliant", "quarantined", "unknown"), default="unknown")
    compliance_score = Column(Integer, default=0)
    session_start = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)

    def __repr__(self):
        return f"<NacSession {self.mac_address} [{self.compliance_status}]>"


class NacAuthLog(Base):
    """认证日志"""
    __tablename__ = "nac_auth_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    mac_address = Column(String(17), nullable=False, index=True)
    ip_address = Column(String(45))
    username = Column(String(100))
    auth_method = Column(String(20))
    result = Column(Enum("success", "failed", "rejected"), nullable=False, index=True)
    failure_reason = Column(String(500))
    switch_ip = Column(String(45))
    switch_port = Column(String(50))
    ssid = Column(String(100))
    policy_id = Column(BigInteger, comment="匹配的策略 ID")
    assigned_vlan = Column(Integer)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<NacAuthLog {self.mac_address} [{self.result}]>"


class VisitorAccount(Base):
    """访客临时账号"""
    __tablename__ = "visitor_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    visitor_name = Column(String(100), nullable=False)
    visitor_company = Column(String(200))
    visitor_phone = Column(String(20))
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    sponsor_name = Column(String(100), comment="邀请人")
    sponsor_department = Column(String(200))
    access_level = Column(Enum("internet_only", "limited", "full"), default="internet_only")
    vlan_id = Column(Integer, comment="访客 VLAN")
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Visitor {self.visitor_name} until={self.valid_until}>"
