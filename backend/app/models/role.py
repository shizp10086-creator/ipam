"""
角色与权限模型。

RBAC 权限体系设计思路：
- 三种预定义角色（Administrator/Regular_User/ReadOnly_User）不可删除
- 支持自定义角色，管理员可创建任意角色并分配细粒度权限
- 权限用 JSON 树存储，格式：{"segments.create": true, "devices.delete": false}
  这样比关联表更灵活，新增模块时不需要改表结构
- 支持角色继承（parent_id），子角色自动继承父角色权限
- 支持数据范围控制（data_scope），限制角色只能操作指定网段/机房的数据
- 支持权限有效期（valid_from/valid_until），临时授权到期自动失效
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Boolean, DateTime, JSON,
    ForeignKey, Table
)
from sqlalchemy.orm import relationship
from app.core.database import Base


# 用户-角色多对多关联表
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", BigInteger, ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, nullable=False, index=True, comment="租户ID")
    name = Column(String(100), nullable=False, comment="角色名称")
    code = Column(String(50), nullable=False, comment="角色编码")
    description = Column(String(500), comment="角色描述")
    is_system = Column(Boolean, default=False, comment="是否系统预定义角色（不可删除）")
    parent_id = Column(BigInteger, ForeignKey("roles.id"), comment="父角色ID（角色继承）")

    # 细粒度权限树
    # 格式：{"segments.create": true, "segments.delete": true, "devices.view": true}
    permissions = Column(JSON, default=dict, comment="权限树")

    # 数据范围控制
    # 格式：{"segments": [1,2,3], "datacenters": [1], "tenants": [1]}
    data_scope = Column(JSON, default=dict, comment="数据范围限制")

    # 权限有效期（临时授权）
    valid_from = Column(DateTime, comment="权限生效时间")
    valid_until = Column(DateTime, comment="权限失效时间")

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关系
    parent = relationship("Role", remote_side=[id], backref="children")

    __table_args__ = (
        # 同一租户内角色编码唯一
        # UniqueConstraint('tenant_id', 'code', name='uk_tenant_role_code'),
        {"comment": "角色表"},
    )

    def __repr__(self):
        return f"<Role {self.code} (tenant={self.tenant_id})>"

    def has_permission(self, permission: str) -> bool:
        """
        检查角色是否拥有指定权限。

        支持通配符：
        - "segments.*" 匹配 segments 下所有权限
        - "*" 匹配所有权限（超级管理员）
        """
        if not self.permissions:
            return False

        # 超级管理员
        if self.permissions.get("*") is True:
            return True

        # 精确匹配
        if self.permissions.get(permission) is True:
            return True

        # 通配符匹配（如 segments.* 匹配 segments.create）
        parts = permission.split(".")
        if len(parts) >= 2:
            wildcard = f"{parts[0]}.*"
            if self.permissions.get(wildcard) is True:
                return True

        return False


# 预定义角色权限模板
SYSTEM_ROLES = {
    "administrator": {
        "name": "管理员",
        "code": "administrator",
        "is_system": True,
        "permissions": {"*": True},  # 所有权限
        "data_scope": {},  # 无限制
    },
    "regular_user": {
        "name": "普通用户",
        "code": "regular_user",
        "is_system": True,
        "permissions": {
            "segments.view": True,
            "ips.view": True, "ips.allocate": True, "ips.release": True,
            "devices.view": True, "devices.create": True, "devices.update": True,
            "alerts.view": True,
            "logs.view": True,
            "dashboard.view": True,
        },
        "data_scope": {},
    },
    "readonly_user": {
        "name": "只读用户",
        "code": "readonly_user",
        "is_system": True,
        "permissions": {
            "segments.view": True,
            "ips.view": True,
            "devices.view": True,
            "alerts.view": True,
            "logs.view": True,
            "dashboard.view": True,
        },
        "data_scope": {},
    },
}
