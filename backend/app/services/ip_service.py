"""
IP Address Service
处理 IP 地址分配、回收、保留等业务逻辑
"""
from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.ip_address import IPAddress
from app.models.device import Device
from app.models.operation_log import OperationLog
from app.utils.ip_utils import (
    validate_ip_address,
    find_segment_for_ip,
    is_ip_in_segment,
    can_allocate_ip
)


class IPAllocationError(Exception):
    """IP 分配错误"""
    pass


class IPService:
    """IP 地址服务类"""
    
    @staticmethod
    def allocate_ip(
        db: Session,
        ip_address_str: str,
        device_id: int,
        user_id: int,
        segment_id: Optional[int] = None,
        skip_conflict_check: bool = False
    ) -> Tuple[bool, str, Optional[IPAddress]]:
        """
        分配 IP 地址
        
        Args:
            db: 数据库会话
            ip_address_str: IP 地址字符串
            device_id: 设备 ID
            user_id: 操作用户 ID
            segment_id: 网段 ID（可选，如果不提供则自动查找）
            skip_conflict_check: 是否跳过冲突检测（默认 False）
            
        Returns:
            (success, message, ip_address): 操作结果、消息和 IP 对象
        """
        # 1. 验证 IP 地址格式
        is_valid, error = validate_ip_address(ip_address_str)
        if not is_valid:
            return False, error, None
        
        # 2. 验证设备是否存在
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return False, "Device not found", None
        
        # 3. 查找或验证网段
        if segment_id:
            # 如果提供了 segment_id，验证 IP 是否属于该网段
            from app.models.network_segment import NetworkSegment
            segment = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
            if not segment:
                return False, "Network segment not found", None
            
            if not is_ip_in_segment(ip_address_str, segment):
                return False, f"IP address {ip_address_str} does not belong to segment {segment.network}/{segment.prefix_length}", None
        else:
            # 自动查找 IP 所属网段
            segment = find_segment_for_ip(db, ip_address_str)
            if not segment:
                return False, f"No network segment found for IP address {ip_address_str}", None
            segment_id = segment.id
        
        # 4. 查询 IP 地址记录
        ip_record = db.query(IPAddress).filter(
            IPAddress.ip_address == ip_address_str
        ).first()
        
        if ip_record:
            # IP 已存在，检查是否可分配
            can_alloc, reason = can_allocate_ip(ip_record)
            if not can_alloc:
                return False, f"Cannot allocate IP: {reason}", None
        else:
            # IP 不存在，创建新记录
            ip_record = IPAddress(
                ip_address=ip_address_str,
                segment_id=segment_id,
                status="available"
            )
            db.add(ip_record)
            db.flush()  # 获取 ID
        
        # 5. 执行冲突检测（如果需要）
        if not skip_conflict_check:
            # 调用冲突检测服务
            import asyncio
            from app.services.conflict_detection import ConflictDetectionService
            
            # 在同步函数中运行异步冲突检测
            conflict_result = asyncio.run(
                ConflictDetectionService.check_ip_conflict(
                    db=db,
                    ip_address=ip_address_str,
                    check_ping=True,
                    check_arp=False  # ARP 检测可选
                )
            )
            
            if conflict_result.has_conflict:
                return False, f"IP conflict detected: {conflict_result.message}", None
        
        # 6. 更新 IP 状态为"已用"
        ip_record.status = "used"
        ip_record.device_id = device_id
        ip_record.allocated_by = user_id
        ip_record.allocated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(ip_record)
            
            # 7. 记录操作日志
            IPService._log_operation(
                db=db,
                user_id=user_id,
                operation_type="allocate",
                resource_type="ip",
                resource_id=ip_record.id,
                details={
                    "ip_address": ip_address_str,
                    "device_id": device_id,
                    "segment_id": segment_id,
                    "status": "used"
                }
            )
            
            # 8. 检查网段使用率并触发告警（如果需要）
            from app.services.alert_service import AlertService
            AlertService.check_and_create_alert(db, segment_id)
            
            return True, "IP address allocated successfully", ip_record
            
        except Exception as e:
            db.rollback()
            return False, f"Database error: {str(e)}", None
    
    @staticmethod
    def release_ip(
        db: Session,
        ip_address_str: Optional[str] = None,
        ip_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Tuple[bool, str, Optional[IPAddress]]:
        """
        回收 IP 地址
        
        Args:
            db: 数据库会话
            ip_address_str: IP 地址字符串（二选一）
            ip_id: IP 地址 ID（二选一）
            user_id: 操作用户 ID
            
        Returns:
            (success, message, ip_address): 操作结果、消息和 IP 对象
        """
        # 1. 查询 IP 地址记录
        if ip_id:
            ip_record = db.query(IPAddress).filter(IPAddress.id == ip_id).first()
        elif ip_address_str:
            ip_record = db.query(IPAddress).filter(
                IPAddress.ip_address == ip_address_str
            ).first()
        else:
            return False, "Either ip_address or ip_id must be provided", None
        
        if not ip_record:
            return False, "IP address not found", None
        
        # 2. 检查当前状态
        if ip_record.status == "available":
            return False, "IP address is already available", None
        
        # 3. 更新 IP 状态为"空闲"
        old_device_id = ip_record.device_id
        old_segment_id = ip_record.segment_id
        ip_record.status = "available"
        ip_record.device_id = None
        ip_record.allocated_by = None
        ip_record.allocated_at = None
        
        try:
            db.commit()
            db.refresh(ip_record)
            
            # 4. 记录操作日志
            if user_id:
                IPService._log_operation(
                    db=db,
                    user_id=user_id,
                    operation_type="release",
                    resource_type="ip",
                    resource_id=ip_record.id,
                    details={
                        "ip_address": ip_record.ip_address,
                        "old_device_id": old_device_id,
                        "status": "available"
                    }
                )
            
            # 5. 检查网段使用率并解除告警（如果需要）
            from app.services.alert_service import AlertService
            AlertService.check_and_resolve_alert(db, old_segment_id)
            
            return True, "IP address released successfully", ip_record
            
        except Exception as e:
            db.rollback()
            return False, f"Database error: {str(e)}", None
    
    @staticmethod
    def reserve_ip(
        db: Session,
        ip_address_str: Optional[str] = None,
        ip_id: Optional[int] = None,
        reserve: bool = True,
        user_id: Optional[int] = None
    ) -> Tuple[bool, str, Optional[IPAddress]]:
        """
        保留或取消保留 IP 地址
        
        Args:
            db: 数据库会话
            ip_address_str: IP 地址字符串（二选一）
            ip_id: IP 地址 ID（二选一）
            reserve: True=保留, False=取消保留
            user_id: 操作用户 ID
            
        Returns:
            (success, message, ip_address): 操作结果、消息和 IP 对象
        """
        # 1. 查询 IP 地址记录
        if ip_id:
            ip_record = db.query(IPAddress).filter(IPAddress.id == ip_id).first()
        elif ip_address_str:
            ip_record = db.query(IPAddress).filter(
                IPAddress.ip_address == ip_address_str
            ).first()
        else:
            return False, "Either ip_address or ip_id must be provided", None
        
        if not ip_record:
            return False, "IP address not found", None
        
        # 2. 检查当前状态
        if reserve:
            # 保留操作
            if ip_record.status == "used":
                return False, "Cannot reserve IP address that is in use", None
            if ip_record.status == "reserved":
                return False, "IP address is already reserved", None
            
            ip_record.status = "reserved"
            operation = "reserve"
            message = "IP address reserved successfully"
        else:
            # 取消保留操作
            if ip_record.status != "reserved":
                return False, "IP address is not reserved", None
            
            ip_record.status = "available"
            operation = "unreserve"
            message = "IP address reservation cancelled successfully"
        
        try:
            db.commit()
            db.refresh(ip_record)
            
            # 3. 记录操作日志
            if user_id:
                IPService._log_operation(
                    db=db,
                    user_id=user_id,
                    operation_type=operation,
                    resource_type="ip",
                    resource_id=ip_record.id,
                    details={
                        "ip_address": ip_record.ip_address,
                        "status": ip_record.status
                    }
                )
            
            return True, message, ip_record
            
        except Exception as e:
            db.rollback()
            return False, f"Database error: {str(e)}", None
    
    @staticmethod
    def _log_operation(
        db: Session,
        user_id: int,
        operation_type: str,
        resource_type: str,
        resource_id: int,
        details: dict,
        ip_address: Optional[str] = None
    ):
        """
        记录操作日志
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            operation_type: 操作类型
            resource_type: 资源类型
            resource_id: 资源 ID
            details: 操作详情
            ip_address: 客户端 IP（可选）
        """
        import json
        from app.models.user import User
        
        # 查询用户名
        user = db.query(User).filter(User.id == user_id).first()
        username = user.username if user else "unknown"
        
        log = OperationLog(
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details),
            ip_address=ip_address
        )
        
        db.add(log)
        db.commit()
