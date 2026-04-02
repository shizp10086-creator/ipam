"""
Unit tests for Device Utilities
测试设备工具函数的单元测试
需求: 3.2, 3.5, 3.6
"""
import pytest
from app.utils.device_utils import (
    validate_mac_address,
    normalize_mac_address,
    search_devices,
    check_mac_address_exists,
    get_device_by_mac,
    get_device_by_id
)
from app.models.device import Device
from app.models.user import User


class TestMACAddressValidation:
    """测试 MAC 地址格式验证 - 需求 3.2"""
    
    def test_validate_mac_colon_format(self):
        """测试冒号分隔的 MAC 地址格式 (AA:BB:CC:DD:EE:FF)"""
        is_valid, error = validate_mac_address("AA:BB:CC:DD:EE:FF")
        assert is_valid is True
        assert error is None
        
        # 测试小写
        is_valid, error = validate_mac_address("aa:bb:cc:dd:ee:ff")
        assert is_valid is True
        assert error is None
        
        # 测试混合大小写
        is_valid, error = validate_mac_address("Aa:Bb:Cc:Dd:Ee:Ff")
        assert is_valid is True
        assert error is None
    
    def test_validate_mac_dash_format(self):
        """测试短横线分隔的 MAC 地址格式 (AA-BB-CC-DD-EE-FF)"""
        is_valid, error = validate_mac_address("AA-BB-CC-DD-EE-FF")
        assert is_valid is True
        assert error is None
        
        # 测试小写
        is_valid, error = validate_mac_address("aa-bb-cc-dd-ee-ff")
        assert is_valid is True
        assert error is None
    
    def test_validate_mac_no_separator_format(self):
        """测试无分隔符的 MAC 地址格式 (AABBCCDDEEFF)"""
        is_valid, error = validate_mac_address("AABBCCDDEEFF")
        assert is_valid is True
        assert error is None
        
        # 测试小写
        is_valid, error = validate_mac_address("aabbccddeeff")
        assert is_valid is True
        assert error is None
    
    def test_validate_mac_empty_string(self):
        """测试空字符串"""
        is_valid, error = validate_mac_address("")
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_validate_mac_none(self):
        """测试 None 值"""
        is_valid, error = validate_mac_address(None)
        assert is_valid is False
        assert error is not None
    
    def test_validate_mac_invalid_length(self):
        """测试长度不正确的 MAC 地址"""
        # 太短
        is_valid, error = validate_mac_address("AA:BB:CC:DD:EE")
        assert is_valid is False
        
        # 太长
        is_valid, error = validate_mac_address("AA:BB:CC:DD:EE:FF:00")
        assert is_valid is False
    
    def test_validate_mac_invalid_characters(self):
        """测试包含非法字符的 MAC 地址"""
        # 包含非十六进制字符
        is_valid, error = validate_mac_address("GG:HH:II:JJ:KK:LL")
        assert is_valid is False
        
        # 包含特殊字符
        is_valid, error = validate_mac_address("AA:BB:CC:DD:EE:F@")
        assert is_valid is False
    
    def test_validate_mac_wrong_format(self):
        """测试格式错误的 MAC 地址"""
        # 随机字符串
        is_valid, error = validate_mac_address("not a mac address")
        assert is_valid is False
        
        # 数字格式错误
        is_valid, error = validate_mac_address("192.168.1.1")
        assert is_valid is False
        
        # 只有部分字节
        is_valid, error = validate_mac_address("AA:BB:CC")
        assert is_valid is False
    
    def test_validate_mac_with_whitespace(self):
        """测试带空格的 MAC 地址"""
        # 前后空格应该被处理
        is_valid, error = validate_mac_address("  AA:BB:CC:DD:EE:FF  ")
        assert is_valid is True
        assert error is None


class TestMACAddressNormalization:
    """测试 MAC 地址标准化 - 需求 3.2"""
    
    def test_normalize_colon_format(self):
        """测试标准化冒号格式"""
        result = normalize_mac_address("AA:BB:CC:DD:EE:FF")
        assert result == "AA:BB:CC:DD:EE:FF"
        
        # 小写转大写
        result = normalize_mac_address("aa:bb:cc:dd:ee:ff")
        assert result == "AA:BB:CC:DD:EE:FF"
    
    def test_normalize_dash_format(self):
        """测试标准化短横线格式"""
        result = normalize_mac_address("AA-BB-CC-DD-EE-FF")
        assert result == "AA:BB:CC:DD:EE:FF"
        
        # 小写转大写
        result = normalize_mac_address("aa-bb-cc-dd-ee-ff")
        assert result == "AA:BB:CC:DD:EE:FF"
    
    def test_normalize_no_separator_format(self):
        """测试标准化无分隔符格式"""
        result = normalize_mac_address("AABBCCDDEEFF")
        assert result == "AA:BB:CC:DD:EE:FF"
        
        # 小写转大写
        result = normalize_mac_address("aabbccddeeff")
        assert result == "AA:BB:CC:DD:EE:FF"
    
    def test_normalize_mixed_case(self):
        """测试标准化混合大小写"""
        result = normalize_mac_address("Aa:Bb:Cc:Dd:Ee:Ff")
        assert result == "AA:BB:CC:DD:EE:FF"


