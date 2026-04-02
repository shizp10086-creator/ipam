"""
Unit Tests for Statistics Service

Tests the statistical calculations for dashboard data.

Requirements: 7.1, 7.2, 7.3, 7.4
"""
import pytest
from datetime import datetime, timedelta
from app.services.statistics_service import StatisticsService
from app.models.ip_address import IPAddress
from app.models.device import Device
from app.models.network_segment import NetworkSegment
from app.models.operation_log import OperationLog
from app.models.user import User


class TestStatisticsService:
    """Test suite for StatisticsService"""
    
    def test_get_overview_stats_empty_database(self, db_session):
        """
        Test overview stats with empty database
        
        Validates: Requirements 7.4
        """
        stats_service = StatisticsService(db_session)
        stats = stats_service.get_overview_stats()
        
        assert stats["total_ips"] == 0
        assert stats["used_ips"] == 0
        assert stats["available_ips"] == 0
        assert stats["reserved_ips"] == 0
        assert stats["total_devices"] == 0
        assert stats["total_segments"] == 0
        assert stats["overall_usage_rate"] == 0.0
    
    def test_get_overview_stats_with_data(self, db_session, test_user, test_segment):
        """
        Test overview stats with sample data
        
        Validates: Requirements 7.4
        """
        # Create test IPs with different statuses
        ip1 = IPAddress(
            ip_address="192.168.1.10",
            status="used",
            segment_id=test_segment.id,
            allocated_by=test_user.id
        )
        ip2 = IPAddress(
            ip_address="192.168.1.11",
            status="available",
            segment_id=test_segment.id
        )
        ip3 = IPAddress(
            ip_address="192.168.1.12",
            status="reserved",
            segment_id=test_segment.id
        )
        
        db_session.add_all([ip1, ip2, ip3])
        
        # Create test device
        device = Device(
            name="Test Device",
            mac_address="AA:BB:CC:DD:EE:FF",
            owner="Test Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        
        # Get stats
        stats_service = StatisticsService(db_session)
        stats = stats_service.get_overview_stats()
        
        assert stats["total_ips"] == 3
        assert stats["used_ips"] == 1
        assert stats["available_ips"] == 1
        assert stats["reserved_ips"] == 1
        assert stats["total_devices"] == 1
        assert stats["total_segments"] == 1
        # Usage rate = (1 used + 1 reserved) / 3 total * 100 = 66.67%
        assert abs(stats["overall_usage_rate"] - 66.67) < 0.01
    
    def test_get_segment_usage_distribution(self, db_session, test_user):
        """
        Test segment usage distribution calculation
        
        Validates: Requirements 7.1
        """
        # Create test segment (192.168.1.0/24 = 254 usable IPs)
        segment = NetworkSegment(
            name="Test Segment",
            network="192.168.1.0",
            prefix_length=24,
            usage_threshold=80,
            created_by=test_user.id
        )
        db_session.add(segment)
        db_session.commit()
        
        # Create test IPs
        ip1 = IPAddress(
            ip_address="192.168.1.10",
            status="used",
            segment_id=segment.id
        )
        ip2 = IPAddress(
            ip_address="192.168.1.11",
            status="used",
            segment_id=segment.id
        )
        ip3 = IPAddress(
            ip_address="192.168.1.12",
            status="reserved",
            segment_id=segment.id
        )
        ip4 = IPAddress(
            ip_address="192.168.1.13",
            status="available",
            segment_id=segment.id
        )
        
        db_session.add_all([ip1, ip2, ip3, ip4])
        db_session.commit()
        
        # Get segment usage distribution
        stats_service = StatisticsService(db_session)
        distribution = stats_service.get_segment_usage_distribution()
        
        assert len(distribution) == 1
        segment_stats = distribution[0]
        
        assert segment_stats["segment_id"] == segment.id
        assert segment_stats["segment_name"] == "Test Segment"
        assert segment_stats["network"] == "192.168.1.0"
        assert segment_stats["prefix_length"] == 24
        assert segment_stats["total_ips"] == 254  # 2^(32-24) - 2
        assert segment_stats["used_ips"] == 2
        assert segment_stats["available_ips"] == 1
        assert segment_stats["reserved_ips"] == 1
        # Usage rate = (2 used + 1 reserved) / 254 total * 100 = 1.18%
        assert abs(segment_stats["usage_rate"] - 1.18) < 0.01
        assert segment_stats["usage_threshold"] == 80
    
    def test_get_segment_usage_distribution_multiple_segments(self, db_session, test_user):
        """
        Test segment usage distribution with multiple segments
        
        Validates: Requirements 7.1
        """
        # Create two segments
        segment1 = NetworkSegment(
            name="Segment 1",
            network="192.168.1.0",
            prefix_length=24,
            usage_threshold=80,
            created_by=test_user.id
        )
        segment2 = NetworkSegment(
            name="Segment 2",
            network="10.0.0.0",
            prefix_length=16,
            usage_threshold=90,
            created_by=test_user.id
        )
        db_session.add_all([segment1, segment2])
        db_session.commit()
        
        # Add IPs to segment1
        ip1 = IPAddress(
            ip_address="192.168.1.10",
            status="used",
            segment_id=segment1.id
        )
        db_session.add(ip1)
        
        # Add IPs to segment2
        ip2 = IPAddress(
            ip_address="10.0.0.10",
            status="reserved",
            segment_id=segment2.id
        )
        db_session.add(ip2)
        db_session.commit()
        
        # Get distribution
        stats_service = StatisticsService(db_session)
        distribution = stats_service.get_segment_usage_distribution()
        
        assert len(distribution) == 2
        
        # Verify segment1
        seg1_stats = next(s for s in distribution if s["segment_id"] == segment1.id)
        assert seg1_stats["used_ips"] == 1
        assert seg1_stats["reserved_ips"] == 0
        
        # Verify segment2
        seg2_stats = next(s for s in distribution if s["segment_id"] == segment2.id)
        assert seg2_stats["used_ips"] == 0
        assert seg2_stats["reserved_ips"] == 1
    
    def test_get_ip_status_distribution(self, db_session, test_user, test_segment):
        """
        Test IP status distribution calculation
        
        Validates: Requirements 7.2
        """
        # Create IPs with different statuses
        ips = [
            IPAddress(ip_address="192.168.1.10", status="used", segment_id=test_segment.id),
            IPAddress(ip_address="192.168.1.11", status="used", segment_id=test_segment.id),
            IPAddress(ip_address="192.168.1.12", status="available", segment_id=test_segment.id),
            IPAddress(ip_address="192.168.1.13", status="available", segment_id=test_segment.id),
            IPAddress(ip_address="192.168.1.14", status="available", segment_id=test_segment.id),
            IPAddress(ip_address="192.168.1.15", status="reserved", segment_id=test_segment.id),
        ]
        db_session.add_all(ips)
        db_session.commit()
        
        # Get IP status distribution
        stats_service = StatisticsService(db_session)
        distribution = stats_service.get_ip_status_distribution()
        
        assert distribution["available"] == 3
        assert distribution["used"] == 2
        assert distribution["reserved"] == 1
        assert distribution["total"] == 6
        
        # Check percentages
        assert abs(distribution["distribution"]["available"] - 50.0) < 0.01  # 3/6 = 50%
        assert abs(distribution["distribution"]["used"] - 33.33) < 0.01  # 2/6 = 33.33%
        assert abs(distribution["distribution"]["reserved"] - 16.67) < 0.01  # 1/6 = 16.67%
    
    def test_get_ip_status_distribution_empty(self, db_session):
        """
        Test IP status distribution with no IPs
        
        Validates: Requirements 7.2
        """
        stats_service = StatisticsService(db_session)
        distribution = stats_service.get_ip_status_distribution()
        
        assert distribution["available"] == 0
        assert distribution["used"] == 0
        assert distribution["reserved"] == 0
        assert distribution["total"] == 0
        assert distribution["distribution"]["available"] == 0.0
        assert distribution["distribution"]["used"] == 0.0
        assert distribution["distribution"]["reserved"] == 0.0
    
    def test_get_device_statistics(self, db_session, test_user):
        """
        Test device statistics calculation
        
        Validates: Requirements 7.3
        """
        # Create devices with different types
        devices = [
            Device(
                name="Server 1",
                mac_address="AA:BB:CC:DD:EE:01",
                device_type="server",
                owner="Owner 1",
                created_by=test_user.id,
                created_at=datetime.now() - timedelta(days=5)
            ),
            Device(
                name="Server 2",
                mac_address="AA:BB:CC:DD:EE:02",
                device_type="server",
                owner="Owner 2",
                created_by=test_user.id,
                created_at=datetime.now() - timedelta(days=3)
            ),
            Device(
                name="Switch 1",
                mac_address="AA:BB:CC:DD:EE:03",
                device_type="switch",
                owner="Owner 3",
                created_by=test_user.id,
                created_at=datetime.now() - timedelta(days=1)
            ),
        ]
        db_session.add_all(devices)
        db_session.commit()
        
        # Get device statistics
        stats_service = StatisticsService(db_session)
        stats = stats_service.get_device_statistics(days=30)
        
        assert stats["total_devices"] == 3
        assert stats["device_types"]["server"] == 2
        assert stats["device_types"]["switch"] == 1
        
        # Check growth trend
        assert len(stats["growth_trend"]) == 31  # 30 days + today
        
        # Verify cumulative count increases
        cumulative_counts = [day["cumulative_count"] for day in stats["growth_trend"]]
        assert cumulative_counts[-1] == 3  # Final count should be 3
    
    def test_get_device_statistics_with_null_type(self, db_session, test_user):
        """
        Test device statistics with devices that have no type
        
        Validates: Requirements 7.3
        """
        device = Device(
            name="Unknown Device",
            mac_address="AA:BB:CC:DD:EE:FF",
            device_type=None,
            owner="Owner",
            created_by=test_user.id
        )
        db_session.add(device)
        db_session.commit()
        
        stats_service = StatisticsService(db_session)
        stats = stats_service.get_device_statistics(days=30)
        
        assert stats["total_devices"] == 1
        assert "未分类" in stats["device_types"]
        assert stats["device_types"]["未分类"] == 1
    
    def test_get_recent_activities(self, db_session, test_user):
        """
        Test fetching recent activities
        """
        # Create operation logs
        logs = [
            OperationLog(
                user_id=test_user.id,
                username=test_user.username,
                operation_type="create",
                resource_type="device",
                resource_id=1,
                created_at=datetime.now() - timedelta(minutes=i)
            )
            for i in range(15)
        ]
        db_session.add_all(logs)
        db_session.commit()
        
        # Get recent activities (limit 10)
        stats_service = StatisticsService(db_session)
        activities = stats_service.get_recent_activities(limit=10)
        
        assert len(activities) == 10
        
        # Verify they are ordered by created_at descending
        for i in range(len(activities) - 1):
            assert activities[i]["created_at"] >= activities[i + 1]["created_at"]
    
    def test_get_time_range_stats(self, db_session, test_user, test_segment):
        """
        Test time range statistics
        
        Validates: Requirements 7.6
        """
        # Set up time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Create devices within time range
        device1 = Device(
            name="Device 1",
            mac_address="AA:BB:CC:DD:EE:01",
            owner="Owner",
            created_by=test_user.id,
            created_at=start_date + timedelta(days=1)
        )
        device2 = Device(
            name="Device 2",
            mac_address="AA:BB:CC:DD:EE:02",
            owner="Owner",
            created_by=test_user.id,
            created_at=start_date + timedelta(days=3)
        )
        db_session.add_all([device1, device2])
        
        # Create IPs within time range
        ip1 = IPAddress(
            ip_address="192.168.1.10",
            status="used",
            segment_id=test_segment.id,
            allocated_at=start_date + timedelta(days=2),
            allocated_by=test_user.id
        )
        db_session.add(ip1)
        
        # Create operation logs within time range
        log1 = OperationLog(
            user_id=test_user.id,
            username=test_user.username,
            operation_type="create",
            resource_type="device",
            resource_id=1,
            created_at=start_date + timedelta(days=1)
        )
        log2 = OperationLog(
            user_id=test_user.id,
            username=test_user.username,
            operation_type="allocate",
            resource_type="ip",
            resource_id=1,
            created_at=start_date + timedelta(days=2)
        )
        db_session.add_all([log1, log2])
        db_session.commit()
        
        # Get time range stats
        stats_service = StatisticsService(db_session)
        stats = stats_service.get_time_range_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        assert stats["devices_created"] == 2
        assert stats["ips_allocated"] == 1
        assert stats["operations_count"] == 2
        assert stats["operation_types"]["create"] == 1
        assert stats["operation_types"]["allocate"] == 1
    
    def test_get_time_range_stats_default_range(self, db_session):
        """
        Test time range stats with default range (30 days)
        
        Validates: Requirements 7.6
        """
        stats_service = StatisticsService(db_session)
        stats = stats_service.get_time_range_stats()
        
        # Should return stats for last 30 days
        assert "start_date" in stats
        assert "end_date" in stats
        assert stats["devices_created"] == 0
        assert stats["ips_allocated"] == 0
        assert stats["operations_count"] == 0
