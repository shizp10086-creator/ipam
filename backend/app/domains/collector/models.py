"""
数据采集域模型

包含
- CollectorCredential: 采集凭证（SNMP 社区字符SSH 密码/密钥等，AES-256 加密存储
- CollectorTask: 采集任务定义（协目标/周期/状态）
- CollectorTaskLog: 采集任务执行日志
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, JSON,
    Boolean, Numeric, Enum
)
from sqlalchemy.sql import func
from app.core.database import Base


class CollectorCredential(Base):
    """采集凭证（加密存储）"""
    __tablename__ = "collector_credentials"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    name = Column(String(200), nullable=False, comment="凭证名称")
    credential_type = Column(
        Enum("snmp_v2c", "snmp_v3", "ssh_password", "ssh_key", "wmi", "api_key"),
        nullable=False, comment="凭证类型",
    )
    # 加密存储的凭证数
    credential_data = Column(JSON, nullable=False, comment="凭证数据（敏感字AES 加密")
    # 示例:
    # snmp_v2c: {"community": "encrypted:xxx"}
    # ssh_password: {"username": "admin", "password": "encrypted:xxx"}
    # snmp_v3: {"username": "...", "auth_protocol": "SHA", "auth_password": "encrypted:...", "priv_protocol": "AES", "priv_password": "encrypted:..."}
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Credential [{self.credential_type}] {self.name}>"


class CollectorTask(Base):
    """采集任务定义"""
    __tablename__ = "collector_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True)
    name = Column(String(200), nullable=False, comment="任务名称")
    protocol = Column(
        Enum("snmp", "ssh", "ping", "syslog", "netflow", "wmi", "modbus", "mqtt", "ipmi"),
        nullable=False, index=True, comment="采集协议",
    )
    # 采集目标
    targets = Column(JSON, nullable=False, comment="采集目标列表（IP/网段")
    credential_id = Column(BigInteger, comment="关联凭证 ID")
    # 采集配置
    config = Column(JSON, default=dict, comment="采集配置（OID 列表/命令/端口等）")
    interval_seconds = Column(Integer, default=300, comment="采集间隔（秒")
    timeout_seconds = Column(Integer, default=30, comment="超时时间（秒")
    retry_count = Column(Integer, default=2, comment="重试次数")
    priority = Column(Integer, default=5, comment="优先级（1-10")
    # 状
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_run_at = Column(DateTime, comment="最后执行时")
    last_run_status = Column(String(20), comment="最后执行状")
    last_run_duration_ms = Column(Integer, comment="最后执行耗时（毫秒）")
    total_runs = Column(Integer, default=0, comment="总执行次")
    success_runs = Column(Integer, default=0, comment="成功次数")
    fail_runs = Column(Integer, default=0, comment="失败次数")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def success_rate(self):
        if self.total_runs > 0:
            return round((self.success_runs / self.total_runs) * 100, 2)
        return 0

    def __repr__(self):
        return f"<CollectorTask [{self.protocol}] {self.name}>"


class CollectorTaskLog(Base):
    """采集任务执行日志"""
    __tablename__ = "collector_task_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False, index=True)
    status = Column(Enum("success", "failed", "timeout", "partial"), nullable=False)
    target_count = Column(Integer, comment="目标数量")
    success_count = Column(Integer, default=0, comment="成功数量")
    fail_count = Column(Integer, default=0, comment="失败数量")
    duration_ms = Column(Integer, comment="执行耗时（毫秒）")
    error_message = Column(Text, comment="错误信息")
    details = Column(JSON, comment="执行详情")
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    def __repr__(self):
        return f"<TaskLog task={self.task_id} [{self.status}]>"
