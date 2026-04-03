"""
Device Service
设备管理业务逻辑层
"""
from typing import Tuple, Optional, List
from sqlalchemy.orm import Session
from app.models.device import Device
from app.models.ip_address import IPAddress
from app.utils.device_utils import (
    validate_mac_address,
    normalize_mac_address,
    check_mac_address_exists,
    get_device_by_id
)


class DeviceService:
    """设备管理服务"""

    @staticmethod
    def create_device(
        db: Session,
        name: str,
        mac_address: str,
        owner: str,
        device_type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        department: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        created_by: int = 1
    ) -> Tuple[bool, str, Optional[Device]]:
        """
        创建设备

        Args:
            db: 数据库会话
            name: 设备名称
            mac_address: MAC 地址
            owner: 责任人
            device_type: 设备类型
            manufacturer: 制造商
            model: 型号
            department: 部门
            location: 物理位置
            description: 描述
            created_by: 创建人 ID

        Returns:
            (success, message, device): 操作结果、消息和设备对象
        """
        # 验证 MAC 地址格式
        is_valid, error = validate_mac_address(mac_address)
        if not is_valid:
            return False, error, None

        # 标准化 MAC 地址
        mac_address = normalize_mac_address(mac_address)

        # 检查 MAC 地址是否已存在
        if check_mac_address_exists(db, mac_address):
            return False, f"Device with MAC address {mac_address} already exists", None

        # 创建设备
        device = Device(
            name=name,
            mac_address=mac_address,
            device_type=device_type,
            manufacturer=manufacturer,
            model=model,
            owner=owner,
            department=department,
            location=location,
            description=description,
            created_by=created_by
        )

        try:
            db.add(device)
            db.commit()
            db.refresh(device)
            return True, "Device created successfully", device
        except Exception as e:
            db.rollback()
            return False, f"Failed to create device: {str(e)}", None

    @staticmethod
    def update_device(
        db: Session,
        device_id: int,
        name: Optional[str] = None,
        mac_address: Optional[str] = None,
        device_type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        owner: Optional[str] = None,
        department: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Device]]:
        """
        更新设备信息

        Args:
            db: 数据库会话
            device_id: 设备 ID
            name: 设备名称
            mac_address: MAC 地址
            device_type: 设备类型
            manufacturer: 制造商
            model: 型号
            owner: 责任人
            department: 部门
            location: 物理位置
            description: 描述

        Returns:
            (success, message, device): 操作结果、消息和设备对象
        """
        # 查询设备
        device = get_device_by_id(db, device_id)
        if not device:
            return False, "Device not found", None

        # 如果更新 MAC 地址，需要验证
        if mac_address is not None:
            is_valid, error = validate_mac_address(mac_address)
            if not is_valid:
                return False, error, None

            # 标准化 MAC 地址
            mac_address = normalize_mac_address(mac_address)

            # 检查 MAC 地址是否已被其他设备使用
            if check_mac_address_exists(db, mac_address, exclude_device_id=device_id):
                return False, f"Device with MAC address {mac_address} already exists", None

            device.mac_address = mac_address

        # 更新其他字段
        if name is not None:
            device.name = name
        if device_type is not None:
            device.device_type = device_type
        if manufacturer is not None:
            device.manufacturer = manufacturer
        if model is not None:
            device.model = model
        if owner is not None:
            device.owner = owner
        if department is not None:
            device.department = department
        if location is not None:
            device.location = location
        if description is not None:
            device.description = description

        try:
            db.commit()
            db.refresh(device)
            return True, "Device updated successfully", device
        except Exception as e:
            db.rollback()
            return False, f"Failed to update device: {str(e)}", None

    @staticmethod
    def delete_device(
        db: Session,
        device_id: int
    ) -> Tuple[bool, str]:
        """
        删除设备（自动回收关联的 IP 地址）

        Args:
            db: 数据库会话
            device_id: 设备 ID

        Returns:
            (success, message): 操作结果和消息
        """
        # 查询设备
        device = get_device_by_id(db, device_id)
        if not device:
            return False, "Device not found"

        try:
            # 回收所有关联的 IP 地址
            associated_ips = db.query(IPAddress).filter(
                IPAddress.device_id == device_id
            ).all()

            for ip in associated_ips:
                ip.status = "available"
                ip.device_id = None
                ip.allocated_by = None
                ip.allocated_at = None

            # 删除设备
            db.delete(device)
            db.commit()

            return True, f"Device deleted successfully. {len(associated_ips)} IP(s) released."
        except Exception as e:
            db.rollback()
            return False, f"Failed to delete device: {str(e)}"

    @staticmethod
    def get_device_ips(
        db: Session,
        device_id: int
    ) -> Tuple[bool, str, Optional[List[IPAddress]]]:
        """
        获取设备关联的所有 IP 地址

        Args:
            db: 数据库会话
            device_id: 设备 ID

        Returns:
            (success, message, ips): 操作结果、消息和 IP 地址列表
        """
        # 查询设备
        device = get_device_by_id(db, device_id)
        if not device:
            return False, "Device not found", None

        # 查询关联的 IP 地址
        ips = db.query(IPAddress).filter(
            IPAddress.device_id == device_id
        ).all()

        return True, "Success", ips
