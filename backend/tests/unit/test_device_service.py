"""
Unit tests for Device Service
测试设备服务的单元测试
需求: 3.2, 3.5, 3.6
"""
import pytest
from app.services.device_service import DeviceService
from app.models.device import Device
from app.models.user import User
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress


class TestDeviceCreation:
    """测试设备创建功能 - 需求 3.2"""
    
    def test_create_device_success(self, db_session, test_user):
        """测试成功创建设备"""
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Test Server",
            mac_address="AA:BB:CC:DD:EE:FF",
            owner="John Doe",
            device_type="Server",
            manufacturer="Dell",
            model="PowerEdge R740",
            department="IT",
            location="Data Center A",
            description="Production server",
            created_by=test_user.id
        )
        
        assert success is True
        assert "successfully" in message
        assert device is not None
        assert device.name == "Test Server"
        assert device.mac_address == "AA:BB:CC:DD:EE:FF"
        assert device.owner == "John Doe"
        assert device.device_type == "Server"
        assert device.manufacturer == "Dell"
        assert device.model == "PowerEdge R740"
        assert device.department == "IT"
        assert device.location == "Data Center A"
        assert device.description == "Production server"
        assert device.created_by == test_user.id
    
    def test_create_device_minimal_fields(self, db_session, test_user):
        """测试只使用必填字段创建设备"""
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Minimal Device",
            mac_address="AA:BB:CC:DD:EE:01",
            owner="Owner",
            created_by=test_user.id
        )
        
        assert success is True
        assert device is not None
        assert device.name == "Minimal Device"
        assert device.mac_address == "AA:BB:CC:DD:EE:01"
        assert device.owner == "Owner"
        assert device.device_type is None
        assert device.manufacturer is None
    
    def test_create_device_invalid_mac_format(self, db_session, test_user):
        """测试使用无效 MAC 地址格式创建设备"""
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="invalid-mac-address",
            owner="Owner",
            created_by=test_user.id
        )
        
        assert success is False
        assert "Invalid MAC address" in message
        assert device is None
    
    def test_create_device_empty_mac(self, db_session, test_user):
        """测试使用空 MAC 地址创建设备"""
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="",
            owner="Owner",
            created_by=test_user.id
        )
        
        assert success is False
        assert "cannot be empty" in message
        assert device is None
    
    def test_create_device_duplicate_mac(self, db_session, test_user):
        """测试使用重复 MAC 地址创建设备"""
        # 创建第一个设备
        DeviceService.create_device(
            db=db_session,
            name="Device 1",
            mac_address="AA:BB:CC:DD:EE:11",
            owner="Owner 1",
            created_by=test_user.id
        )
        
        # 尝试使用相同 MAC 地址创建第二个设备
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Device 2",
            mac_address="AA:BB:CC:DD:EE:11",
            owner="Owner 2",
            created_by=test_user.id
        )
        
        assert success is False
        assert "already exists" in message
        assert device is None
    
    def test_create_device_mac_normalization(self, db_session, test_user):
        """测试 MAC 地址自动标准化"""
        # 使用短横线格式
        success, message, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="aa-bb-cc-dd-ee-22",
            owner="Owner",
            created_by=test_user.id
        )
        
        assert success is True
        assert device.mac_address == "AA:BB:CC:DD:EE:22"  # 标准化为冒号格式


class TestDeviceUpdate:
    """测试设备更新功能"""
    
    def test_update_device_name(self, db_session, test_user):
        """测试更新设备名称"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Original Name",
            mac_address="AA:BB:CC:DD:EE:31",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 更新名称
        success, message, updated_device = DeviceService.update_device(
            db=db_session,
            device_id=device.id,
            name="Updated Name"
        )
        
        assert success is True
        assert updated_device.name == "Updated Name"
        assert updated_device.mac_address == "AA:BB:CC:DD:EE:31"  # MAC 未改变
    
    def test_update_device_multiple_fields(self, db_session, test_user):
        """测试同时更新多个字段"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Original Name",
            mac_address="AA:BB:CC:DD:EE:32",
            owner="Original Owner",
            device_type="Server",
            created_by=test_user.id
        )
        
        # 更新多个字段
        success, message, updated_device = DeviceService.update_device(
            db=db_session,
            device_id=device.id,
            name="Updated Name",
            owner="Updated Owner",
            device_type="Switch",
            manufacturer="Cisco",
            model="Catalyst 9300"
        )
        
        assert success is True
        assert updated_device.name == "Updated Name"
        assert updated_device.owner == "Updated Owner"
        assert updated_device.device_type == "Switch"
        assert updated_device.manufacturer == "Cisco"
        assert updated_device.model == "Catalyst 9300"
    
    def test_update_device_mac_address(self, db_session, test_user):
        """测试更新 MAC 地址"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:33",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 更新 MAC 地址
        success, message, updated_device = DeviceService.update_device(
            db=db_session,
            device_id=device.id,
            mac_address="AA:BB:CC:DD:EE:34"
        )
        
        assert success is True
        assert updated_device.mac_address == "AA:BB:CC:DD:EE:34"
    
    def test_update_device_invalid_mac(self, db_session, test_user):
        """测试更新为无效 MAC 地址"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:35",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 尝试更新为无效 MAC
        success, message, updated_device = DeviceService.update_device(
            db=db_session,
            device_id=device.id,
            mac_address="invalid-mac"
        )
        
        assert success is False
        assert "Invalid MAC address" in message
    
    def test_update_device_duplicate_mac(self, db_session, test_user):
        """测试更新为已存在的 MAC 地址"""
        # 创建两个设备
        _, _, device1 = DeviceService.create_device(
            db=db_session,
            name="Device 1",
            mac_address="AA:BB:CC:DD:EE:36",
            owner="Owner 1",
            created_by=test_user.id
        )
        _, _, device2 = DeviceService.create_device(
            db=db_session,
            name="Device 2",
            mac_address="AA:BB:CC:DD:EE:37",
            owner="Owner 2",
            created_by=test_user.id
        )
        
        # 尝试将 device2 的 MAC 更新为 device1 的 MAC
        success, message, updated_device = DeviceService.update_device(
            db=db_session,
            device_id=device2.id,
            mac_address="AA:BB:CC:DD:EE:36"
        )
        
        assert success is False
        assert "already exists" in message
    
    def test_update_device_not_found(self, db_session):
        """测试更新不存在的设备"""
        success, message, device = DeviceService.update_device(
            db=db_session,
            device_id=99999,
            name="Updated Name"
        )
        
        assert success is False
        assert "not found" in message.lower()
        assert device is None


