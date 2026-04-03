"""
设备工具函数
提供 MAC 地址格式验证、设备搜索等功能
"""
import re
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.device import Device


def validate_mac_address(mac_str: str) -> Tuple[bool, Optional[str]]:
    """
    验证 MAC 地址格式

    支持的格式:
    - AA:BB:CC:DD:EE:FF
    - AA-BB-CC-DD-EE-FF
    - AABBCCDDEEFF

    Args:
        mac_str: MAC 地址字符串

    Returns:
        (is_valid, error_message): 验证结果和错误信息
    """
    if not mac_str:
        return False, "MAC address cannot be empty"

    # 移除空格
    mac_str = mac_str.strip()

    # 支持的 MAC 地址格式
    patterns = [
        r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',  # AA:BB:CC:DD:EE:FF 或 AA-BB-CC-DD-EE-FF
        r'^[0-9A-Fa-f]{12}$'  # AABBCCDDEEFF
    ]

    for pattern in patterns:
        if re.match(pattern, mac_str):
            return True, None

    return False, "Invalid MAC address format. Supported formats: AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, AABBCCDDEEFF"


def normalize_mac_address(mac_str: str) -> str:
    """
    标准化 MAC 地址格式为 AA:BB:CC:DD:EE:FF

    Args:
        mac_str: MAC 地址字符串

    Returns:
        标准化后的 MAC 地址
    """
    # 移除所有分隔符
    mac_clean = re.sub(r'[:-]', '', mac_str.upper())

    # 格式化为 AA:BB:CC:DD:EE:FF
    return ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])


def search_devices(
    db: Session,
    keyword: Optional[str] = None,
    device_type: Optional[str] = None,
    owner: Optional[str] = None,
    department: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[Device], int]:
    """
    搜索设备（支持模糊搜索）

    Args:
        db: 数据库会话
        keyword: 搜索关键词（在名称、MAC、责任人中搜索）
        device_type: 设备类型筛选
        owner: 责任人筛选
        department: 部门筛选
        page: 页码
        page_size: 每页数量

    Returns:
        (devices, total): 设备列表和总数
    """
    query = db.query(Device)

    # 关键词模糊搜索
    if keyword:
        keyword_filter = or_(
            Device.name.ilike(f"%{keyword}%"),
            Device.mac_address.ilike(f"%{keyword}%"),
            Device.owner.ilike(f"%{keyword}%")
        )
        query = query.filter(keyword_filter)

    # 设备类型筛选
    if device_type:
        query = query.filter(Device.device_type == device_type)

    # 责任人筛选
    if owner:
        query = query.filter(Device.owner.ilike(f"%{owner}%"))

    # 部门筛选
    if department:
        query = query.filter(Device.department.ilike(f"%{department}%"))

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    devices = query.offset(offset).limit(page_size).all()

    return devices, total


def check_mac_address_exists(db: Session, mac_address: str, exclude_device_id: Optional[int] = None) -> bool:
    """
    检查 MAC 地址是否已存在

    Args:
        db: 数据库会话
        mac_address: MAC 地址
        exclude_device_id: 排除的设备 ID（用于更新时检查）

    Returns:
        True 如果 MAC 地址已存在，否则 False
    """
    query = db.query(Device).filter(Device.mac_address == mac_address)

    if exclude_device_id:
        query = query.filter(Device.id != exclude_device_id)

    return query.first() is not None


def get_device_by_mac(db: Session, mac_address: str) -> Optional[Device]:
    """
    根据 MAC 地址查询设备

    Args:
        db: 数据库会话
        mac_address: MAC 地址

    Returns:
        Device 对象，如果未找到则返回 None
    """
    return db.query(Device).filter(Device.mac_address == mac_address).first()


def get_device_by_id(db: Session, device_id: int) -> Optional[Device]:
    """
    根据 ID 查询设备

    Args:
        db: 数据库会话
        device_id: 设备 ID

    Returns:
        Device 对象，如果未找到则返回 None
    """
    return db.query(Device).filter(Device.id == device_id).first()
