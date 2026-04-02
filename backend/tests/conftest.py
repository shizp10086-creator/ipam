"""
Pytest configuration and fixtures for IPAM system tests
"""
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Configure Hypothesis
from hypothesis import settings, Verbosity

# Register Hypothesis profiles
settings.register_profile("default", max_examples=100)
settings.register_profile("ci", max_examples=1000)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)
settings.register_profile("quick", max_examples=20)

# Load the appropriate profile
profile = os.getenv('HYPOTHESIS_PROFILE', 'default')
settings.load_profile(profile)

# Database fixtures
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.network_segment import NetworkSegment
from app.models.device import Device
from app.models.ip_address import IPAddress


@pytest.fixture(scope="function")
def db_session():
    """
    创建测试数据库会话
    每个测试函数使用独立的数据库会话，测试结束后回滚
    """
    # 使用内存数据库
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    from app.core.security import get_password_hash
    
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session):
    """创建测试管理员用户"""
    from app.core.security import get_password_hash
    
    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_segment(db_session, test_admin):
    """创建测试网段"""
    segment = NetworkSegment(
        name="Test Segment",
        network="192.168.1.0",
        prefix_length=24,
        gateway="192.168.1.1",
        description="Test network segment",
        usage_threshold=80,
        created_by=test_admin.id
    )
    db_session.add(segment)
    db_session.commit()
    db_session.refresh(segment)
    return segment


@pytest.fixture
def test_device(db_session, test_admin):
    """创建测试设备"""
    device = Device(
        name="Test Device",
        mac_address="AA:BB:CC:DD:EE:FF",
        device_type="Server",
        manufacturer="Dell",
        model="PowerEdge R740",
        owner="Test Owner",
        department="IT",
        location="Data Center",
        description="Test device",
        created_by=test_admin.id
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def test_available_ip(db_session, test_segment):
    """创建测试可用 IP"""
    ip = IPAddress(
        ip_address="192.168.1.10",
        segment_id=test_segment.id,
        status="available"
    )
    db_session.add(ip)
    db_session.commit()
    db_session.refresh(ip)
    return ip


@pytest.fixture
def test_used_ip(db_session, test_segment, test_device, test_admin):
    """创建测试已用 IP"""
    ip = IPAddress(
        ip_address="192.168.1.20",
        segment_id=test_segment.id,
        status="used",
        device_id=test_device.id,
        allocated_by=test_admin.id
    )
    db_session.add(ip)
    db_session.commit()
    db_session.refresh(ip)
    return ip


@pytest.fixture
def test_reserved_ip(db_session, test_segment):
    """创建测试保留 IP"""
    ip = IPAddress(
        ip_address="192.168.1.30",
        segment_id=test_segment.id,
        status="reserved"
    )
    db_session.add(ip)
    db_session.commit()
    db_session.refresh(ip)
    return ip
