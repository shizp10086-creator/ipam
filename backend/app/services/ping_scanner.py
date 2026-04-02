"""
Ping Scanner Service
IP Ping 扫描服务 - 实现并发 Ping 扫描功能和扫描结果处理
"""
import asyncio
import platform
import time
import ipaddress
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.ip_address import IPAddress
from app.models.scan_history import ScanHistory
from app.models.network_segment import NetworkSegment


@dataclass
class PingResult:
    """单个 IP 的 Ping 结果"""
    ip_address: str
    is_online: bool
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "ip_address": self.ip_address,
            "is_online": self.is_online,
            "response_time_ms": self.response_time_ms,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class ScanProgress:
    """扫描进度信息"""
    total_ips: int
    scanned_ips: int
    online_ips: int
    offline_ips: int
    progress_percentage: float
    elapsed_time: float
    estimated_remaining_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "total_ips": self.total_ips,
            "scanned_ips": self.scanned_ips,
            "online_ips": self.online_ips,
            "offline_ips": self.offline_ips,
            "progress_percentage": round(self.progress_percentage, 2),
            "elapsed_time": round(self.elapsed_time, 2),
            "estimated_remaining_time": round(self.estimated_remaining_time, 2) if self.estimated_remaining_time else None
        }


class PingScanner:
    """并发 Ping 扫描器"""
    
    def __init__(
        self,
        timeout: int = 2,
        max_concurrent: int = 50,
        ping_count: int = 1,
        use_proxy: bool = False,
        proxy_url: str = "http://host.docker.internal:8001",
        source_ip: str = None
    ):
        """
        初始化 Ping 扫描器
        
        Args:
            timeout: 单个 Ping 的超时时间（秒）
            max_concurrent: 最大并发数
            ping_count: 每个 IP 的 Ping 次数
            use_proxy: 是否使用 Ping 代理服务
            proxy_url: Ping 代理服务的 URL
            source_ip: 源 IP 地址（用于指定从哪个网络接口发送 ping）
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.ping_count = ping_count
        self.system = platform.system().lower()
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        self.source_ip = source_ip
        
        # 扫描状态
        self._total_ips = 0
        self._scanned_ips = 0
        self._online_ips = 0
        self._offline_ips = 0
        self._start_time = None
        self._progress_callback: Optional[Callable[[ScanProgress], None]] = None
    
    async def ping_single_ip(self, ip_address: str) -> PingResult:
        """
        Ping 单个 IP 地址
        
        Args:
            ip_address: 要 Ping 的 IP 地址
            
        Returns:
            PingResult: Ping 结果
        """
        if self.use_proxy:
            return await self._ping_via_proxy(ip_address)
        else:
            return await self._ping_direct(ip_address)
    
    async def _ping_via_proxy(self, ip_address: str) -> PingResult:
        """
        通过代理服务 Ping IP
        
        Args:
            ip_address: 要 Ping 的 IP 地址
            
        Returns:
            PingResult: Ping 结果
        """
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "ip_address": ip_address,
                    "timeout": self.timeout,
                    "count": self.ping_count
                }
                # 如果配置了源 IP，添加到请求中
                if self.source_ip:
                    payload["source_ip"] = self.source_ip
                
                async with session.post(
                    f"{self.proxy_url}/ping",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout + 2)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return PingResult(
                            ip_address=ip_address,
                            is_online=data.get('is_online', False),
                            response_time_ms=None,  # 代理暂不返回响应时间
                            error=data.get('error')
                        )
                    else:
                        return PingResult(
                            ip_address=ip_address,
                            is_online=False,
                            error=f"Proxy error: {response.status}"
                        )
        except Exception as e:
            return PingResult(
                ip_address=ip_address,
                is_online=False,
                error=f"Proxy connection error: {str(e)}"
            )
    
    async def _ping_direct(self, ip_address: str) -> PingResult:
        """
        直接 Ping IP（原有实现）
        
        Args:
            ip_address: 要 Ping 的 IP 地址
            
        Returns:
            PingResult: Ping 结果
        """
        try:
            # 根据操作系统选择 ping 命令参数
            if self.system == "windows":
                # Windows: ping -n count -w timeout_ms ip_address
                cmd = [
                    "ping",
                    "-n", str(self.ping_count),
                    "-w", str(self.timeout * 1000),  # Windows 使用毫秒
                ]
                # Windows: 使用 -S 参数指定源 IP
                if self.source_ip:
                    cmd.extend(["-S", self.source_ip])
                cmd.append(ip_address)
            else:
                # Linux/Unix: ping -c count -W timeout ip_address
                cmd = [
                    "ping",
                    "-c", str(self.ping_count),
                    "-W", str(self.timeout),
                ]
                # Linux: 使用 -I 参数指定源 IP 或网络接口
                if self.source_ip:
                    cmd.extend(["-I", self.source_ip])
                cmd.append(ip_address)
            
            # 异步执行 ping 命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 等待命令完成
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout + 2  # 额外的超时缓冲
            )
            
            # 检查返回码
            if process.returncode == 0:
                # Ping 成功
                output = stdout.decode('utf-8', errors='ignore')
                
                # 尝试提取响应时间
                response_time = self._extract_response_time(output)
                
                return PingResult(
                    ip_address=ip_address,
                    is_online=True,
                    response_time_ms=response_time
                )
            else:
                # Ping 失败
                return PingResult(
                    ip_address=ip_address,
                    is_online=False
                )
        
        except asyncio.TimeoutError:
            # 超时
            return PingResult(
                ip_address=ip_address,
                is_online=False,
                error="Timeout"
            )
        
        except Exception as e:
            # 其他错误
            return PingResult(
                ip_address=ip_address,
                is_online=False,
                error=str(e)
            )
    
    def _extract_response_time(self, output: str) -> Optional[float]:
        """
        从 Ping 输出中提取响应时间
        
        Args:
            output: Ping 命令的输出
            
        Returns:
            响应时间（毫秒），如果无法提取则返回 None
        """
        import re
        
        try:
            if self.system == "windows":
                # Windows 格式: time=XXms 或 时间=XXms 或 time<1ms
                match = re.search(r'(?:time|时间)[=<](\d+)ms', output, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                # 处理 time<1ms 的情况
                if re.search(r'(?:time|时间)<1ms', output, re.IGNORECASE):
                    return 0.5  # 返回一个小于 1 的值
            else:
                # Linux 格式: time=XX.X ms
                match = re.search(r'time=(\d+\.?\d*)\s*ms', output)
                if match:
                    return float(match.group(1))
        except Exception:
            pass
        
        return None
    
    async def _scan_with_semaphore(
        self,
        ip_addresses: List[str],
        semaphore: asyncio.Semaphore
    ) -> List[PingResult]:
        """
        使用信号量控制并发的扫描
        
        Args:
            ip_addresses: 要扫描的 IP 地址列表
            semaphore: 并发控制信号量
            
        Returns:
            扫描结果列表
        """
        async def scan_with_limit(ip: str) -> PingResult:
            async with semaphore:
                result = await self.ping_single_ip(ip)
                
                # 更新统计信息
                self._scanned_ips += 1
                if result.is_online:
                    self._online_ips += 1
                else:
                    self._offline_ips += 1
                
                # 调用进度回调
                if self._progress_callback:
                    progress = self._get_current_progress()
                    self._progress_callback(progress)
                
                return result
        
        # 并发执行所有 Ping 任务
        tasks = [scan_with_limit(ip) for ip in ip_addresses]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def _get_current_progress(self) -> ScanProgress:
        """
        获取当前扫描进度
        
        Returns:
            ScanProgress: 扫描进度信息
        """
        elapsed_time = time.time() - self._start_time if self._start_time else 0
        progress_percentage = (self._scanned_ips / self._total_ips * 100) if self._total_ips > 0 else 0
        
        # 估算剩余时间
        estimated_remaining_time = None
        if self._scanned_ips > 0 and progress_percentage < 100:
            avg_time_per_ip = elapsed_time / self._scanned_ips
            remaining_ips = self._total_ips - self._scanned_ips
            estimated_remaining_time = avg_time_per_ip * remaining_ips
        
        return ScanProgress(
            total_ips=self._total_ips,
            scanned_ips=self._scanned_ips,
            online_ips=self._online_ips,
            offline_ips=self._offline_ips,
            progress_percentage=progress_percentage,
            elapsed_time=elapsed_time,
            estimated_remaining_time=estimated_remaining_time
        )
    
    async def scan_ip_range(
        self,
        start_ip: str,
        end_ip: str,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> List[PingResult]:
        """
        扫描 IP 地址范围
        
        Args:
            start_ip: 起始 IP 地址
            end_ip: 结束 IP 地址
            progress_callback: 进度回调函数
            
        Returns:
            扫描结果列表
        """
        # 生成 IP 地址列表
        start = ipaddress.IPv4Address(start_ip)
        end = ipaddress.IPv4Address(end_ip)
        
        ip_addresses = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start), int(end) + 1)]
        
        return await self.scan_ip_list(ip_addresses, progress_callback)
    
    async def scan_network_segment(
        self,
        network: str,
        prefix_length: int,
        exclude_network_broadcast: bool = True,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> List[PingResult]:
        """
        扫描整个网段
        
        Args:
            network: 网络地址（如 192.168.1.0）
            prefix_length: 前缀长度（如 24）
            exclude_network_broadcast: 是否排除网络地址和广播地址
            progress_callback: 进度回调函数
            
        Returns:
            扫描结果列表
        """
        # 创建网络对象
        net = ipaddress.IPv4Network(f"{network}/{prefix_length}", strict=False)
        
        # 生成 IP 地址列表
        if exclude_network_broadcast:
            # 排除网络地址和广播地址
            ip_addresses = [str(ip) for ip in net.hosts()]
        else:
            # 包含所有地址
            ip_addresses = [str(ip) for ip in net]
        
        return await self.scan_ip_list(ip_addresses, progress_callback)
    
    async def scan_ip_list(
        self,
        ip_addresses: List[str],
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> List[PingResult]:
        """
        扫描 IP 地址列表
        
        Args:
            ip_addresses: 要扫描的 IP 地址列表
            progress_callback: 进度回调函数
            
        Returns:
            扫描结果列表
        """
        # 初始化扫描状态
        self._total_ips = len(ip_addresses)
        self._scanned_ips = 0
        self._online_ips = 0
        self._offline_ips = 0
        self._start_time = time.time()
        self._progress_callback = progress_callback
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 执行扫描
        results = await self._scan_with_semaphore(ip_addresses, semaphore)
        
        return results
    
    def get_scan_summary(self, results: List[PingResult]) -> Dict[str, Any]:
        """
        生成扫描摘要
        
        Args:
            results: 扫描结果列表
            
        Returns:
            扫描摘要字典
        """
        online_ips = [r for r in results if r.is_online]
        offline_ips = [r for r in results if not r.is_online]
        
        # 计算平均响应时间
        response_times = [r.response_time_ms for r in online_ips if r.response_time_ms is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        return {
            "total_ips": len(results),
            "online_ips": len(online_ips),
            "offline_ips": len(offline_ips),
            "online_percentage": round(len(online_ips) / len(results) * 100, 2) if results else 0,
            "avg_response_time_ms": round(avg_response_time, 2) if avg_response_time else None,
            "online_ip_list": [r.ip_address for r in online_ips],
            "offline_ip_list": [r.ip_address for r in offline_ips]
        }



class ScanResultProcessor:
    """扫描结果处理器"""
    
    @staticmethod
    def update_ip_scan_results(
        db: Session,
        scan_results: List[PingResult]
    ) -> Dict[str, Any]:
        """
        更新 IP 地址的扫描结果
        更新 last_seen 和 is_online 字段
        
        Args:
            db: 数据库会话
            scan_results: 扫描结果列表
            
        Returns:
            更新统计信息
        """
        updated_count = 0
        not_found_count = 0
        
        for result in scan_results:
            # 查询数据库中的 IP 记录
            ip_record = db.query(IPAddress).filter(
                IPAddress.ip_address == result.ip_address
            ).first()
            
            if ip_record:
                # 更新扫描结果
                ip_record.is_online = result.is_online
                ip_record.last_seen = result.timestamp
                updated_count += 1
            else:
                not_found_count += 1
        
        # 提交更改
        db.commit()
        
        return {
            "updated_count": updated_count,
            "not_found_count": not_found_count,
            "total_scanned": len(scan_results)
        }
    
    @staticmethod
    def identify_unregistered_ips(
        db: Session,
        segment_id: int,
        scan_results: List[PingResult]
    ) -> List[Dict[str, Any]]:
        """
        标识未注册的在线 IP
        找出在网络中在线但未在数据库中注册的 IP 地址
        
        Args:
            db: 数据库会话
            segment_id: 网段 ID
            scan_results: 扫描结果列表
            
        Returns:
            未注册的在线 IP 列表
        """
        unregistered_ips = []
        
        # 获取在线的 IP
        online_results = [r for r in scan_results if r.is_online]
        
        for result in online_results:
            # 检查 IP 是否在数据库中注册
            ip_record = db.query(IPAddress).filter(
                IPAddress.ip_address == result.ip_address,
                IPAddress.segment_id == segment_id
            ).first()
            
            if not ip_record:
                # IP 未注册
                unregistered_ips.append({
                    "ip_address": result.ip_address,
                    "response_time_ms": result.response_time_ms,
                    "detected_at": result.timestamp.isoformat() if result.timestamp else None
                })
        
        return unregistered_ips
    
    @staticmethod
    def generate_scan_report(
        db: Session,
        segment_id: int,
        scan_results: List[PingResult],
        scan_duration: float
    ) -> Dict[str, Any]:
        """
        生成扫描报告
        
        Args:
            db: 数据库会话
            segment_id: 网段 ID
            scan_results: 扫描结果列表
            scan_duration: 扫描耗时（秒）
            
        Returns:
            扫描报告
        """
        # 获取网段信息
        segment = db.query(NetworkSegment).filter(
            NetworkSegment.id == segment_id
        ).first()
        
        if not segment:
            raise ValueError(f"Network segment with id {segment_id} not found")
        
        # 统计信息
        online_ips = [r for r in scan_results if r.is_online]
        offline_ips = [r for r in scan_results if not r.is_online]
        
        # 计算平均响应时间
        response_times = [r.response_time_ms for r in online_ips if r.response_time_ms is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # 标识未注册的在线 IP
        unregistered_ips = ScanResultProcessor.identify_unregistered_ips(
            db, segment_id, scan_results
        )
        
        # 获取已注册的在线 IP
        registered_online_ips = []
        for result in online_ips:
            ip_record = db.query(IPAddress).filter(
                IPAddress.ip_address == result.ip_address,
                IPAddress.segment_id == segment_id
            ).first()
            
            if ip_record:
                registered_online_ips.append({
                    "ip_address": result.ip_address,
                    "status": ip_record.status,
                    "device_id": ip_record.device_id,
                    "response_time_ms": result.response_time_ms
                })
        
        # 生成报告
        report = {
            "segment_info": {
                "id": segment.id,
                "name": segment.name,
                "network": f"{segment.network}/{segment.prefix_length}"
            },
            "scan_summary": {
                "total_ips": len(scan_results),
                "online_ips": len(online_ips),
                "offline_ips": len(offline_ips),
                "online_percentage": round(len(online_ips) / len(scan_results) * 100, 2) if scan_results else 0,
                "avg_response_time_ms": round(avg_response_time, 2) if avg_response_time else None,
                "scan_duration": round(scan_duration, 2)
            },
            "registered_online_ips": registered_online_ips,
            "unregistered_online_ips": unregistered_ips,
            "unregistered_count": len(unregistered_ips),
            "scan_timestamp": datetime.utcnow().isoformat()
        }
        
        return report
    
    @staticmethod
    def save_scan_history(
        db: Session,
        segment_id: int,
        scan_type: str,
        scan_results: List[PingResult],
        scan_duration: float,
        user_id: int
    ) -> ScanHistory:
        """
        持久化扫描历史记录
        
        Args:
            db: 数据库会话
            segment_id: 网段 ID
            scan_type: 扫描类型（ping/arp）
            scan_results: 扫描结果列表
            scan_duration: 扫描耗时（秒）
            user_id: 发起人 ID
            
        Returns:
            ScanHistory: 保存的扫描历史记录
        """
        # 统计信息
        online_ips = len([r for r in scan_results if r.is_online])
        
        # 生成详细结果（JSON 格式）
        detailed_results = {
            "scan_results": [r.to_dict() for r in scan_results],
            "summary": {
                "total_ips": len(scan_results),
                "online_ips": online_ips,
                "offline_ips": len(scan_results) - online_ips
            }
        }
        
        # 创建扫描历史记录
        scan_history = ScanHistory(
            segment_id=segment_id,
            scan_type=scan_type,
            total_ips=len(scan_results),
            online_ips=online_ips,
            duration=scan_duration,
            results=json.dumps(detailed_results, ensure_ascii=False),
            created_by=user_id
        )
        
        db.add(scan_history)
        db.commit()
        db.refresh(scan_history)
        
        return scan_history
    
    @staticmethod
    async def process_scan_results(
        db: Session,
        segment_id: int,
        scan_results: List[PingResult],
        scan_duration: float,
        user_id: int,
        scan_type: str = "ping"
    ) -> Dict[str, Any]:
        """
        处理扫描结果的完整流程
        1. 更新 IP 地址的 last_seen 和 is_online 字段
        2. 标识未注册的在线 IP
        3. 生成扫描报告
        4. 持久化扫描历史记录
        
        Args:
            db: 数据库会话
            segment_id: 网段 ID
            scan_results: 扫描结果列表
            scan_duration: 扫描耗时（秒）
            user_id: 发起人 ID
            scan_type: 扫描类型（ping/arp）
            
        Returns:
            处理结果，包含报告和历史记录 ID
        """
        # 1. 更新 IP 地址扫描结果
        update_stats = ScanResultProcessor.update_ip_scan_results(db, scan_results)
        
        # 2. 生成扫描报告
        report = ScanResultProcessor.generate_scan_report(
            db, segment_id, scan_results, scan_duration
        )
        
        # 3. 保存扫描历史
        scan_history = ScanResultProcessor.save_scan_history(
            db, segment_id, scan_type, scan_results, scan_duration, user_id
        )
        
        # 4. 返回处理结果（扁平化格式，方便前端使用）
        return {
            "scan_history_id": scan_history.id,
            "total_ips": report["scan_summary"]["total_ips"],
            "online_ips": report["scan_summary"]["online_ips"],
            "offline_ips": report["scan_summary"]["offline_ips"],
            "duration": scan_duration,
            "report": report,
            "update_stats": update_stats
        }
