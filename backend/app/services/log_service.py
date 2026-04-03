"""
日志记录服务
提供操作日志的记录功能
"""
import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.operation_log import OperationLog


class LogService:
    """
    日志记录服务类
    负责记录系统中所有关键操作的审计日志
    """

    @staticmethod
    def create_log(
        db: Session,
        user_id: int,
        username: str,
        operation_type: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None
    ) -> OperationLog:
        """
        创建操作日志记录

        Args:
            db: 数据库会话
            user_id: 操作人 ID
            username: 操作人用户名
            operation_type: 操作类型 (create/update/delete/allocate/release)
            resource_type: 资源类型 (ip/device/segment/user)
            resource_id: 资源 ID（可选）
            details: 操作详情（字典格式，将转换为 JSON）
            client_ip: 客户端 IP 地址

        Returns:
            创建的日志记录对象
        """
        # 将详情字典转换为 JSON 字符串
        details_json = None
        if details:
            details_json = json.dumps(details, ensure_ascii=False)

        # 创建日志记录
        log = OperationLog(
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details_json,
            ip_address=client_ip
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        return log

    @staticmethod
    def log_ip_allocation(
        db: Session,
        user_id: int,
        username: str,
        ip_address: str,
        device_id: Optional[int],
        device_name: Optional[str],
        segment_id: int,
        client_ip: Optional[str] = None
    ) -> OperationLog:
        """
        记录 IP 分配操作

        Args:
            db: 数据库会话
            user_id: 操作人 ID
            username: 操作人用户名
            ip_address: 分配的 IP 地址
            device_id: 关联设备 ID
            device_name: 关联设备名称
            segment_id: 所属网段 ID
            client_ip: 客户端 IP

        Returns:
            创建的日志记录
        """
        details = {
            "ip_address": ip_address,
            "device_id": device_id,
            "device_name": device_name,
            "segment_id": segment_id,
            "action": "allocate"
        }

        return LogService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            operation_type="allocate",
            resource_type="ip",
            resource_id=None,  # IP 分配时可能还没有 IP 记录 ID
            details=details,
            client_ip=client_ip
        )

    @staticmethod
    def log_ip_release(
        db: Session,
        user_id: int,
        username: str,
        ip_address: str,
        ip_id: int,
        client_ip: Optional[str] = None
    ) -> OperationLog:
        """
        记录 IP 回收操作

        Args:
            db: 数据库会话
            user_id: 操作人 ID
            username: 操作人用户名
            ip_address: 回收的 IP 地址
            ip_id: IP 记录 ID
            client_ip: 客户端 IP

        Returns:
            创建的日志记录
        """
        details = {
            "ip_address": ip_address,
            "action": "release"
        }

        return LogService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            operation_type="release",
            resource_type="ip",
            resource_id=ip_id,
            details=details,
            client_ip=client_ip
        )

    @staticmethod
    def log_device_operation(
        db: Session,
        user_id: int,
        username: str,
        operation_type: str,
        device_id: int,
        device_data: Dict[str, Any],
        client_ip: Optional[str] = None
    ) -> OperationLog:
        """
        记录设备操作（创建/编辑/删除）

        Args:
            db: 数据库会话
            user_id: 操作人 ID
            username: 操作人用户名
            operation_type: 操作类型 (create/update/delete)
            device_id: 设备 ID
            device_data: 设备数据
            client_ip: 客户端 IP

        Returns:
            创建的日志记录
        """
        return LogService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            resource_type="device",
            resource_id=device_id,
            details=device_data,
            client_ip=client_ip
        )

    @staticmethod
    def log_segment_operation(
        db: Session,
        user_id: int,
        username: str,
        operation_type: str,
        segment_id: int,
        segment_data: Dict[str, Any],
        client_ip: Optional[str] = None
    ) -> OperationLog:
        """
        记录网段操作（创建/编辑/删除）

        Args:
            db: 数据库会话
            user_id: 操作人 ID
            username: 操作人用户名
            operation_type: 操作类型 (create/update/delete)
            segment_id: 网段 ID
            segment_data: 网段数据
            client_ip: 客户端 IP

        Returns:
            创建的日志记录
        """
        return LogService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            resource_type="segment",
            resource_id=segment_id,
            details=segment_data,
            client_ip=client_ip
        )

    @staticmethod
    def log_user_operation(
        db: Session,
        user_id: int,
        username: str,
        operation_type: str,
        target_user_id: int,
        user_data: Dict[str, Any],
        client_ip: Optional[str] = None
    ) -> OperationLog:
        """
        记录用户操作（创建/编辑/删除）

        Args:
            db: 数据库会话
            user_id: 操作人 ID
            username: 操作人用户名
            operation_type: 操作类型 (create/update/delete)
            target_user_id: 目标用户 ID
            user_data: 用户数据（应包含角色信息）
            client_ip: 客户端 IP

        Returns:
            创建的日志记录
        """
        return LogService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            resource_type="user",
            resource_id=target_user_id,
            details=user_data,
            client_ip=client_ip
        )
