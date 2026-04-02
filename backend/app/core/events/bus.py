"""
事件总线 - 基于内存的事件发布/订阅实现。
生产环境可替换为 RabbitMQ 实现，接口保持一致。
"""
import logging
import uuid
from typing import Callable, Optional
from collections import defaultdict
from app.core.events.base import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    事件总线核心类。
    
    当前为内存实现（适合单进程开发/测试），
    后续可无缝切换为 RabbitMQ 实现。
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._processed_ids: set[str] = set()  # 幂等性：已处理的消息ID
        self._max_processed_cache = 10000

    def subscribe(self, routing_key: str, handler: Callable) -> None:
        """订阅指定路由键的事件。"""
        self._handlers[routing_key].append(handler)
        logger.info(f"事件订阅注册: {routing_key} -> {handler.__name__}")

    def subscribe_pattern(self, pattern: str, handler: Callable) -> None:
        """订阅匹配模式的事件（如 'ip.*' 匹配所有 IP 事件）。"""
        self._handlers[f"pattern:{pattern}"].append(handler)
        logger.info(f"模式订阅注册: {pattern} -> {handler.__name__}")

    async def publish(self, event: DomainEvent) -> None:
        """
        发布事件到总线。
        
        支持幂等性检查：相同 event_id 的事件不会重复处理。
        """
        # 幂等性检查
        if event.event_id in self._processed_ids:
            logger.warning(f"重复事件已跳过: {event.event_id}")
            return

        logger.info(
            f"事件发布: type={event.event_type} "
            f"routing_key={event.routing_key} "
            f"resource={event.resource_type}:{event.resource_id}"
        )

        # 精确匹配的处理器
        handlers = list(self._handlers.get(event.routing_key, []))

        # 模式匹配的处理器
        for key, pattern_handlers in self._handlers.items():
            if key.startswith("pattern:"):
                pattern = key[8:]
                if self._match_pattern(pattern, event.routing_key):
                    handlers.extend(pattern_handlers)

        # 执行所有处理器
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"事件处理失败: handler={handler.__name__} "
                    f"event_id={event.event_id} error={e}"
                )

        # 记录已处理
        self._processed_ids.add(event.event_id)
        if len(self._processed_ids) > self._max_processed_cache:
            # 清理最早的一半缓存
            to_remove = list(self._processed_ids)[:self._max_processed_cache // 2]
            for item in to_remove:
                self._processed_ids.discard(item)

    def _match_pattern(self, pattern: str, routing_key: str) -> bool:
        """简单的通配符匹配（支持 * 和 #）。"""
        pattern_parts = pattern.split(".")
        key_parts = routing_key.split(".")

        if len(pattern_parts) != len(key_parts):
            # # 匹配多级
            if "#" in pattern_parts:
                return True
            return False

        for p, k in zip(pattern_parts, key_parts):
            if p == "*":
                continue
            if p == "#":
                return True
            if p != k:
                return False
        return True

    def clear(self) -> None:
        """清除所有订阅和缓存（用于测试）。"""
        self._handlers.clear()
        self._processed_ids.clear()


# 全局事件总线单例
event_bus = EventBus()