class TestDeviceSearch:
    """测试设备模糊搜索功能 - 需求 3.6"""
    
    def test_search_devices_no_filters(self, db_session, test_user):
        """测试无筛选条件的设备搜索"""
        # 创建测试设备
        devices_data = [
            ("Server 1", "AA:BB:CC:DD:EE:01", "Owner 1"),
            ("Server 2", "AA:BB:CC:DD:EE:02", "Owner 2"),
            ("Server 3", "AA:BB:CC:DD:EE:03", "Owner 3"),
        ]
        
        for name, mac, owner in devices_data:
            device = Device(
                name=name,
                mac_address=mac,
                owner=owner,
                created_by=test_user.id
            )
            db_session.add(device)
        db_session.commit()
        
        # 搜索所有设备
        devices, total = search_devices(db_session)
        
        assert total >= 3
        assert len(devices) >= 3
    
    def test_search_devices_by_name_keyword(self, db_session, test_user):
        """测试按设备名称关键词搜索"""
        # 创建测试设备
        device1 = Device(
            name="Special Server",
            mac_address="AA:BB:CC:DD:EE:11",
            owner="Owner 1",
            created_by=test_user.id
        )
        device2 = Device(
            name="Normal Server",
            mac_address="AA:BB:CC:DD:EE:12",
            owner="Owner 2",
            created_by=test_user.id
        )
        db_session.add(device1)
        db_session.add(device2)
        db_session.commit()
        
        # 搜索包含 "Special" 的设备
        devices, total = search_devices(db_session, keyword="Special")
        
        assert total >= 1
        assert any("Special" in device.name for device in devices)
    
    def test_search_devices_by_mac_keyword(self, db_session, test_user):
        """测试按 MAC 地址关键词搜索"""
        # 创建测试设备
        device = Device(
            name="Test Server",
            mac_address="AA:BB:CC:DD:EE:99",
            owner="Owner 1",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        
        # 搜索包含 "99" 的 MAC 地址
        devices, total = search_devices(db_session, keyword="99")
        
        assert total >= 1
        assert any("99" in device.mac_address for device in devices)
    
    def test_search_devices_by_owner_keyword(self, db_session, test_user):
        """测试按责任人关键词搜索"""
        # 创建测试设备
        device1 = Device(
            name="Server 1",
            mac_address="AA:BB:CC:DD:EE:21",
            owner="John Doe",
            created_by=test_user.id
        )
        device2 = Device(
            name="Server 2",
            mac_address="AA:BB:CC:DD:EE:22",
            owner="Jane Smith",
            created_by=test_user.id
        )
        db_session.add(device1)
        db_session.add(device2)
        db_session.commit()
        
        # 搜索包含 "John" 的责任人
        devices, total = search_devices(db_session, keyword="John")
        
        assert total >= 1
        assert any("John" in device.owner for device in devices)
    
    def test_search_devices_by_device_type(self, db_session, test_user):
        """测试按设备类型筛选"""
        # 创建不同类型的设备
        device1 = Device(
            name="Server 1",
            mac_address="AA:BB:CC:DD:EE:31",
            owner="Owner 1",
            device_type="Server",
            created_by=test_user.id
        )
        device2 = Device(
            name="Switch 1",
            mac_address="AA:BB:CC:DD:EE:32",
            owner="Owner 2",
            device_type="Switch",
            created_by=test_user.id
        )
        db_session.add(device1)
        db_session.add(device2)
        db_session.commit()
        
        # 筛选服务器类型
        devices, total = search_devices(db_session, device_type="Server")
        
        assert total >= 1
        assert all(device.device_type == "Server" for device in devices)
    
    def test_search_devices_by_owner_filter(self, db_session, test_user):
        """测试按责任人筛选"""
        # 创建测试设备
        device1 = Device(
            name="Server 1",
            mac_address="AA:BB:CC:DD:EE:41",
            owner="Alice",
            created_by=test_user.id
        )
        device2 = Device(
            name="Server 2",
            mac_address="AA:BB:CC:DD:EE:42",
            owner="Bob",
            created_by=test_user.id
        )
        db_session.add(device1)
        db_session.add(device2)
        db_session.commit()
        
        # 筛选 Alice 的设备
        devices, total = search_devices(db_session, owner="Alice")
        
        assert total >= 1
        assert all("Alice" in device.owner for device in devices)
    
    def test_search_devices_by_department(self, db_session, test_user):
        """测试按部门筛选"""
        # 创建测试设备
        device1 = Device(
            name="Server 1",
            mac_address="AA:BB:CC:DD:EE:51",
            owner="Owner 1",
            department="IT",
            created_by=test_user.id
        )
        device2 = Device(
            name="Server 2",
            mac_address="AA:BB:CC:DD:EE:52",
            owner="Owner 2",
            department="HR",
            created_by=test_user.id
        )
        db_session.add(device1)
        db_session.add(device2)
        db_session.commit()
        
        # 筛选 IT 部门的设备
        devices, total = search_devices(db_session, department="IT")
        
        assert total >= 1
        assert all("IT" in device.department for device in devices if device.department)
    
    def test_search_devices_with_pagination(self, db_session, test_user):
        """测试分页功能"""
        # 创建多个测试设备
        for i in range(25):
            device = Device(
                name=f"Server {i}",
                mac_address=f"AA:BB:CC:DD:EE:{i:02X}",
                owner="Owner",
                created_by=test_user.id
            )
            db_session.add(device)
        db_session.commit()
        
        # 第一页，每页 10 条
        devices_page1, total = search_devices(db_session, page=1, page_size=10)
        assert len(devices_page1) == 10
        assert total >= 25
        
        # 第二页，每页 10 条
        devices_page2, total = search_devices(db_session, page=2, page_size=10)
        assert len(devices_page2) == 10
        
        # 确保两页的设备不重复
        page1_ids = {device.id for device in devices_page1}
        page2_ids = {device.id for device in devices_page2}
        assert len(page1_ids.intersection(page2_ids)) == 0
    
    def test_search_devices_combined_filters(self, db_session, test_user):
        """测试组合筛选条件"""
        # 创建测试设备
        device1 = Device(
            name="Production Server",
            mac_address="AA:BB:CC:DD:EE:61",
            owner="John Doe",
            device_type="Server",
            department="IT",
            created_by=test_user.id
        )
        device2 = Device(
            name="Test Server",
            mac_address="AA:BB:CC:DD:EE:62",
            owner="Jane Smith",
            device_type="Server",
            department="IT",
            created_by=test_user.id
        )
        device3 = Device(
            name="Production Switch",
            mac_address="AA:BB:CC:DD:EE:63",
            owner="John Doe",
            device_type="Switch",
            department="IT",
            created_by=test_user.id
        )
        db_session.add_all([device1, device2, device3])
        db_session.commit()
        
        # 组合筛选：关键词 + 设备类型 + 部门
        devices, total = search_devices(
            db_session,
            keyword="Production",
            device_type="Server",
            department="IT"
        )
        
        assert total >= 1
        assert all("Production" in device.name for device in devices)
        assert all(device.device_type == "Server" for device in devices)


class TestDeviceQueries:
    """测试设备查询函数"""
    
    def test_check_mac_address_exists(self, db_session, test_user):
        """测试检查 MAC 地址是否存在"""
        # 创建测试设备
        device = Device(
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:71",
            owner="Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        
        # 检查存在的 MAC 地址
        exists = check_mac_address_exists(db_session, "AA:BB:CC:DD:EE:71")
        assert exists is True
        
        # 检查不存在的 MAC 地址
        exists = check_mac_address_exists(db_session, "AA:BB:CC:DD:EE:72")
        assert exists is False
    
    def test_check_mac_address_exists_with_exclusion(self, db_session, test_user):
        """测试检查 MAC 地址是否存在（排除指定设备）"""
        # 创建测试设备
        device = Device(
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:81",
            owner="Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        
        # 检查时排除当前设备（用于更新场景）
        exists = check_mac_address_exists(
            db_session,
            "AA:BB:CC:DD:EE:81",
            exclude_device_id=device.id
        )
        assert exists is False
    
    def test_get_device_by_mac(self, db_session, test_user):
        """测试根据 MAC 地址查询设备"""
        # 创建测试设备
        device = Device(
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:91",
            owner="Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        
        # 查询存在的设备
        found_device = get_device_by_mac(db_session, "AA:BB:CC:DD:EE:91")
        assert found_device is not None
        assert found_device.name == "Test Device"
        
        # 查询不存在的设备
        not_found = get_device_by_mac(db_session, "AA:BB:CC:DD:EE:92")
        assert not_found is None
    
    def test_get_device_by_id(self, db_session, test_user):
        """测试根据 ID 查询设备"""
        # 创建测试设备
        device = Device(
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:A1",
            owner="Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        
        # 查询存在的设备
        found_device = get_device_by_id(db_session, device.id)
        assert found_device is not None
        assert found_device.name == "Test Device"
        
        # 查询不存在的设备
        not_found = get_device_by_id(db_session, 99999)
        assert not_found is None


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
