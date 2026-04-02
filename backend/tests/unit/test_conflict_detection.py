"""
Unit tests for IP Conflict Detection Service
测试 IP 冲突检测服务的各项功能
"""
import pytest
import asyncio
from app.services.conflict_detection import ConflictDetectionService, ConflictResult
from app.models.ip_address import IPAddress


class TestLogicalConflictDetection:
    """测试逻辑冲突检测"""
    
    def test_no_conflict_ip_not_in_database(self, db_session):
        """
        测试：IP 不在数据库中，没有逻辑冲突
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address="192.168.1.100"
        )
        
        assert result.has_conflict is False
        assert "not found in database" in result.message
    
    def test_no_conflict_ip_available(self, db_session, test_available_ip):
        """
        测试：IP 状态为 available，没有逻辑冲突
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address=test_available_ip.ip_address
        )
        
        assert result.has_conflict is False
        assert "available" in result.message
    
    def test_conflict_ip_used(self, db_session, test_used_ip):
        """
        测试：IP 状态为 used，存在逻辑冲突
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address=test_used_ip.ip_address
        )
        
        assert result.has_conflict is True
        assert result.conflict_type == "logical"
        assert "already in use" in result.message
        assert result.details["status"] == "used"
        assert result.details["device_id"] == test_used_ip.device_id
    
    def test_conflict_ip_reserved(self, db_session, test_reserved_ip):
        """
        测试：IP 状态为 reserved，存在逻辑冲突
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address=test_reserved_ip.ip_address
        )
        
        assert result.has_conflict is True
        assert result.conflict_type == "logical"
        assert "reserved" in result.message
        assert result.details["status"] == "reserved"


class TestPhysicalConflictDetectionPing:
    """测试物理冲突检测（Ping）"""
    
    @pytest.mark.asyncio
    async def test_ping_localhost_responds(self):
        """
        测试：Ping localhost 应该有响应（物理冲突）
        """
        result = await ConflictDetectionService.check_physical_conflict_ping(
            ip_address="127.0.0.1",
            timeout=2
        )
        
        # localhost 应该总是响应
        assert result.has_conflict is True
        assert result.conflict_type == "physical"
        assert "responding to ping" in result.message
        assert result.details["ping_successful"] is True
    
    @pytest.mark.asyncio
    async def test_ping_nonexistent_ip_no_response(self):
        """
        测试：Ping 不存在的 IP 应该没有响应（无冲突）
        """
        # 使用一个不太可能存在的 IP
        result = await ConflictDetectionService.check_physical_conflict_ping(
            ip_address="192.0.2.254",  # TEST-NET-1 保留地址
            timeout=1,
            count=1
        )
        
        # 应该没有响应
        assert result.has_conflict is False
        assert "not responding" in result.message or "timeout" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_ping_timeout_handling(self):
        """
        测试：Ping 超时处理
        """
        result = await ConflictDetectionService.check_physical_conflict_ping(
            ip_address="192.0.2.1",  # TEST-NET-1 保留地址
            timeout=1
        )
        
        # 超时应该视为无冲突
        assert result.has_conflict is False


class TestPhysicalConflictDetectionARP:
    """测试物理冲突检测（ARP）"""
    
    @pytest.mark.asyncio
    async def test_arp_check_executes(self):
        """
        测试：ARP 检测能够执行（不一定找到结果）
        """
        result = await ConflictDetectionService.check_physical_conflict_arp(
            ip_address="192.168.1.1",
            timeout=2
        )
        
        # 结果应该是有效的 ConflictResult 对象
        assert isinstance(result, ConflictResult)
        assert isinstance(result.has_conflict, bool)
        assert isinstance(result.message, str)