class TestDeviceDeletion:
    """测试设备删除功能 - 需求 3.5"""
    
    def test_delete_device_success(self, db_session, test_user):
        """测试成功删除设备"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="To Be Deleted",
            mac_address="AA:BB:CC:DD:EE:41",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 删除设备
        success, message = DeviceService.delete_device(db_session, device.id)
        
        assert success is True
        assert "successfully" in message.lower()
        
        # 验证设备已被删除
        deleted_device = db_session.query(Device).filter_by(id=device.id).first()
        assert deleted_device is None
    
    def test_delete_device_with_single_ip(self, db_session, test_user, test_segment):
        """测试删除关联单个 IP 的设备"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:42",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 创建并分配 IP 给设备
        ip = IPAddress(
            segment_id=test_segment.id,
            ip_address="192.168.1.10",
            status="used",
            device_id=device.id,
            allocated_by=test_user.id
        )
        db_session.add(ip)
        db_session.commit()
        
        # 删除设备
        success, message = DeviceService.delete_device(db_session, device.id)
        
        assert success is True
        assert "1 IP(s) released" in message
        
        # 验证 IP 已被回收
        db_session.refresh(ip)
        assert ip.status == "available"
        assert ip.device_id is None
        assert ip.allocated_by is None
        assert ip.allocated_at is None
    
    def test_delete_device_with_multiple_ips(self, db_session, test_user, test_segment):
        """测试删除关联多个 IP 的设备"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:43",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 创建并分配多个 IP 给设备
        ips = []
        for i in range(5):
            ip = IPAddress(
                segment_id=test_segment.id,
                ip_address=f"192.168.1.{20+i}",
                status="used",
                device_id=device.id,
                allocated_by=test_user.id
            )
            db_session.add(ip)
            ips.append(ip)
        db_session.commit()
        
        # 删除设备
        success, message = DeviceService.delete_device(db_session, device.id)
        
        assert success is True
        assert "5 IP(s) released" in message
        
        # 验证所有 IP 都已被回收
        for ip in ips:
            db_session.refresh(ip)
            assert ip.status == "available"
            assert ip.device_id is None
    
    def test_delete_device_without_ips(self, db_session, test_user):
        """测试删除没有关联 IP 的设备"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:44",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 删除设备
        success, message = DeviceService.delete_device(db_session, device.id)
        
        assert success is True
        assert "0 IP(s) released" in message
    
    def test_delete_device_not_found(self, db_session):
        """测试删除不存在的设备"""
        success, message = DeviceService.delete_device(db_session, 99999)
        
        assert success is False
        assert "not found" in message.lower()


class TestDeviceIPAssociation:
    """测试设备与 IP 关联功能"""
    
    def test_get_device_ips_success(self, db_session, test_user, test_segment):
        """测试获取设备关联的 IP 地址"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:51",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 创建关联的 IP 地址
        ip1 = IPAddress(
            segment_id=test_segment.id,
            ip_address="192.168.1.30",
            status="used",
            device_id=device.id,
            allocated_by=test_user.id
        )
        ip2 = IPAddress(
            segment_id=test_segment.id,
            ip_address="192.168.1.31",
            status="used",
            device_id=device.id,
            allocated_by=test_user.id
        )
        db_session.add(ip1)
        db_session.add(ip2)
        db_session.commit()
        
        # 获取设备的 IP 地址
        success, message, ips = DeviceService.get_device_ips(db_session, device.id)
        
        assert success is True
        assert len(ips) == 2
        assert all(ip.device_id == device.id for ip in ips)
    
    def test_get_device_ips_no_ips(self, db_session, test_user):
        """测试获取没有关联 IP 的设备"""
        # 创建设备
        _, _, device = DeviceService.create_device(
            db=db_session,
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:52",
            owner="Owner",
            created_by=test_user.id
        )
        
        # 获取设备的 IP 地址
        success, message, ips = DeviceService.get_device_ips(db_session, device.id)
        
        assert success is True
        assert len(ips) == 0
    
    def test_get_device_ips_not_found(self, db_session):
        """测试获取不存在设备的 IP 地址"""
        success, message, ips = DeviceService.get_device_ips(db_session, 99999)
        
        assert success is False
        assert "not found" in message.lower()
        assert ips is None


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
