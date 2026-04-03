"""
IP 地址工具函数
提供 IP 地址格式验证、网段归属查询、状态转换等功能
"""
import ipaddress
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress


def validate_ip_address(ip_str: str) -> Tuple[bool, Optional[str]]:
    """
    验证 IP 地址格式

    Args:
        ip_str: IP 地址字符

    Returns:
        (is_valid, error_message): 验证结果和错误信
    """
    try:
        ipaddress.ip_address(ip_str)
        return True, None
    except ValueError as e:
        return False, f"Invalid IP address format: {str(e)}"


def find_segment_for_ip(db: Session, ip_str: str) -> Optional[NetworkSegment]:
    """
    查找 IP 地址归属的网

    Args:
        db: 数据库会
        ip_str: IP 地址字符

    Returns:
        NetworkSegment 对象，如果未找到则返None
    """
    try:
        ip_obj = ipaddress.ip_address(ip_str)

        # 查询所有网
        segments = db.query(NetworkSegment).all()

        for segment in segments:
            # 构建网段的网络对
            network = ipaddress.ip_network(f"{segment.network}/{segment.prefix_length}", strict=False)

            # 检IP 是否在网段范围内
            if ip_obj in network:
                return segment

        return None
    except ValueError:
        return None


def is_ip_in_segment(ip_str: str, segment: NetworkSegment) -> bool:
    """
    检IP 地址是否属于指定网段

    Args:
        ip_str: IP 地址字符
        segment: 网段对象

    Returns:
        True 如果 IP 在网段内，否False
    """
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        network = ipaddress.ip_network(f"{segment.network}/{segment.prefix_length}", strict=False)
        return ip_obj in network
    except ValueError:
        return False


def validate_ip_status(status: str) -> Tuple[bool, Optional[str]]:
    """
    验证 IP 地址状态

    Args:
        status: 状态字符串

    Returns:
        (is_valid, error_message): 验证结果和错误信
    """
    valid_statuses = ["available", "used", "reserved"]
    if status not in valid_statuses:
        return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
    return True, None


def transition_ip_status(
    db: Session,
    ip_id: int,
    new_status: str,
    device_id: Optional[int] = None,
    allocated_by: Optional[int] = None
) -> Tuple[bool, Optional[str], Optional[IPAddress]]:
    """
    转换 IP 地址状

    Args:
        db: 数据库会
        ip_id: IP 地址 ID
        new_status: 新状
        device_id: 设备 ID（可选）
        allocated_by: 分配ID（可选）

    Returns:
        (success, error_message, ip_address): 操作结果、错误信息和更新后的 IP 对象
    """
    from datetime import datetime

    # 验证状态
    is_valid, error = validate_ip_status(new_status)
    if not is_valid:
        return False, error, None

    # 查询 IP 地址
    ip_address = db.query(IPAddress).filter(IPAddress.id == ip_id).first()
    if not ip_address:
        return False, "IP address not found", None

    # 状态转换逻辑
    if new_status == "used":
        # 转换为已用状
        if not device_id:
            return False, "Device ID is required when status is 'used'", None
        ip_address.status = "used"
        ip_address.device_id = device_id
        ip_address.allocated_by = allocated_by
        ip_address.allocated_at = datetime.now()

    elif new_status == "available":
        # 转换为空闲状
        ip_address.status = "available"
        ip_address.device_id = None
        ip_address.allocated_by = None
        ip_address.allocated_at = None

    elif new_status == "reserved":
        # 转换为保留状
        ip_address.status = "reserved"
        # 保留状态可以有或没有设备关
        if device_id:
            ip_address.device_id = device_id

    try:
        db.commit()
        db.refresh(ip_address)
        return True, None, ip_address
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}", None


def can_allocate_ip(ip_address: IPAddress) -> Tuple[bool, Optional[str]]:
    """
    检IP 地址是否可以被分

    Args:
        ip_address: IP 地址对象

    Returns:
        (can_allocate, reason): 是否可分配和原因
    """
    if ip_address.status == "used":
        return False, "IP address is already in use"
    elif ip_address.status == "reserved":
        return False, "IP address is reserved"
    elif ip_address.status == "available":
        return True, None
    else:
        return False, f"Unknown IP status: {ip_address.status}"


def calculate_network_range(network: str, prefix_length: int) -> Tuple[str, str, int]:
    """
    计算网段IP 范围

    Args:
        network: 网络地址
        prefix_length: 前缀长度

    Returns:
        (first_ip, last_ip, total_ips): 第一个可IP、最后一个可IP、IP
    """
    net = ipaddress.ip_network(f"{network}/{prefix_length}", strict=False)

    # 排除网络地址和广播地址
    hosts = list(net.hosts())

    if len(hosts) == 0:
        # /31 /32 网段的特殊情
        return str(net.network_address), str(net.broadcast_address), net.num_addresses

    first_ip = str(hosts[0])
    last_ip = str(hosts[-1])
    total_ips = len(hosts)

    return first_ip, last_ip, total_ips


# ==================== 网段管理工具函数 ====================

