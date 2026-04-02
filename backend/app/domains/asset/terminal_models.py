"""
终端管理模型。

包含：
- Terminal: 终端设备（PC/笔记本/手机/平板/打印机/摄像头等）
- TerminalGroup: 终端分组（动态分组/静态分组）
- TerminalSecurityPolicy: 终端安全策略模板
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, JSON,
    Boolean, Enum, Numeric
)
from sqlalchemy.sql import func
from app.core.database import Base


class Terminal(Base):
    """终端设备"""
    __tablename__ = "terminals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    hostname = Column(String(255), index=True, comment="主机名")
    ip_address = Column(String(45), index=True)
    mac_address = Column(String(17), index=True)
    # 终端类型（指纹识别结果）
    terminal_type = Column(
        Enum("windows_pc", "mac", "linux", "android", "ios", "printer", "camera", "iot", "unknown"),
        default="unknown", index=True,
    )
    os_type = Column(String(100), comment="操作系统类型")
    os_version = Column(String(100), comment="操作系统版本")
    manufacturer = Column(String(200), comment="厂商（MAC OUI 识别）")
    model = Column(String(200), comment="型号")
    # 硬件信息
    cpu_info = Column(String(200))
    memory_gb = Column(Numeric(10, 2))
    disk_gb = Column(Numeric(10, 2))
    # 使用人
    user_name = Column(String(100), comment="使用人姓名")
    user_department = Column(String(200), comment="使用人部门")
    user_id = Column(BigInteger, comment="关联用户 ID")
    # 网络信息
    switch_ip = Column(String(45), comment="接入交换机 IP")
    switch_port = Column(String(50), comment="接入端口")
    vlan_id = Column(Integer)
    # 状态
    status = Column(Enum("active", "idle", "repair", "retired"), default="active", index=True)
    is_online = Column(Boolean, default=False, index=True)
    last_online_at = Column(DateTime)
    last_offline_at = Column(DateTime)
    offline_days = Column(Integer, default=0, comment="连续离线天数")
    # 安全合规
    compliance_score = Column(Integer, default=0, comment="合规评分 0-100")
    compliance_status = Column(Enum("compliant", "non_compliant", "unknown"), default="unknown")
    antivirus_installed = Column(Boolean)
    antivirus_updated = Column(Boolean)
    firewall_enabled = Column(Boolean)
    os_patched = Column(Boolean)
    # 标签和分组
    tags = Column(JSON, default=list)
    group_ids = Column(JSON, default=list, comment="所属分组 ID 列表")
    custom_fields = Column(JSON, default=dict)
    # 发现信息
    discovery_method = Column(String(50), comment="发现方式: arp/snmp/wmi/agent")
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    approval_status = Column(Enum("approved", "pending", "blacklisted"), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Terminal {self.hostname or self.mac_address} [{self.terminal_type}]>"

    def calculate_compliance_score(self):
        """计算合规评分"""
        score = 0
        checks = [
            (self.antivirus_installed, 25),
            (self.antivirus_updated, 20),
            (self.firewall_enabled, 25),
            (self.os_patched, 30),
        ]
        for check, points in checks:
            if check:
                score += points
        self.compliance_score = score
        self.compliance_status = "compliant" if score >= 80 else "non_compliant"
        return score


class TerminalGroup(Base):
    """终端分组"""
    __tablename__ = "terminal_groups"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    group_type = Column(Enum("static", "dynamic"), default="static")
    # 动态分组条件
    dynamic_conditions = Column(JSON, comment="动态分组条件（terminal_type/department/os_type 等）")
    # 关联策略
    security_policy_id = Column(BigInteger, comment="关联安全策略 ID")
    network_policy = Column(JSON, comment="网络策略（VLAN/ACL/限速）")
    terminal_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TerminalGroup {self.name} [{self.group_type}]>"
