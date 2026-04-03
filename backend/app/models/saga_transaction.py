"""
Saga 事务持久化模型

记录每个 Saga 事务的执行状态，用于：
- 断点续执：系统重启后恢复未完成的事务
- 审计追溯：查看每个跨系统操作的完整执行过程
- 故障排查：定位哪一步失败、补偿是否成功
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, String, Text, DateTime, JSON, Enum, Integer
)
from app.core.database import Base


class SagaTransactionLog(Base):
    """Saga 事务日志"""
    __tablename__ = "saga_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    saga_id = Column(String(36), unique=True, nullable=False, index=True, comment="事务唯一ID")
    name = Column(String(200), nullable=False, comment="事务名称")
    status = Column(
        Enum("pending", "running", "completed", "compensating", "rolled_back", "failed"),
        default="pending",
        nullable=False,
        comment="事务状态",
    )
    tenant_id = Column(BigInteger, index=True, comment="租户ID")
    operator_id = Column(BigInteger, comment="操作人ID")
    context = Column(JSON, comment="事务上下文数据")
    steps_snapshot = Column(JSON, comment="步骤执行快照")
    current_step = Column(Integer, default=0, comment="当前执行到第几步")
    error = Column(Text, comment="错误信息")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    completed_at = Column(DateTime, comment="完成时间")

    def __repr__(self):
        return f"<SagaTransaction {self.saga_id} [{self.status}] {self.name}>"
