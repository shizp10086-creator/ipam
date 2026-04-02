"""
Event Bus Infrastructure

RabbitMQ-based event-driven architecture for inter-service communication.
Supports priority queues, idempotent consumption, and dead letter handling.
"""
from app.core.events.bus import EventBus, event_bus
from app.core.events.base import DomainEvent, EventHandler
from app.core.events.exchanges import Exchanges

__all__ = ["EventBus", "event_bus", "DomainEvent", "EventHandler", "Exchanges"]