class TestIntegratedConflictDetection:
    """测试综合冲突检测"""
    
    @pytest.mark.asyncio
    async def test_logical_conflict_stops_physical_check(self, db_session, test_used_ip):
        """
        测试：逻辑冲突检测失败时，不执行物理检测
        """
        result = await ConflictDetectionService.check_ip_conflict(
            db=db_session,
            ip_address=test_used_ip.ip_address,
            check_ping=True,
            check_arp=True
        )
        
        # 应该检测到逻辑冲突
        assert result.has_conflict is True
        assert result.conflict_type == "logical"
        assert "already in use" in result.message
    
    @pytest.mark.asyncio
    async def test_no_conflict_all_checks_pass(self, db_session):
        """
        测试：所有检测都通过，没有冲突
        """
        result = await ConflictDetectionService.check_ip_conflict(
            db=db_session,
            ip_address="192.0.2.100",  # 不在数据库中且不会响应的 IP
            check_ping=True,
            check_arp=False,
            ping_timeout=1
        )
        
        # 应该没有冲突
        assert result.has_conflict is False
        assert "No conflict detected" in result.message
        assert "logical_check" in result.details
        assert result.details["logical_check"] == "passed"
    
    @pytest.mark.asyncio
    async def test_physical_conflict_detected_by_ping(self, db_session):
        """
        测试：物理冲突通过 Ping 检测到
        """
        result = await ConflictDetectionService.check_ip_conflict(
            db=db_session,
            ip_address="127.0.0.1",  # localhost 会响应
            check_ping=True,
            check_arp=False
        )
        
        # 应该检测到物理冲突
        assert result.has_conflict is True
        assert result.conflict_type == "physical"
        assert "responding to ping" in result.message
    
    @pytest.mark.asyncio
    async def test_skip_ping_check(self, db_session):
        """
        测试：跳过 Ping 检测
        """
        result = await ConflictDetectionService.check_ip_conflict(
            db=db_session,
            ip_address="127.0.0.1",
            check_ping=False,  # 不执行 Ping
            check_arp=False
        )
        
        # 只执行逻辑检测，localhost 不在数据库中，所以无冲突
        assert result.has_conflict is False
    
    @pytest.mark.asyncio
    async def test_conflict_result_to_dict(self, db_session, test_used_ip):
        """
        测试：ConflictResult 转换为字典
        """
        result = await ConflictDetectionService.check_ip_conflict(
            db=db_session,
            ip_address=test_used_ip.ip_address
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "has_conflict" in result_dict
        assert "conflict_type" in result_dict
        assert "message" in result_dict
        assert "details" in result_dict
        assert result_dict["has_conflict"] is True


class TestConflictDetectionErrorHandling:
    """测试冲突检测的错误处理"""
    
    @pytest.mark.asyncio
    async def test_ping_invalid_ip_format(self):
        """
        测试：无效的 IP 格式处理
        注意：此测试验证服务的健壮性
        """
        # 传入无效 IP，ping 命令应该失败但不抛出异常
        result = await ConflictDetectionService.check_physical_conflict_ping(
            ip_address="invalid.ip.address",
            timeout=1
        )
        
        # 应该返回无冲突（因为 ping 失败）
        assert result.has_conflict is False


class TestConflictDetectionErrorMessageFormat:
    """测试冲突检测的错误信息格式（需求 4.6）"""
    
    def test_logical_conflict_error_message_format_used(self, db_session, test_used_ip):
        """
        测试：逻辑冲突（已用）错误信息格式
        验证需求 4.2, 4.6：返回详细的逻辑冲突错误信息
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address=test_used_ip.ip_address
        )
        
        # 验证错误信息格式
        assert result.has_conflict is True
        assert result.conflict_type == "logical"
        assert result.message is not None
        assert len(result.message) > 0
        assert test_used_ip.ip_address in result.message
        assert "used" in result.message.lower()
        
        # 验证详细信息包含必要字段
        assert "ip_id" in result.details
        assert "status" in result.details
        assert "device_id" in result.details
        assert result.details["status"] == "used"
        assert result.details["device_id"] == test_used_ip.device_id
    
    def test_logical_conflict_error_message_format_reserved(self, db_session, test_reserved_ip):
        """
        测试：逻辑冲突（保留）错误信息格式
        验证需求 4.2, 4.6：返回详细的逻辑冲突错误信息
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address=test_reserved_ip.ip_address
        )
        
        # 验证错误信息格式
        assert result.has_conflict is True
        assert result.conflict_type == "logical"
        assert result.message is not None
        assert len(result.message) > 0
        assert test_reserved_ip.ip_address in result.message
        assert "reserved" in result.message.lower()
        
        # 验证详细信息包含必要字段
        assert "ip_id" in result.details
        assert "status" in result.details
        assert result.details["status"] == "reserved"
    
    @pytest.mark.asyncio
    async def test_physical_conflict_error_message_format_ping(self):
        """
        测试：物理冲突（Ping）错误信息格式
        验证需求 4.5, 4.6：返回详细的物理冲突错误信息
        """
        result = await ConflictDetectionService.check_physical_conflict_ping(
            ip_address="127.0.0.1",
            timeout=2
        )
        
        # 验证错误信息格式
        assert result.has_conflict is True
        assert result.conflict_type == "physical"
        assert result.message is not None
        assert len(result.message) > 0
        assert "127.0.0.1" in result.message
        assert "ping" in result.message.lower()
        
        # 验证详细信息包含必要字段
        assert "ping_successful" in result.details
        assert result.details["ping_successful"] is True
        # 响应时间字段应该存在（即使值可能为 None）
        assert "response_time_ms" in result.details
    
    @pytest.mark.asyncio
    async def test_conflict_result_structure(self, db_session, test_used_ip):
        """
        测试：ConflictResult 对象结构完整性
        验证需求 4.6：确保错误信息格式统一
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address=test_used_ip.ip_address
        )
        
        # 验证 ConflictResult 对象的所有属性
        assert hasattr(result, 'has_conflict')
        assert hasattr(result, 'conflict_type')
        assert hasattr(result, 'message')
        assert hasattr(result, 'details')
        
        # 验证属性类型
        assert isinstance(result.has_conflict, bool)
        assert isinstance(result.conflict_type, str) or result.conflict_type is None
        assert isinstance(result.message, str)
        assert isinstance(result.details, dict)
    
    @pytest.mark.asyncio
    async def test_no_conflict_message_format(self, db_session):
        """
        测试：无冲突时的消息格式
        验证需求 4.6：确保成功情况下也有清晰的消息
        """
        result = await ConflictDetectionService.check_ip_conflict(
            db=db_session,
            ip_address="192.0.2.200",
            check_ping=True,
            check_arp=False,
            ping_timeout=1
        )
        
        # 验证无冲突时的消息格式
        assert result.has_conflict is False
        assert result.message is not None
        assert len(result.message) > 0
        assert "192.0.2.200" in result.message
        assert "no conflict" in result.message.lower()
        
        # 验证详细信息包含检查结果
        assert "logical_check" in result.details
        assert result.details["logical_check"] == "passed"
    
    def test_conflict_result_to_dict_completeness(self, db_session, test_used_ip):
        """
        测试：ConflictResult.to_dict() 方法的完整性
        验证需求 4.6：确保可以序列化为完整的字典格式
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address=test_used_ip.ip_address
        )
        
        result_dict = result.to_dict()
        
        # 验证字典包含所有必要字段
        assert "has_conflict" in result_dict
        assert "conflict_type" in result_dict
        assert "message" in result_dict
        assert "details" in result_dict
        
        # 验证字段值类型
        assert isinstance(result_dict["has_conflict"], bool)
        assert isinstance(result_dict["conflict_type"], (str, type(None)))
        assert isinstance(result_dict["message"], str)
        assert isinstance(result_dict["details"], dict)
        
        # 验证可以序列化为 JSON（用于 API 响应）
        import json
        json_str = json.dumps(result_dict, default=str)
        assert json_str is not None
        assert len(json_str) > 0


