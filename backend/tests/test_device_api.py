"""
Integration tests for Device API endpoints
测试设备管理 API 接口
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.device import Device
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress


client = TestClient(app)


class TestDeviceAPI:
    """测试设备管理 API"""
    
    def test_create_device_success(self, db_session, test_user):
        """测试创建设备成功"""
        response = client.post(
            "/api/v1/devices/",
            json={
                "name": "Test Server",
                "mac_address": "AA:BB:CC:DD:EE:01",
                "owner": "John Doe",
                "device_type": "Server",
                "manufacturer": "Dell",
                "model": "PowerEdge R740",
                "department": "IT",
                "location": "Data Center A",
                "description": "Production server"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 201
        assert data["data"]["name"] == "Test Server"
        assert data["data"]["mac_address"] == "AA:BB:CC:DD:EE:01"
    
    def test_create_device_invalid_mac(self, db_session, test_user):
        """测试使用无效 MAC 地址创建设备"""
        response = client.post(
            "/api/v1/devices/",
            json={
                "name": "Test Server",
                "mac_address": "invalid-mac",
                "owner": "John Doe"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_devices_list(self, db_session, test_user):
        """测试获取设备列表"""
        # 创建几个测试设备
        for i in range(3):
            device = Device(
                name=f"Device {i}",
                mac_address=f"AA:BB:CC:DD:EE:0{i+2}",
                owner="Test Owner",
                created_by=test_user.id
            )
            db_session.add(device)
        db_session.commit()
        
        response = client.get("/api/v1/devices/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) >= 3
    
    def test_get_devices_with_search(self, db_session, test_user):
        """测试设备搜索功能"""
        # 创建测试设备
        device = Device(
            name="Special Server",
            mac_address="AA:BB:CC:DD:EE:05",
            owner="Special Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        
        # 搜索设备名称
        response = client.get("/api/v1/devices/?keyword=Special")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) >= 1
        assert any("Special" in item["name"] for item in data["data"]["items"])
    
    def test_get_device_by_id(self, db_session, test_user):
        """测试获取设备详情"""
        # 创建测试设备
        device = Device(
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:06",
            owner="Test Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        
        response = client.get(f"/api/v1/devices/{device.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == device.id
        assert data["data"]["name"] == "Test Device"
    
    def test_update_device(self, db_session, test_user):
        """测试更新设备"""
        # 创建测试设备
        device = Device(
            name="Original Name",
            mac_address="AA:BB:CC:DD:EE:07",
            owner="Original Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        
        # 更新设备
        response = client.put(
            f"/api/v1/devices/{device.id}",
            json={
                "name": "Updated Name",
                "owner": "Updated Owner"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["owner"] == "Updated Owner"
    
    def test_delete_device(self, db_session, test_user):
        """测试删除设备"""
        # 创建测试设备
        device = Device(
            name="To Be Deleted",
            mac_address="AA:BB:CC:DD:EE:08",
            owner="Test Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        
        # 删除设备
        response = client.delete(f"/api/v1/devices/{device.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        
        # 验证设备已被删除
        response = client.get(f"/api/v1/devices/{device.id}")
        assert response.status_code == 404
    
    def test_get_device_ips(self, db_session, test_user, test_segment):
        """测试获取设备关联的 IP 地址"""
        # 创建测试设备
        device = Device(
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:09",
            owner="Test Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        
        # 创建关联的 IP 地址
        ip1 = IPAddress(
            segment_id=test_segment.id,
            ip_address="192.168.1.20",
            status="used",
            device_id=device.id,
            allocated_by=test_user.id
        )
        ip2 = IPAddress(
            segment_id=test_segment.id,
            ip_address="192.168.1.21",
            status="used",
            device_id=device.id,
            allocated_by=test_user.id
        )
        db_session.add(ip1)
        db_session.add(ip2)
        db_session.commit()
        
        # 获取设备的 IP 地址
        response = client.get(f"/api/v1/devices/{device.id}/ips")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["ip_count"] == 2
        assert len(data["data"]["ips"]) == 2


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
