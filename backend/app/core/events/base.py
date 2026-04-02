"""
Base classes for domain events and event handlers.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    routing_key: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: Optional[int] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    resource_type: str = ""
    resource_id: Optional[int] = None
    idempotency_key: Optional[str] = None
    priority: int = 5  # 0-10, higher = more urgent
    data: dict[str, Any] = Field(default_factory=dict)

    def to_message(self) -> dict:
        """Serialize event to message dict for RabbitMQ."""
        return self.model_dump(mode="json")


class EventHandler(ABC):
    """Base class for event handlers (consumers)."""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Process a domain event."""
        pass

    @property
    @abstractmethod
    def event_types(self) -> list[str]:
        """List of event types this handler subscribes to."""
        pass