class TestConflictDetectionEdgeCases:
    """测试冲突检测的边界情况"""
    
    def test_logical_conflict_empty_ip_address(self, db_session):
        """
        测试：空 IP 地址的处理
        """
        result = ConflictDetectionService.check_logical_conflict(
            db=db_session,
            ip_address=""
        )
        
        # 空 IP 不应该在数据库中找到
        assert result.has_conflict is False
    
    @pytest.mark.asyncio
    async def test_integrated_check_with_both_ping_and_arp(self, db_session):
        """
        测试：同时启用 Ping 和 ARP 检测
        验证需求 4.4：支持多种物理检测方法
        """
        result = await ConflictDetectionService.check_ip_conflict(
            db=db_session,
            ip_address="192.0.2.150",
            check_ping=True,
            check_arp=True,
            ping_timeout=1,
            arp_timeout=1
        )
        
        # 应该执行所有检测
        assert isinstance(result, ConflictResult)
        assert result.message is not None
    
    @pytest.mark.asyncio
    async def test_conflict_detection_order(self, db_session, test_used_ip):
        """
        测试：冲突检测顺序（逻辑检测优先）
        验证需求 4.1, 4.3：先执行逻辑检测，再执行物理检测
        """
        # 使用一个已用的 IP（逻辑冲突）
        result = await ConflictDetectionService.check_ip_conflict(
            db=db_session,
            ip_address=test_used_ip.ip_address,
            check_ping=True,
            check_arp=True
        )
        
        # 应该在逻辑检测阶段就发现冲突，不执行物理检测
        assert result.has_conflict is True
        assert result.conflict_type == "logical"
        # 详细信息中不应该包含物理检测结果
        assert "physical_checks" not in result.details or len(result.details.get("physical_checks", [])) == 0
