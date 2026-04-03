"""
IP 分配 Saga 事务定义。

完整的 IP 分配流程：
1. 分配 IP（本地数据库）
2. 创建 DHCP 租约（联动 DHCP 服务器）
3. 创建 DNS 记录（联动 DNS 服务器）
4. 更新防火墙策略（联动防火墙）

任何一步失败，自动逆序回滚已完成的步骤。

设计思路：
- 为什么用 Saga 而不是两阶段提交？因为 DHCP/DNS/防火墙是外部系统，
  不支持 XA 事务，只能用补偿式事务保证最终一致性。
- 补偿逻辑目前是占位实现，Phase 4（DHCP/DNS 联动）时填充真实逻辑。
- 每个步骤通过 context 字典传递数据，前一步的结果供后续步骤使用。
"""
import logging
from typing import Any
from app.core.saga.orchestrator import SagaOrchestrator

logger = logging.getLogger(__name__)


async def allocate_ip_in_db(context: dict[str, Any]) -> dict:
    """
    步骤 1：在本地数据库中分配 IP。

    这是唯一在 Phase 1 中有真实实现的步骤，
    其他步骤在 Phase 4 填充。
    """
    ip_address = context.get("ip_address")
    segment_id = context.get("segment_id")
    device_id = context.get("device_id")
    logger.info(f"Saga 步骤 1: 分配 IP {ip_address} (网段={segment_id}, 设备={device_id})")
    # TODO: Phase 1 任务 7.2 填充真实的数据库操作
    return {"ip_id": None, "ip_address": ip_address}


async def rollback_ip_in_db(context: dict[str, Any]) -> None:
    """步骤 1 补偿：回滚 IP 分配。"""
    ip_address = context.get("ip_address")
    logger.info(f"Saga 补偿: 回滚 IP 分配 {ip_address}")
    # TODO: Phase 1 任务 7.2 填充真实的回滚逻辑


async def create_dhcp_lease(context: dict[str, Any]) -> dict:
    """
    步骤 2：在 DHCP 服务器创建租约。

    Phase 4 任务 30.1 填充真实逻辑。
    当前为占位实现，直接返回成功。
    """
    ip_address = context.get("ip_address")
    logger.info(f"Saga 步骤 2: 创建 DHCP 租约 {ip_address} (占位)")
    return {"dhcp_lease_id": None}


async def rollback_dhcp_lease(context: dict[str, Any]) -> None:
    """步骤 2 补偿：删除 DHCP 租约。"""
    ip_address = context.get("ip_address")
    logger.info(f"Saga 补偿: 删除 DHCP 租约 {ip_address} (占位)")


async def create_dns_record(context: dict[str, Any]) -> dict:
    """
    步骤 3：在 DNS 服务器创建解析记录。

    Phase 4 任务 30.1 填充真实逻辑。
    """
    ip_address = context.get("ip_address")
    dns_name = context.get("dns_name")
    logger.info(f"Saga 步骤 3: 创建 DNS 记录 {dns_name} -> {ip_address} (占位)")
    return {"dns_record_id": None}


async def rollback_dns_record(context: dict[str, Any]) -> None:
    """步骤 3 补偿：删除 DNS 记录。"""
    dns_name = context.get("dns_name")
    logger.info(f"Saga 补偿: 删除 DNS 记录 {dns_name} (占位)")


async def update_firewall_policy(context: dict[str, Any]) -> dict:
    """
    步骤 4：更新防火墙地址组策略。

    Phase 3 任务 24.3 填充真实逻辑。
    """
    ip_address = context.get("ip_address")
    logger.info(f"Saga 步骤 4: 更新防火墙策略 {ip_address} (占位)")
    return {"fw_policy_id": None}


async def rollback_firewall_policy(context: dict[str, Any]) -> None:
    """步骤 4 补偿：回滚防火墙策略。"""
    ip_address = context.get("ip_address")
    logger.info(f"Saga 补偿: 回滚防火墙策略 {ip_address} (占位)")


def create_ip_allocation_saga() -> SagaOrchestrator:
    """
    创建 IP 分配 Saga 事务实例。

    使用示例：
    ```python
    saga = create_ip_allocation_saga()
    result = await saga.execute(context={
        "ip_address": "192.168.1.100",
        "segment_id": 1,
        "device_id": 5,
        "dns_name": "server01.example.com",
    })
    if result.status == SagaStatus.COMPLETED:
        print("IP 分配成功")
    elif result.status == SagaStatus.ROLLED_BACK:
        print(f"IP 分配失败并已回滚: {result.error}")
    ```
    """
    saga = SagaOrchestrator("IP 地址分配事务")

    saga.add_step(
        name="分配 IP（本地数据库）",
        execute=allocate_ip_in_db,
        compensate=rollback_ip_in_db,
        timeout=10,
        retries=1,
    )
    saga.add_step(
        name="创建 DHCP 租约",
        execute=create_dhcp_lease,
        compensate=rollback_dhcp_lease,
        timeout=15,
        retries=2,
    )
    saga.add_step(
        name="创建 DNS 记录",
        execute=create_dns_record,
        compensate=rollback_dns_record,
        timeout=15,
        retries=2,
    )
    saga.add_step(
        name="更新防火墙策略",
        execute=update_firewall_policy,
        compensate=rollback_firewall_policy,
        timeout=20,
        retries=1,
    )

    return saga
