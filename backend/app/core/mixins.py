"""
SQLAlchemy Model Mixins

提供可复用的模型字段和行为：
- OptimisticLockMixin: 乐观锁（version 字段），防止并发覆盖
- SoftDeleteMixin: 软删除（deleted_at 字段），支持回收
- AuditMixin: 审计字段（created_by, updated_by, created_at, updated_at
- TenantMixin: 多租户隔离（tenant_id 字段

设计思路
- 乐观锁选择 version 字段而非时间戳，因为时间戳精度不够可能导致误判
- 软删除用 deleted_at 而非 is_deleted 布尔值，因为需要知道删除时间（回收站保留期限）
- 所Mixin 都是独立的，可以按需组合使用
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, DateTime, event
from sqlalchemy.orm import declared_attr
from fastapi import HTTPException, status


class OptimisticLockMixin:
    """
    乐观Mixin

    每次更新version 自动 +1，如果提交的 version 与数据库不一致，
    说明有其他人同时修改了这条数据，返回 409 冲突

    使用方式
    ```python
    class NetworkSegment(Base, OptimisticLockMixin):
        __tablename__ = "network_segments"
        ...

    # 更新时传入当version
    def update_segment(db, segment_id, data, current_version):
        rows = db.query(NetworkSegment).filter(
            NetworkSegment.id == segment_id,
            NetworkSegment.version == current_version  # 关键：版本校
        ).update({
            **data,
            "version": NetworkSegment.version + 1
        })
        if rows == 0:
            raise HTTPException(409, "数据已被其他人修改，请刷新后重试")
    ```
    """
    version = Column(Integer, default=1, nullable=False, comment="乐观锁版本号")


class SoftDeleteMixin:
    """
    软删Mixin

    删除操作不真正删除数据，而是设置 deleted_at 时间戳
    配合回收站功能（需70），超过保留期限后才永久删除

    查询时需要加 .filter(Model.deleted_at.is_(None)) 过滤已删除数据
    """
    deleted_at = Column(DateTime, nullable=True, index=True, comment="软删除时")

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self):
        """标记为已删除"""
        self.deleted_at = datetime.now()

    def restore(self):
        """从回收站恢复"""
        self.deleted_at = None


class AuditMixin:
    """
    审计字段 Mixin

    自动记录创建人、更新人、创建时间、更新时间
    """
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")
    updated_by = Column(BigInteger, nullable=True, comment="最后更新人ID")
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now,
        nullable=False, comment="更新时间"
    )


class TenantMixin:
    """
    多租户隔Mixin

    所有业务数据都tenant_id，通过中间件自动注入查询条件，
    确保租户间数据完全隔离
    """
    @declared_attr
    def tenant_id(cls):
        return Column(BigInteger, nullable=False, index=True, comment="租户ID")
