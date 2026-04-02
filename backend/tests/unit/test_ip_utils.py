"""
Unit tests for IP address utility functions
"""
import pytest
from app.utils.ip_utils import (
    validate_ip_address,
    validate_ip_status,
    calculate_network_range
)


class TestIPAddressValidation:
    """测试 IP 地址格式验证"""
    
    def test_valid_ipv4_address(self):
        """测试有效的 IPv4 地址"""
        is_valid, error = validate_ip_address("192.168.1.1")
        assert is_valid is True
        assert error is None
    
    def test_invalid_ip_address_format(self):
        """测试无效的 IP 地址格式"""
        is_valid, error = validate_ip_address("999.999.999.999")
        assert is_valid is False
        assert error is not None
        assert "Invalid IP address format" in error
    
    def test_invalid_ip_address_string(self):
        """测试无效的 IP 地址字符串"""
        is_valid, error = validate_ip_address("not-an-ip")
        assert is_valid is False
        assert error is not None


class TestIPStatusValidation:
    """测试 IP 状态验证"""
    
    def test_valid_status_available(self):
        """测试有效状态：available"""
        is_valid, error = validate_ip_status("available")
        assert is_valid is True
        assert error is None
    
    def test_valid_status_used(self):
        """测试有效状态：used"""
        is_valid, error = validate_ip_status("used")
        assert is_valid is True
        assert error is None
    
    def test_valid_status_reserved(self):
        """测试有效状态：reserved"""
        is_valid, error = validate_ip_status("reserved")
        assert is_valid is True
        assert error is None
    
    def test_invalid_status(self):
        """测试无效状态"""
        is_valid, error = validate_ip_status("invalid_status")
        assert is_valid is False
        assert error is not None
        assert "Invalid status" in error


class TestNetworkRangeCalculation:
    """测试网段范围计算"""
    
    def test_calculate_class_c_network(self):
        """测试 /24 网段计算"""
        first_ip, last_ip, total_ips = calculate_network_range("192.168.1.0", 24)
        assert first_ip == "192.168.1.1"
        assert last_ip == "192.168.1.254"
        assert total_ips == 254
    
    def test_calculate_class_b_network(self):
        """测试 /16 网段计算"""
        first_ip, last_ip, total_ips = calculate_network_range("172.16.0.0", 16)
        assert first_ip == "172.16.0.1"
        assert last_ip == "172.16.255.254"
        assert total_ips == 65534
    
    def test_calculate_small_network(self):
        """测试 /30 网段计算（小网段）"""
        first_ip, last_ip, total_ips = calculate_network_range("10.0.0.0", 30)
        assert first_ip == "10.0.0.1"
        assert last_ip == "10.0.0.2"
        assert total_ips == 2
