"""
Unit tests for IP address Pydantic schemas
"""
import pytest
from pydantic import ValidationError
from app.schemas.ip_address import (
    IPAddressCreate,
    IPAddressUpdate,
    IPAllocateRequest,
    IPReleaseRequest,
    IPReserveRequest
)


class TestIPAddressCreate:
    """测试 IP 地址创建模式"""
    
    def test_valid_ip_address_create(self):
        """测试有效的 IP 地址创建请求"""
        data = {
            "ip_address": "192.168.1.10",
            "segment_id": 1,
            "status": "available"
        }
        schema = IPAddressCreate(**data)
        assert schema.ip_address == "192.168.1.10"
        assert schema.segment_id == 1
        assert schema.status == "available"
    
    def test_invalid_ip_format(self):
        """测试无效的 IP 格式"""
        data = {
            "ip_address": "999.999.999.999",
            "segment_id": 1
        }
        with pytest.raises(ValidationError) as exc_info:
            IPAddressCreate(**data)
        assert "Invalid IP address format" in str(exc_info.value)
    
    def test_invalid_status(self):
        """测试无效的状态值"""
        data = {
            "ip_address": "192.168.1.10",
            "segment_id": 1,
            "status": "invalid_status"
        }
        with pytest.raises(ValidationError) as exc_info:
            IPAddressCreate(**data)
        assert "Status must be one of" in str(exc_info.value)


class TestIPAllocateRequest:
    """测试 IP 分配请求模式"""
    
    def test_valid_allocate_request(self):
        """测试有效的分配请求"""
        data = {
            "ip_address": "192.168.1.10",
            "device_id": 1
        }
        schema = IPAllocateRequest(**data)
        assert schema.ip_address == "192.168.1.10"
        assert schema.device_id == 1
    
    def test_allocate_with_segment_id(self):
        """测试带网段 ID 的分配请求"""
        data = {
            "ip_address": "192.168.1.10",
            "device_id": 1,
            "segment_id": 1
        }
        schema = IPAllocateRequest(**data)
        assert schema.segment_id == 1


class TestIPReleaseRequest:
    """测试 IP 回收请求模式"""
    
    def test_release_by_ip_address(self):
        """测试通过 IP 地址回收"""
        data = {"ip_address": "192.168.1.10"}
        schema = IPReleaseRequest(**data)
        assert schema.ip_address == "192.168.1.10"
    
    def test_release_by_ip_id(self):
        """测试通过 IP ID 回收"""
        data = {"ip_id": 1}
        schema = IPReleaseRequest(**data)
        assert schema.ip_id == 1
    
    def test_release_without_identifier(self):
        """测试没有提供标识符的情况"""
        with pytest.raises(ValueError) as exc_info:
            IPReleaseRequest()
        assert "Either ip_address or ip_id must be provided" in str(exc_info.value)


class TestIPReserveRequest:
    """测试 IP 保留请求模式"""
    
    def test_reserve_ip(self):
        """测试保留 IP"""
        data = {
            "ip_address": "192.168.1.10",
            "reserve": True
        }
        schema = IPReserveRequest(**data)
        assert schema.ip_address == "192.168.1.10"
        assert schema.reserve is True
    
    def test_unreserve_ip(self):
        """测试取消保留 IP"""
        data = {
            "ip_id": 1,
            "reserve": False
        }
        schema = IPReserveRequest(**data)
        assert schema.ip_id == 1
        assert schema.reserve is False
    
    def test_reserve_without_identifier(self):
        """测试没有提供标识符的情况"""
        with pytest.raises(ValueError) as exc_info:
            IPReserveRequest(reserve=True)
        assert "Either ip_address or ip_id must be provided" in str(exc_info.value)
