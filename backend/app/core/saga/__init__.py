"""
Saga 分布式事务编排引擎。

采用编排式 Saga 模式，支持：
- 多步骤事务定义（步骤 + 补偿逻辑）
- 失败自动回滚（逆序执行补偿）
- 断点续执（事务状态持久化）
- 幂等性保障
"""
from app.core.saga.orchestrator import SagaOrchestrator, SagaStep, SagaStatus

__all__ = ["SagaOrchestrator", "SagaStep", "SagaStatus"]
