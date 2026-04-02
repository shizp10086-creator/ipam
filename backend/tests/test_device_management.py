"""
Tests for Device Management Module
测试设备资产管理模块的功能
"""
import pytest
from app.utils.device_utils import validate_mac_address, normalize_mac_address
from app.services.device_service import DeviceService
from app.models.device import Device
from app.models.user import User
from app.models.ip_address import IPAddress


class TestDeviceUtils:
    """测试设备工具函数"""
    
    def test_validate_mac_address_valid_formats(self):
        """测试有效的 MAC 地址格式"""
        # 测试 AA:BB:CC:DD:EE:FF 格式
        is_valid, error = validate_mac_address("AA:BB:CC:DD:EE:FF")
        assert is_valid is True
        assert error is None
        
        # 测试 AA-BB-CC-DD-EE-FF 格式
        is_valid, error = validate_mac_address("AA-BB-CC-DD-EE-FF")
        assert is_valid is True
        assert error is None
        
        # 测试 AABBCCDDEEFF 格式
        is_valid, error = validate_mac_address("AABBCCDDEEFF")
        assert is_valid is True
        assert error is None
        
        # 测试小写
        is_valid, error = validate_mac_address("aa:bb:cc:dd:ee:ff")
        assert is_valid is True
        assert error is None
    
    def test_validate_mac_address_invalid_formats(self):
        """测试无效的 MAC 地址格式"""
        # 测试空字符串
        is_valid, error = validate_mac_address("")
        assert is_valid is False
        assert "cannot be empty" in error
        
        # 测试格式错误
        is_valid, error = validate_mac_address("AA:BB:CC:DD:EE")
        assert is_valid is False
        
        # 测试包含非法字符
        is_valid, error = validate_mac_address("GG:HH:II:JJ:KK:LL")
        assert is_valid is False
        
        # 测试随机字符串
        is_valid, error = validate_mac_address("not a mac address")
        assert is_valid is False
    
    def test_normalize_mac_address(self):
        """测试 MAC 地址标准化"""
        # 测试不同格式都能标准化为 AA:BB:CC:DD:EE:FF
        assert normalize_mac_address("AA:BB:CC:DD:EE:FF") == "AA:BB:CC:DD:EE:FF"
        assert normalize_mac_address("AA-BB-CC-DD-EE-FF") == "AA:BB:CC:DD:EE:FF"
        assert normalize_mac_address("AABBCCDDEEFF") == "AA:BB:CC:DD:EE:FF"
        assert normalize_mac_address("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"


class TestDeviceService:
    """测试设备服务"""
    
    def test_create_device_success(self, db_session, test_user):
        """测试成功创建设备"""
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Test Server",
            mac_address="AA:BB:CC:DD:EE:FF",
            owner="John Doe",
            device_type="Server",
            created_by=test_user.id
        )
        
        assert success is True
        assert "successfully" in message
        assert device is not None
        assert device.name == "Test Server"
        assert device.mac_address == "AA:BB:CC:DD:EE:FF"
        assert device.owner == "John Doe"
    
    def test_create_device_invalid_mac(self, db_session, test_user):
        """测试使用无效 MAC 地址创建设备"""
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Test Server",
            mac_address="invalid-mac",
            owner="John Doe",
            created_by=test_user.id
        )
        
        assert success is False
        assert "Invalid MAC address" in message
        assert device is None
    
    def test_create_device_duplicate_mac(self, db_session, test_user):
        """测试使用重复 MAC 地址创建设备"""
        # 创建第一个设备
        DeviceService.create_device(
            db=db_session,
            name="Device 1",
            mac_address="AA:BB:CC:DD:EE:11",
            owner="John Doe",
            created_by=test_user.id
        )
        
        # 尝试使用相同 MAC 地址创建第二个设备
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Device 2",
            mac_address="AA:BB:CC:DD:EE:11",
            owner="Jane Doe",
            created_by=test_user.id
        )
        
        assert success is False
        assert "already exists" in message
        assert device is None
    
    def test_update_device_success(self, db_session, test_user):
        """测试成功更新设备"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Original Name",
            mac_address="AA:BB:CC:DD:EE:22",
            owner="John Doe",
            created_by=test_user.id
        )
        
        # 更新设备
        success, message, updated_device = DeviceService.update_device(
            db=db_session,
            device_id=device.id,
            name="Updated Name",
            owner="Jane Doe"
        )
        
        assert success is True
        assert updated_device.name == "Updated Name"
        assert updated_device.owner == "Jane Doe"
        assert updated_device.mac_address == "AA:BB:CC:DD:EE:22"  # MAC 未改变
    
    def test_delete_device_with_ips(self, db_session, test_user, test_segment):
        """测试删除设备时自动回收关联的 IP"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:33",
            owner="John Doe",
            created_by=test_user.id
        )
        
        # 创建并分配 IP 给设备
        ip1 = IPAddress(
            segment_id=test_segment.id,
            ip_address="192.168.1.10",
            status="used",
            device_id=device.id,
            allocated_by=test_user.id
        )
        ip2 = IPAddress(
            segment_id=test_segment.id,
            ip_address="192.168.1.11",
            status="used",
            device_id=device.id,
            allocated_by=test_user.id
        )
        db_session.add(ip1)
        db_session.add(ip2)
        db_session.commit()
        
        # 删除设备
        success, message = DeviceService.delete_device(db_session, device.id)
        
        assert success is True
        assert "2 IP(s) released" in message
        
        # 验证 IP 已被回收
        db_session.refresh(ip1)
        db_session.refresh(ip2)
        assert ip1.status == "available"
        assert ip1.device_id is None
        assert ip2.status == "available"
        assert ip2.device_id is None


# Fixtures
@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        hashed_password="hashed_password",
        email="test@example.com",
        full_name="Test User",
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_segment(db_session, test_user):
    """创建测试网段"""
    from app.models.network_segment import NetworkSegment
    segment = NetworkSegment(
        name="Test Segment",
        network="192.168.1.0",
        prefix_length=24,
        gateway="192.168.1.1",
        description="Test segment",
        usage_threshold=80,
        created_by=test_user.id
    )
    db_session.add(segment)
    db_session.commit()
    db_session.refresh(segment)
    return segment
