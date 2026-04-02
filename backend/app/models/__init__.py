"""
Database Models

This module imports all database models to ensure they are registered with SQLAlchemy.
Import this module to access all models.
"""
from app.models.user import User
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress
from app.models.device import Device
from app.models.operation_log import OperationLog
from app.models.alert import Alert
from app.models.scan_history import ScanHistory

# Export all models
__all__ = [
    "User",
    "NetworkSegment",
    "IPAddress",
    "Device",
    "OperationLog",
    "Alert",
    "ScanHistory",
]
