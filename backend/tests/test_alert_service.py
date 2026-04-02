"""
Alert Service Tests
测试告警服务的核心功能
"""
import pytest
from sqlalchemy.orm import Session
from app.services.alert_service import AlertService
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress
from app.models.alert import Alert
from app.models.user import User
from app.core.security import get_password_hash


class TestAlertService:
    """告警服务测试类"""
    
    @pytest.fixture
    def alert_user(self, db_session: Session):
        """创建测试用户"""
        user = User(
            username="test_alert_user",
            hashed_password=get_password_hash("password123"),
            email="alert@test.com",
            full_name="Alert Test User",
            role="admin",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def alert_segment(self, db_session: Session, alert_user: User):
        """创建测试网段"""
        segment = NetworkSegment(
            name="Alert Test Segment",
            network="192.168.100.0",
            prefix_length=24,
            gateway="192.168.100.1",
            description="Test segment for alerts",
            usage_threshold=80,
            created_by=alert_user.id
        )
        db_session.add(segment)
        db_session.commit()
        db_session.refresh(segment)
        return segment
    
    def test_calculate_segment_usage_empty(self, db_session: Session, alert_segment: NetworkSegment):
        """测试计算空网段的使用率"""
        usage_stats = AlertService.calculate_segment_usage(db_session, alert_segment.id)
        
        assert usage_stats is not None
        assert usage_stats['segment_id'] == alert_segment.id
        assert usage_stats['total_ips'] == 254
        assert usage_stats['used_ips'] == 0
        assert usage_stats['available_ips'] == 254
        assert usage_stats['reserved_ips'] == 0
        assert usage_stats['usage_rate'] == 0.0
        assert usage_stats['threshold'] == 80
    
    def test_calculate_segment_usage_with_ips(self, db_session: Session, alert_segment: NetworkSegment):
        """测试计算有 IP 的网段使用率"""
        for i in range(1, 11):
            ip = IPAddress(
                ip_address=f"192.168.100.{i}",
                segment_id=alert_segment.id,
                status="used"
            )
            db_session.add(ip)
        
        for i in range(11, 16):
            ip = IPAddress(
                ip_address=f"192.168.100.{i}",
                segment_id=alert_segment.id,
                status="reserved"
            )
            db_session.add(ip)
        
        db_session.commit()
        
        usage_stats = AlertService.calculate_segment_usage(db_session, alert_segment.id)
        
        assert usage_stats['used_ips'] == 10
        assert usage_stats['reserved_ips'] == 5
        assert usage_stats['available_ips'] == 239
        assert abs(usage_stats['usage_rate'] - 5.91) < 0.01
    
    def test_check_and_create_alert_below_threshold(self, db_session: Session, alert_segment: NetworkSegment):
        """测试使用率低于阈值时不创建告警"""
        for i in range(1, 11):
            ip = IPAddress(
                ip_address=f"192.168.100.{i}",
                segment_id=alert_segment.id,
                status="used"
            )
            db_session.add(ip)
        db_session.commit()
        
        created, message, alert = AlertService.check_and_create_alert(db_session, alert_segment.id)
        
        assert created is False
        assert "below threshold" in message.lower()
        assert alert is None
    
    def test_check_and_create_alert_above_threshold(self, db_session: Session, alert_segment: NetworkSegment):
        """测试使用率达到阈值时创建告警"""
        for i in range(1, 205):
            ip = IPAddress(
                ip_address=f"192.168.100.{i}",
                segment_id=alert_segment.id,
                status="used"
            )
            db_session.add(ip)
        db_session.commit()
        
        created, message, alert = AlertService.check_and_create_alert(db_session, alert_segment.id)
        
        assert created is True
        assert "created successfully" in message.lower()
        assert alert is not None
        assert alert.segment_id == alert_segment.id
        assert alert.alert_type == "usage_threshold"
        assert alert.is_resolved is False
        assert alert.current_usage >= 80
    
    def test_resolve_alert_manually(self, db_session: Session, alert_segment: NetworkSegment):
        """测试手动解决告警"""
        for i in range(1, 205):
            ip = IPAddress(
                ip_address=f"192.168.100.{i}",
                segment_id=alert_segment.id,
                status="used"
            )
            db_session.add(ip)
        db_session.commit()
        
        created, _, alert = AlertService.check_and_create_alert(db_session, alert_segment.id)
        assert created is True
        
        success, message, resolved_alert = AlertService.resolve_alert_manually(db_session, alert.id)
        
        assert success is True
        assert "resolved successfully" in message.lower()
        assert resolved_alert.is_resolved is True
        assert resolved_alert.resolved_at is not None
