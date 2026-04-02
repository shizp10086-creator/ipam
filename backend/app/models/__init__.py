"""
Database Models - 所有数据库模型注册。
"""
from app.models.user import User
from app.models.tenant import Tenant
from app.models.role import Role, user_roles, SYSTEM_ROLES
from app.models.network_segment import NetworkSegment, SegmentGroup
from app.models.ip_address import IPAddress, IPLifecycleLog
from app.models.device import Device
from app.models.operation_log import OperationLog
from app.models.alert import Alert
from app.models.scan_history import ScanHistory
from app.models.saga_transaction import SagaTransactionLog
from app.models.designer_config import DesignerConfig, DesignerConfigVersion
from app.models.custom_connector import CustomConnector
from app.models.automation_workflow import AutomationWorkflow

__all__ = [
    "User", "Tenant", "Role", "user_roles", "SYSTEM_ROLES",
    "NetworkSegment", "SegmentGroup",
    "IPAddress", "IPLifecycleLog",
    "Device", "OperationLog", "Alert", "ScanHistory",
    "SagaTransactionLog",
    "DesignerConfig", "DesignerConfigVersion",
    "CustomConnector", "AutomationWorkflow",
]
