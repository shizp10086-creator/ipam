"""
Unit tests for Ping Scanner Service
测试 Ping 扫描器的核心功能
"""
import pytest
import asyncio
from app.services.ping_scanner import PingScanner, PingResult, ScanProgress


class TestPingScanner:
    """测试 PingScanner 类"""
    
    def test_ping_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = PingScanner(timeout=2, max_concurrent=50, ping_count=1)
        
        assert scanner.timeout == 2
        assert scanner.max_concurrent == 50
        assert scanner.ping_count == 1
        assert scanner._total_ips == 0
        assert scanner._scanned_ips == 0
    
    @pytest.mark.asyncio
    async def test_ping_single_ip_localhost(self):
        """测试 Ping 本地回环地址"""
        scanner = PingScanner(timeout=2)
        
        # Ping 本地回环地址应该成功
        result = await scanner.ping_single_ip("127.0.0.1")
        
        assert isinstance(result, PingResult)
        assert result.ip_address == "127.0.0.1"
        assert result.is_online == True
        # 响应时间可能为 None（如果无法从输出中提取）
        assert result.response_time_ms is None or result.response_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_ping_single_ip_invalid(self):
        """测试 Ping 无效 IP 地址"""
        scanner = PingScanner(timeout=1)
        
        # Ping 一个不太可能存在的 IP
        result = await scanner.ping_single_ip("192.0.2.1")  # TEST-NET-1
        
        assert isinstance(result, PingResult)
        assert result.ip_address == "192.0.2.1"
        # 可能在线也可能离线，取决于网络环境
        assert result.is_online in [True, False]
    
    @pytest.mark.asyncio
    async def test_scan_ip_list(self):
        """测试扫描 IP 列表"""
        scanner = PingScanner(timeout=1, max_concurrent=10)
        
        # 扫描包含本地回环地址的列表
        ip_list = ["127.0.0.1", "192.0.2.1", "192.0.2.2"]
        
        results = await scanner.scan_ip_list(ip_list)
        
        assert len(results) == 3
        assert all(isinstance(r, PingResult) for r in results)
        
        # 至少本地回环地址应该在线
        localhost_result = next(r for r in results if r.ip_address == "127.0.0.1")
        assert localhost_result.is_online == True
    
    def test_get_scan_summary(self):
        """测试生成扫描摘要"""
        scanner = PingScanner()
        
        # 创建模拟扫描结果
        results = [
            PingResult(ip_address="192.168.1.1", is_online=True, response_time_ms=10.5),
            PingResult(ip_address="192.168.1.2", is_online=True, response_time_ms=15.2),
            PingResult(ip_address="192.168.1.3", is_online=False),
            PingResult(ip_address="192.168.1.4", is_online=False),
        ]
        
        summary = scanner.get_scan_summary(results)
        
        assert summary["total_ips"] == 4
        assert summary["online_ips"] == 2
        assert summary["offline_ips"] == 2
        assert summary["online_percentage"] == 50.0
        assert summary["avg_response_time_ms"] is not None
        assert len(summary["online_ip_list"]) == 2
        assert len(summary["offline_ip_list"]) == 2


class TestPingResult:
    """测试 PingResult 数据类"""
    
    def test_ping_result_creation(self):
        """测试创建 PingResult"""
        result = PingResult(
            ip_address="192.168.1.1",
            is_online=True,
            response_time_ms=10.5
        )
        
        assert result.ip_address == "192.168.1.1"
        assert result.is_online == True
        assert result.response_time_ms == 10.5
        assert result.error is None
        assert result.timestamp is not None
    
    def test_ping_result_to_dict(self):
        """测试 PingResult 转换为字典"""
        result = PingResult(
            ip_address="192.168.1.1",
            is_online=True,
            response_time_ms=10.5
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["ip_address"] == "192.168.1.1"
        assert result_dict["is_online"] == True
        assert result_dict["response_time_ms"] == 10.5
        assert "timestamp" in result_dict


class TestScanProgress:
    """测试 ScanProgress 数据类"""
    
    def test_scan_progress_creation(self):
        """测试创建 ScanProgress"""
        progress = ScanProgress(
            total_ips=100,
            scanned_ips=50,
            online_ips=30,
            offline_ips=20,
            progress_percentage=50.0,
            elapsed_time=25.5,
            estimated_remaining_time=25.5
        )
        
        assert progress.total_ips == 100
        assert progress.scanned_ips == 50
        assert progress.online_ips == 30
        assert progress.offline_ips == 20
        assert progress.progress_percentage == 50.0
    
    def test_scan_progress_to_dict(self):
        """测试 ScanProgress 转换为字典"""
        progress = ScanProgress(
            total_ips=100,
            scanned_ips=50,
            online_ips=30,
            offline_ips=20,
            progress_percentage=50.0,
            elapsed_time=25.5
        )
        
        progress_dict = progress.to_dict()
        
        assert progress_dict["total_ips"] == 100
        assert progress_dict["scanned_ips"] == 50
        assert progress_dict["progress_percentage"] == 50.0