def validate_cidr(cidr: str) -> Tuple[bool, Optional[str], Optional[Tuple[str, int]]]:
    """
    验证 CIDR 格式

    Args:
        cidr: CIDR 格式字符("192.168.1.0/24")

    Returns:
        (is_valid, error_message, (network, prefix_length)):
        验证结果、错误信息和解析后的网络地址与前缀长度
    """
    try:
        # 检查是否包含斜
        if '/' not in cidr:
            return False, "CIDR format must include prefix length (e.g., 192.168.1.0/24)", None

        # 解析 CIDR
        network = ipaddress.ip_network(cidr, strict=False)

        # 只支IPv4
        if network.version != 4:
            return False, "Only IPv4 networks are supported", None

        # 提取网络地址和前缀长度
        network_addr = str(network.network_address)
        prefix_len = network.prefixlen

        # 验证前缀长度范围 (通常 /8 /30 是合理的)
        if prefix_len < 8 or prefix_len > 30:
            return False, f"Prefix length must be between 8 and 30, got {prefix_len}", None

        return True, None, (network_addr, prefix_len)

    except ValueError as e:
        return False, f"Invalid CIDR format: {str(e)}", None


def calculate_segment_ip_range(network: str, prefix_length: int) -> dict:
    """
    计算网段IP 范围信息

    Args:
        network: 网络地址 ("192.168.1.0")
        prefix_length: 前缀长度 (24)

    Returns:
        包含网段范围信息的字
        {
            'network_address': str,      # 网络地址
            'broadcast_address': str,    # 广播地址
            'first_usable_ip': str,      # 第一个可IP
            'last_usable_ip': str,       # 最后一个可IP
            'total_ips': int,            # IP 数（排除网络地址和广播地址
            'netmask': str,              # 子网掩码
        }
    """
    try:
        net = ipaddress.ip_network(f"{network}/{prefix_length}", strict=False)

        # 获取所有主机地址（排除网络地址和广播地址
        hosts = list(net.hosts())

        if len(hosts) == 0:
            # /31 /32 的特殊情
            return {
                'network_address': str(net.network_address),
                'broadcast_address': str(net.broadcast_address),
                'first_usable_ip': str(net.network_address),
                'last_usable_ip': str(net.broadcast_address),
                'total_ips': net.num_addresses,
                'netmask': str(net.netmask),
            }

        return {
            'network_address': str(net.network_address),
            'broadcast_address': str(net.broadcast_address),
            'first_usable_ip': str(hosts[0]),
            'last_usable_ip': str(hosts[-1]),
            'total_ips': len(hosts),
            'netmask': str(net.netmask),
        }

    except ValueError as e:
        raise ValueError(f"Invalid network parameters: {str(e)}")


def calculate_segment_usage(db: Session, segment_id: int) -> dict:
    """
    计算网段使用

    Args:
        db: 数据库会
        segment_id: 网段 ID

    Returns:
        包含使用率信息的字典:
        {
            'total_ips': int,           # IP 数量
            'used_ips': int,            # 已用 IP 数量
            'available_ips': int,       # 可用 IP 数量 = 总数 - (已用 + 保留 + 在线)
            'reserved_ips': int,        # 保留 IP 数量
            'online_ips': int,          # 在线 IP 数量
            'offline_ips': int,         # 离线 IP 数量
            'usage_rate': float         # 使用率（百分比）
        }
    """
    # 查询网段
    segment = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
    if not segment:
        raise ValueError(f"Network segment with ID {segment_id} not found")

    # 计算IP 数量
    range_info = calculate_segment_ip_range(segment.network, segment.prefix_length)
    total_ips = range_info['total_ips']

    # 查询各状态的 IP 数量
    used_ips = db.query(IPAddress).filter(
        IPAddress.segment_id == segment_id,
        IPAddress.status == "used"
    ).count()

    reserved_ips = db.query(IPAddress).filter(
        IPAddress.segment_id == segment_id,
        IPAddress.status == "reserved"
    ).count()

    # 查询在线和离IP 数量
    online_ips = db.query(IPAddress).filter(
        IPAddress.segment_id == segment_id,
        IPAddress.is_online == True
    ).count()

    # 离线 IP = 已扫描但不在线的 IP
    offline_ips = db.query(IPAddress).filter(
        IPAddress.segment_id == segment_id,
        IPAddress.last_seen.isnot(None),
        IPAddress.is_online == False
    ).count()

    # 可用 IP = 总数 - (已用 IP + 保留 IP + 在线 IP)
    available_ips = total_ips - (used_ips + reserved_ips + online_ips)

    # 计算使用= (已用 IP + 保留 IP + 在线 IP) / IP × 100%
    # 修改后的需
    if total_ips > 0:
        usage_rate = ((used_ips + reserved_ips + online_ips) / total_ips) * 100
    else:
        usage_rate = 0.0

    return {
        'total_ips': total_ips,
        'used_ips': used_ips,
        'available_ips': available_ips,
        'reserved_ips': reserved_ips,
        'online_ips': online_ips,
        'offline_ips': offline_ips,
        'usage_rate': round(usage_rate, 2)
    }
