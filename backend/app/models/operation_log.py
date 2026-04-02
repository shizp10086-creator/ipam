"""
操作日志模型 - 扩展版。

新增：
- tenant_id 多租户
- log_level 日志分级（normal/sensitive/critical）
- hash_value 链式哈希（防篡改）
- prev_hash 前一条日志的哈希（链式校验）
- old_data/new_data 变更前后数据（JSON）
- user_role 操作人角色

设计思路：
- 链式哈希：每条日志的 hash = SHA256(prev_hash + log_content)，
  形成链式结构，任何一条被篡改都会导致后续所有哈希校验失败。
- 日志分级：normal（普通操作）、sensitive（敏感操作如编辑网段）、
  critical（高危操作如删除网段、批量回收 IP）。
- old_data/new_data 记录变更前后的完整数据差异，用于审计追溯。
"""
import hashlib
import json
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # 操作人信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username = Column(String(50), nullable=False, comment="操作人用户名")
    user_role = Column(String(50), comment="操作人角色")

    # 操作信息
    operation_type = Column(
        String(20), nullable=False, index=True,
        comment="操作类型: create/update/delete/allocate/release/login/logout",
    )
    resource_type = Column(
        String(50), nullable=False, index=True,
        comment="资源类型: ip/device/segment/user/tenant/alert/ticket",
    )
    resource_id = Column(Integer, comment="资源 ID")

    # 日志分级
    log_level = Column(
        Enum("normal", "sensitive", "critical"),
        default="normal", nullable=False, index=True,
        comment="日志级别: normal/sensitive/critical",
    )

    # 变更数据
    details = Column(Text, comment="操作详情")
    old_data = Column(JSON, comment="变更前数据")
    new_data = Column(JSON, comment="变更后数据")

    # 链式哈希（防篡改）
    hash_value = Column(String(64), comment="当前日志哈希 SHA256")
    prev_hash = Column(String(64), comment="前一条日志哈希（链式校验）")

    # 客户端信息
    ip_address = Column(String(45), comment="客户端 IP")
    user_agent = Column(String(500), comment="User-Agent")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # 关系
    user = relationship("User", back_populates="operation_logs")

    def __repr__(self):
        return f"<OperationLog [{self.log_level}] {self.username} {self.operation_type} {self.resource_type}>"

    def compute_hash(self) -> str:
        """计算当前日志的哈希值。"""
        content = json.dumps({
            "id": self.id,
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "created_at": str(self.created_at),
            "prev_hash": self.prev_hash or "",
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def classify_log_level(operation_type: str, resource_type: str) -> str:
        """根据操作类型和资源类型自动分级。"""
        critical_ops = {
            ("delete", "segment"), ("delete", "tenant"),
            ("release", "ip"),  # 批量回收
        }
        sensitive_ops = {
            ("update", "segment"), ("update", "user"),
            ("create", "tenant"), ("delete", "device"),
            ("allocate", "ip"),
        }
        key = (operation_type, resource_type)
        if key in critical_ops:
            return "critical"
        if key in sensitive_ops:
            return "sensitive"
        return "normal"
