"""
RabbitMQ Exchange definitions for the event bus.
"""


class Exchanges:
    """All RabbitMQ exchange names used by the system."""
    IP = "ipam.ip"
    DEVICE = "ipam.device"
    NAC = "ipam.nac"
    SCAN = "ipam.scan"
    ALERT = "ipam.alert"
    CHANGE = "ipam.change"
    AUDIT = "ipam.audit"
    WORKFLOW = "ipam.workflow"
    COLLECTOR = "ipam.collector"
    TERMINAL = "ipam.terminal"

    ALL = [IP, DEVICE, NAC, SCAN, ALERT, CHANGE, AUDIT, WORKFLOW, COLLECTOR, TERMINAL]


class RoutingKeys:
    """Standard routing keys for events."""
    # IP events
    IP_ALLOCATED = "ip.allocated"
    IP_RELEASED = "ip.released"
    IP_CONFLICT_DETECTED = "ip.conflict.detected"
    IP_STATUS_CHANGED = "ip.status.changed"

    # Device events
    DEVICE_CREATED = "device.created"
    DEVICE_UPDATED = "device.updated"
    DEVICE_DELETED = "device.deleted"
    DEVICE_CONFIG_CHANGED = "device.config.changed"

    # NAC events
    NAC_AUTH_SUCCESS = "nac.auth.success"
    NAC_AUTH_FAILED = "nac.auth.failed"
    NAC_VIOLATION_DETECTED = "nac.violation.detected"

    # Scan events
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    SCAN_UNREGISTERED_FOUND = "scan.unregistered.found"

    # Alert events
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_RESOLVED = "alert.resolved"
    ALERT_ESCALATED = "alert.escalated"

    # Change events
    CHANGE_REQUESTED = "change.requested"
    CHANGE_APPROVED = "change.approved"
    CHANGE_EXECUTED = "change.executed"
    CHANGE_ROLLED_BACK = "change.rolled_back"

    # Audit events
    AUDIT_LOGGED = "audit.logged"

    # Workflow events
    WORKFLOW_SUBMITTED = "workflow.submitted"
    WORKFLOW_APPROVED = "workflow.approved"
    WORKFLOW_REJECTED = "workflow.rejected"
    WORKFLOW_COMPLETED = "workflow.completed"
