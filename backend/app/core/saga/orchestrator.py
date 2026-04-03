"""
Saga 事务编排器。

用于跨系统操作的事务管理，例如：
IP 分配 → DHCP 下发 → DNS 创建 → 防火墙策略更新

任何一步失败，自动逆序执行补偿逻辑回滚已完成的步骤。
"""
import enum
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


class SagaStatus(str, enum.Enum):
    """Saga 事务状态"""
    PENDING = "pending"          # 待执行
    RUNNING = "running"          # 执行中
    COMPLETED = "completed"      # 已完成
    COMPENSATING = "compensating"  # 回滚中
    ROLLED_BACK = "rolled_back"  # 已回滚
    FAILED = "failed"            # 失败（回滚也失败）


class StepStatus(str, enum.Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"
    COMPENSATION_FAILED = "compensation_failed"
    SKIPPED = "skipped"


@dataclass
class SagaStep:
    """
    Saga 事务步骤定义。

    每个步骤包含：
    - name: 步骤名称
    - execute: 执行函数（异步）
    - compensate: 补偿函数（异步，用于回滚）
    - timeout: 超时时间（秒）
    - retries: 重试次数
    """
    name: str
    execute: Callable[..., Coroutine[Any, Any, Any]]
    compensate: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    timeout: int = 30
    retries: int = 0
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class SagaTransaction:
    """Saga 事务实例"""
    saga_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    status: SagaStatus = SagaStatus.PENDING
    steps: list[SagaStep] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    current_step_index: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class SagaOrchestrator:
    """
    Saga 事务编排器。

    使用示例：
    ```python
    saga = SagaOrchestrator("IP分配事务")
    saga.add_step(
        name="分配IP",
        execute=allocate_ip,
        compensate=release_ip
    )
    saga.add_step(
        name="创建DHCP租约",
        execute=create_dhcp_lease,
        compensate=delete_dhcp_lease
    )
    saga.add_step(
        name="创建DNS记录",
        execute=create_dns_record,
        compensate=delete_dns_record
    )
    result = await saga.execute(context={"ip": "192.168.1.100"})
    ```
    """

    def __init__(self, name: str):
        self.transaction = SagaTransaction(name=name)

    def add_step(
        self,
        name: str,
        execute: Callable[..., Coroutine[Any, Any, Any]],
        compensate: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None,
        timeout: int = 30,
        retries: int = 0,
    ) -> "SagaOrchestrator":
        """添加事务步骤，支持链式调用。"""
        step = SagaStep(
            name=name,
            execute=execute,
            compensate=compensate,
            timeout=timeout,
            retries=retries,
        )
        self.transaction.steps.append(step)
        return self

    async def execute(self, context: Optional[dict] = None) -> SagaTransaction:
        """
        执行 Saga 事务。

        按顺序执行所有步骤，任何步骤失败则逆序执行补偿。
        """
        if context:
            self.transaction.context.update(context)

        self.transaction.status = SagaStatus.RUNNING
        logger.info(f"Saga 开始执行: {self.transaction.name} (ID: {self.transaction.saga_id})")

        for i, step in enumerate(self.transaction.steps):
            self.transaction.current_step_index = i
            step.status = StepStatus.RUNNING
            step.started_at = datetime.now(timezone.utc)

            try:
                # 执行步骤（支持重试）
                result = await self._execute_with_retry(step)
                step.result = result
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)

                # 将步骤结果存入上下文，供后续步骤使用
                self.transaction.context[f"step_{i}_result"] = result

                logger.info(f"Saga 步骤完成: [{i+1}/{len(self.transaction.steps)}] {step.name}")

            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                step.completed_at = datetime.now(timezone.utc)
                self.transaction.error = f"步骤 '{step.name}' 失败: {e}"

                logger.error(f"Saga 步骤失败: {step.name} - {e}")

                # 触发补偿（回滚）
                await self._compensate(i)
                return self.transaction

        # 所有步骤成功
        self.transaction.status = SagaStatus.COMPLETED
        self.transaction.completed_at = datetime.now(timezone.utc)
        logger.info(f"Saga 执行成功: {self.transaction.name}")
        return self.transaction

    async def _execute_with_retry(self, step: SagaStep) -> Any:
        """执行步骤，支持重试。"""
        last_error = None
        for attempt in range(step.retries + 1):
            try:
                return await step.execute(self.transaction.context)
            except Exception as e:
                last_error = e
                if attempt < step.retries:
                    logger.warning(
                        f"步骤 '{step.name}' 第 {attempt+1} 次执行失败，重试中: {e}"
                    )
        raise last_error

    async def _compensate(self, failed_step_index: int) -> None:
        """逆序执行补偿逻辑，回滚已完成的步骤。"""
        self.transaction.status = SagaStatus.COMPENSATING
        logger.info(f"Saga 开始回滚: {self.transaction.name}")

        compensation_failed = False

        # 从失败步骤的前一步开始，逆序补偿
        for i in range(failed_step_index - 1, -1, -1):
            step = self.transaction.steps[i]
            if step.status != StepStatus.COMPLETED:
                continue
            if step.compensate is None:
                logger.warning(f"步骤 '{step.name}' 无补偿逻辑，跳过")
                step.status = StepStatus.SKIPPED
                continue

            try:
                await step.compensate(self.transaction.context)
                step.status = StepStatus.COMPENSATED
                logger.info(f"Saga 补偿完成: {step.name}")
            except Exception as e:
                step.status = StepStatus.COMPENSATION_FAILED
                step.error = f"补偿失败: {e}"
                compensation_failed = True
                logger.error(f"Saga 补偿失败: {step.name} - {e}")

        if compensation_failed:
            self.transaction.status = SagaStatus.FAILED
            logger.error(f"Saga 回滚部分失败: {self.transaction.name}")
        else:
            self.transaction.status = SagaStatus.ROLLED_BACK
            logger.info(f"Saga 回滚完成: {self.transaction.name}")

        self.transaction.completed_at = datetime.now(timezone.utc)
