"""
IP Conflict Detection Service
IP 冲突检测服务 - 实现逻辑冲突和物理冲突检测
"""
import asyncio
import platform
import subprocess
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.ip_address import IPAddress


class ConflictResult:
    """冲突检测结果类"""

    def __init__(
        self,
        has_conflict: bool = False,
        conflict_type: Optional[str] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化冲突检测结果

        Args:
            has_conflict: 是否存在冲突
            conflict_type: 冲突类型 (logical/physical)
            message: 冲突消息
            details: 冲突详情
        """
        self.has_conflict = has_conflict
        self.conflict_type = conflict_type
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "has_conflict": self.has_conflict,
            "conflict_type": self.conflict_type,
            "message": self.message,
            "details": self.details
        }


class ConflictDetectionService:
    """冲突检测服务类"""

    @staticmethod
    def check_logical_conflict(
        db: Session,
        ip_address: str
    ) -> ConflictResult:
        """
        检查逻辑冲突
        查询数据库检查 IP 是否已被标记为"已用"或"保留"

        Args:
            db: 数据库会话
            ip_address: 要检查的 IP 地址

        Returns:
            ConflictResult: 冲突检测结果
        """
        # 查询数据库中的 IP 记录
        ip_record = db.query(IPAddress).filter(
            IPAddress.ip_address == ip_address
        ).first()

        # 如果 IP 不存在，没有逻辑冲突
        if not ip_record:
            return ConflictResult(
                has_conflict=False,
                message="No logical conflict - IP address not found in database"
            )

        # 检查 IP 状态
        if ip_record.status == "used":
            # IP 已被使用
            details = {
                "ip_id": ip_record.id,
                "status": ip_record.status,
                "device_id": ip_record.device_id,
                "allocated_at": ip_record.allocated_at.isoformat() if ip_record.allocated_at else None,
                "allocated_by": ip_record.allocated_by
            }

            return ConflictResult(
                has_conflict=True,
                conflict_type="logical",
                message=f"IP address {ip_address} is already in use (status: used)",
                details=details
            )

        elif ip_record.status == "reserved":
            # IP 已被保留
            details = {
                "ip_id": ip_record.id,
                "status": ip_record.status
            }

            return ConflictResult(
                has_conflict=True,
                conflict_type="logical",
                message=f"IP address {ip_address} is reserved (status: reserved)",
                details=details
            )

        # IP 状态为 available，没有逻辑冲突
        return ConflictResult(
            has_conflict=False,
            message=f"No logical conflict - IP address {ip_address} is available"
        )

    @staticmethod
    async def check_physical_conflict_ping(
        ip_address: str,
        timeout: int = 2,
        count: int = 1
    ) -> ConflictResult:
        """
        检查物理冲突（Ping）
        使用 asyncio 实现异步 Ping 功能

        Args:
            ip_address: 要检查的 IP 地址
            timeout: 超时时间（秒）
            count: Ping 次数

        Returns:
            ConflictResult: 冲突检测结果
        """
        try:
            # 根据操作系统选择 ping 命令参数
            system = platform.system().lower()

            if system == "windows":
                # Windows: ping -n count -w timeout_ms ip_address
                cmd = [
                    "ping",
                    "-n", str(count),
                    "-w", str(timeout * 1000),  # Windows 使用毫秒
                    ip_address
                ]
            else:
                # Linux/Unix: ping -c count -W timeout ip_address
                cmd = [
                    "ping",
                    "-c", str(count),
                    "-W", str(timeout),
                    ip_address
                ]

            # 异步执行 ping 命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 等待命令完成
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout + 2  # 额外的超时缓冲
            )

            # 检查返回码
            if process.returncode == 0:
                # Ping 成功，存在物理冲突
                output = stdout.decode('utf-8', errors='ignore')

                # 尝试提取响应时间
                response_time = None
                if system == "windows":
                    # Windows 格式: time=XXms 或 时间=XXms
                    import re
                    match = re.search(r'(?:time|时间)[=<](\d+)ms', output, re.IGNORECASE)
                    if match:
                        response_time = int(match.group(1))
                else:
                    # Linux 格式: time=XX.X ms
                    import re
                    match = re.search(r'time=(\d+\.?\d*)\s*ms', output)
                    if match:
                        response_time = float(match.group(1))

                details = {
                    "ping_successful": True,
                    "response_time_ms": response_time,
                    "output": output[:500]  # 限制输出长度
                }

                return ConflictResult(
                    has_conflict=True,
                    conflict_type="physical",
                    message=f"IP address {ip_address} is responding to ping (physical conflict detected)",
                    details=details
                )
            else:
                # Ping 失败，没有物理冲突
                return ConflictResult(
                    has_conflict=False,
                    message=f"No physical conflict - IP address {ip_address} is not responding to ping"
                )

        except asyncio.TimeoutError:
            # 超时，视为没有响应
            return ConflictResult(
                has_conflict=False,
                message=f"No physical conflict - Ping timeout for IP address {ip_address}"
            )

        except Exception as e:
            # 其他错误，返回错误信息但不视为冲突
            return ConflictResult(
                has_conflict=False,
                message=f"Ping check failed: {str(e)}",
                details={"error": str(e)}
            )

    @staticmethod
    async def check_physical_conflict_arp(
        ip_address: str,
        timeout: int = 2
    ) -> ConflictResult:
        """
        检查物理冲突（ARP）
        实现 ARP 协议检测，检测 IP 与 MAC 地址映射关系
        注意：此功能可选，根据平台支持情况使用

        Args:
            ip_address: 要检查的 IP 地址
            timeout: 超时时间（秒）

        Returns:
            ConflictResult: 冲突检测结果
        """
        try:
            system = platform.system().lower()

            if system == "windows":
                # Windows: arp -a ip_address
                cmd = ["arp", "-a", ip_address]
            else:
                # Linux/Unix: arp -n ip_address 或 ip neigh show ip_address
                # 优先使用 ip 命令（更现代）
                cmd = ["ip", "neigh", "show", ip_address]

            # 异步执行 ARP 命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 等待命令完成
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            output = stdout.decode('utf-8', errors='ignore')

            # 解析 ARP 输出
            mac_address = None

            if system == "windows":
                # Windows 格式: IP地址 物理地址 类型
                # 例如: 192.168.1.1    aa-bb-cc-dd-ee-ff    动态
                import re
                # 匹配 MAC 地址格式
                match = re.search(
                    r'([0-9a-fA-F]{2}[-:]){5}[0-9a-fA-F]{2}',
                    output
                )
                if match:
                    mac_address = match.group(0)
            else:
                # Linux 格式: IP dev interface lladdr MAC state STATE
                # 例如: 192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
                import re
                match = re.search(
                    r'lladdr\s+(([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})',
                    output
                )
                if match:
                    mac_address = match.group(1)

            if mac_address:
                # 找到 MAC 地址，存在物理冲突
                details = {
                    "arp_found": True,
                    "mac_address": mac_address,
                    "output": output[:500]
                }

                return ConflictResult(
                    has_conflict=True,
                    conflict_type="physical",
                    message=f"IP address {ip_address} has ARP entry with MAC {mac_address} (physical conflict detected)",
                    details=details
                )
            else:
                # 没有找到 MAC 地址，没有物理冲突
                return ConflictResult(
                    has_conflict=False,
                    message=f"No physical conflict - No ARP entry found for IP address {ip_address}"
                )

        except asyncio.TimeoutError:
            # 超时
            return ConflictResult(
                has_conflict=False,
                message=f"No physical conflict - ARP check timeout for IP address {ip_address}"
            )

        except FileNotFoundError:
            # 命令不存在（如 Linux 上没有 ip 命令）
            return ConflictResult(
                has_conflict=False,
                message="ARP check not available - command not found",
                details={"error": "ARP command not available on this system"}
            )

        except Exception as e:
            # 其他错误
            return ConflictResult(
                has_conflict=False,
                message=f"ARP check failed: {str(e)}",
                details={"error": str(e)}
            )

    @staticmethod
    async def check_ip_conflict(
        db: Session,
        ip_address: str,
        check_ping: bool = True,
        check_arp: bool = False,
        ping_timeout: int = 2,
        arp_timeout: int = 2
    ) -> ConflictResult:
        """
        综合冲突检测
        按顺序执行逻辑检测和物理检测，返回详细的冲突信息

        Args:
            db: 数据库会话
            ip_address: 要检查的 IP 地址
            check_ping: 是否执行 Ping 检测
            check_arp: 是否执行 ARP 检测
            ping_timeout: Ping 超时时间（秒）
            arp_timeout: ARP 超时时间（秒）

        Returns:
            ConflictResult: 冲突检测结果
        """
        # 1. 首先执行逻辑冲突检测
        logical_result = ConflictDetectionService.check_logical_conflict(db, ip_address)

        if logical_result.has_conflict:
            # 如果存在逻辑冲突，直接返回
            return logical_result

        # 2. 逻辑检测通过，执行物理冲突检测
        physical_results = []

        # 2.1 Ping 检测
        if check_ping:
            ping_result = await ConflictDetectionService.check_physical_conflict_ping(
                ip_address,
                timeout=ping_timeout
            )
            physical_results.append(("ping", ping_result))

            if ping_result.has_conflict:
                # Ping 检测到冲突，直接返回
                return ping_result

        # 2.2 ARP 检测
        if check_arp:
            arp_result = await ConflictDetectionService.check_physical_conflict_arp(
                ip_address,
                timeout=arp_timeout
            )
            physical_results.append(("arp", arp_result))

            if arp_result.has_conflict:
                # ARP 检测到冲突，直接返回
                return arp_result

        # 3. 所有检测都通过，没有冲突
        check_details = {
            "logical_check": "passed",
            "physical_checks": [
                {
                    "type": check_type,
                    "result": result.message
                }
                for check_type, result in physical_results
            ]
        }

        return ConflictResult(
            has_conflict=False,
            message=f"No conflict detected for IP address {ip_address}",
            details=check_details
        )
