"""
Test script to verify database models are correctly defined.

This script tests:
1. Model imports
2. Table creation
3. Basic CRUD operations
4. Relationships between models
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import (
    User, NetworkSegment, IPAddress, Device, 
    OperationLog, Alert, ScanHistory
)
from app.core.security import get_password_hash
from datetime import datetime

# Create an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_models():
    """Test all models and their relationships"""
    
    print("\n" + "="*80)
    print("Testing IPAM System Database Models")
    print("="*80 + "\n")
    
    # Create all tables
    print("1. Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully\n")
    
    # Create a test session
    db = TestSessionLocal()
    
    try:
        # Test 1: Create a User
        print("2. Testing User model...")
        user = User(
            username="testuser",
            hashed_password=get_password_hash("password123"),
            email="test@example.com",
            full_name="Test User",
            role="admin",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✓ Created user: {user}")
        print(f"  - ID: {user.id}")
        print(f"  - Username: {user.username}")
        print(f"  - Role: {user.role}\n")
        
        # Test 2: Create a NetworkSegment
        print("3. Testing NetworkSegment model...")
        segment = NetworkSegment(
            name="Test Network",
            network="192.168.1.0",
            prefix_length=24,
            gateway="192.168.1.1",
            description="Test network segment",
            usage_threshold=80,
            created_by=user.id
        )
        db.add(segment)
        db.commit()
        db.refresh(segment)
        print(f"✓ Created network segment: {segment}")
        print(f"  - ID: {segment.id}")
        print(f"  - Network: {segment.network}/{segment.prefix_length}")
        print(f"  - Creator: {segment.creator.username}\n")
        
        # Test 3: Create a Device
        print("4. Testing Device model...")
        device = Device(
            name="Test Server",
            mac_address="00:11:22:33:44:55",
            device_type="server",
            manufacturer="Dell",
            model="PowerEdge R740",
            owner="IT Department",
            department="Infrastructure",
            location="Data Center A",
            description="Test server device",
            created_by=user.id
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        print(f"✓ Created device: {device}")
        print(f"  - ID: {device.id}")
        print(f"  - Name: {device.name}")
        print(f"  - MAC: {device.mac_address}")
        print(f"  - Creator: {device.creator.username}\n")
        
        # Test 4: Create an IPAddress
        print("5. Testing IPAddress model...")
        ip = IPAddress(
            ip_address="192.168.1.100",
            status="used",
            segment_id=segment.id,
            device_id=device.id,
            allocated_by=user.id,
            allocated_at=datetime.now(),
            is_online=True
        )
        db.add(ip)
        db.commit()
        db.refresh(ip)
        print(f"✓ Created IP address: {ip}")
        print(f"  - ID: {ip.id}")
        print(f"  - IP: {ip.ip_address}")
        print(f"  - Status: {ip.status}")
        print(f"  - Segment: {ip.segment.name}")
        print(f"  - Device: {ip.device.name}")
        print(f"  - Allocator: {ip.allocator.username}\n")
        
        # Test 5: Create an OperationLog
        print("6. Testing OperationLog model...")
        log = OperationLog(
            user_id=user.id,
            username=user.username,
            operation_type="allocate",
            resource_type="ip",
            resource_id=ip.id,
            details='{"ip": "192.168.1.100", "device": "Test Server"}',
            ip_address="127.0.0.1"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        print(f"✓ Created operation log: {log}")
        print(f"  - ID: {log.id}")
        print(f"  - User: {log.username}")
        print(f"  - Operation: {log.operation_type}")
        print(f"  - Resource: {log.resource_type}\n")
        
        # Test 6: Create an Alert
        print("7. Testing Alert model...")
        alert = Alert(
            segment_id=segment.id,
            alert_type="usage_threshold",
            severity="warning",
            message="Network segment usage exceeded 80%",
            current_usage=85.5,
            threshold=80.0,
            is_resolved=False
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        print(f"✓ Created alert: {alert}")
        print(f"  - ID: {alert.id}")
        print(f"  - Type: {alert.alert_type}")
        print(f"  - Severity: {alert.severity}")
        print(f"  - Segment: {alert.segment.name}")
        print(f"  - Current Usage: {alert.current_usage}%\n")
        
        # Test 7: Create a ScanHistory
        print("8. Testing ScanHistory model...")
        scan = ScanHistory(
            segment_id=segment.id,
            created_by=user.id,
            scan_type="ping",
            total_ips=254,
            online_ips=120,
            duration=3.5,
            results='{"online": ["192.168.1.1", "192.168.1.100"]}'
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        print(f"✓ Created scan history: {scan}")
        print(f"  - ID: {scan.id}")
        print(f"  - Segment: {scan.segment.name}")
        print(f"  - Type: {scan.scan_type}")
        print(f"  - Online IPs: {scan.online_ips}/{scan.total_ips}")
        print(f"  - Duration: {scan.duration}s")
        print(f"  - Creator: {scan.creator.username}\n")
        
        # Test 8: Verify relationships
        print("9. Testing relationships...")
        
        # User relationships
        print(f"✓ User has {len(user.network_segments)} network segments")
        print(f"✓ User has {len(user.allocated_ips)} allocated IPs")
        print(f"✓ User has {len(user.devices)} devices")
        print(f"✓ User has {len(user.operation_logs)} operation logs")
        print(f"✓ User has {len(user.scan_histories)} scan histories")
        
        # NetworkSegment relationships
        print(f"✓ Network segment has {len(segment.ip_addresses)} IP addresses")
        print(f"✓ Network segment has {len(segment.alerts)} alerts")
        print(f"✓ Network segment has {len(segment.scan_histories)} scan histories")
        
        # Device relationships
        print(f"✓ Device has {len(device.ip_addresses)} IP addresses")
        
        print("\n" + "="*80)
        print("All tests passed successfully! ✓")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_models()
    sys.exit(0 if success else 1)
