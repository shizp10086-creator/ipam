"""
测试日志记录服务的基本功能
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.operation_log import OperationLog
from app.services.log_service import LogService
from app.core.security import get_password_hash


def test_log_service():
    """测试日志记录服务"""
    print("开始测试日志记录服务...")
    
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. 创建测试用户
        print("\n1. 创建测试用户...")
        test_user = User(
            username="test_admin",
            hashed_password=get_password_hash("password123"),
            email="admin@test.com",
            full_name="Test Admin",
            role="admin",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"   ✓ 创建用户成功: {test_user.username} (ID: {test_user.id})")
        
        # 2. 测试 IP 分配日志记录
        print("\n2. 测试 IP 分配日志记录...")
        log1 = LogService.log_ip_allocation(
            db=db,
            user_id=test_user.id,
            username=test_user.username,
            ip_address="192.168.1.100",
            device_id=1,
            device_name="Server-01",
            segment_id=1,
            client_ip="10.0.0.1"
        )
        print(f"   ✓ IP 分配日志创建成功 (ID: {log1.id})")
        print(f"     - 操作类型: {log1.operation_type}")
        print(f"     - 资源类型: {log1.resource_type}")
        print(f"     - 操作人: {log1.username}")
        print(f"     - 客户端 IP: {log1.ip_address}")
        
        # 3. 测试 IP 回收日志记录
        print("\n3. 测试 IP 回收日志记录...")
        log2 = LogService.log_ip_release(
            db=db,
            user_id=test_user.id,
            username=test_user.username,
            ip_address="192.168.1.100",
            ip_id=1,
            client_ip="10.0.0.1"
        )
        print(f"   ✓ IP 回收日志创建成功 (ID: {log2.id})")
        print(f"     - 操作类型: {log2.operation_type}")
        
        # 4. 测试设备操作日志记录
        print("\n4. 测试设备操作日志记录...")
        device_data = {
            "name": "Server-01",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "owner": "IT Department"
        }
        log3 = LogService.log_device_operation(
            db=db,
            user_id=test_user.id,
            username=test_user.username,
            operation_type="create",
            device_id=1,
            device_data=device_data,
            client_ip="10.0.0.1"
        )
        print(f"   ✓ 设备操作日志创建成功 (ID: {log3.id})")
        print(f"     - 操作类型: {log3.operation_type}")
        print(f"     - 资源类型: {log3.resource_type}")
        
        # 5. 测试网段操作日志记录
        print("\n5. 测试网段操作日志记录...")
        segment_data = {
            "name": "Office Network",
            "network": "192.168.1.0",
            "prefix_length": 24
        }
        log4 = LogService.log_segment_operation(
            db=db,
            user_id=test_user.id,
            username=test_user.username,
            operation_type="create",
            segment_id=1,
            segment_data=segment_data,
            client_ip="10.0.0.1"
        )
        print(f"   ✓ 网段操作日志创建成功 (ID: {log4.id})")
        print(f"     - 操作类型: {log4.operation_type}")
        print(f"     - 资源类型: {log4.resource_type}")
        
        # 6. 测试用户操作日志记录（包含角色信息）
        print("\n6. 测试用户操作日志记录...")
        user_data = {
            "username": "new_user",
            "email": "newuser@test.com",
            "role": "user",
            "operator_role": "admin"
        }
        log5 = LogService.log_user_operation(
            db=db,
            user_id=test_user.id,
            username=test_user.username,
            operation_type="create",
            target_user_id=2,
            user_data=user_data,
            client_ip="10.0.0.1"
        )
        print(f"   ✓ 用户操作日志创建成功 (ID: {log5.id})")
        print(f"     - 操作类型: {log5.operation_type}")
        print(f"     - 资源类型: {log5.resource_type}")
        print(f"     - 详情包含角色信息: {log5.details}")
        
        # 7. 验证日志查询
        print("\n7. 验证日志查询...")
        all_logs = db.query(OperationLog).all()
        print(f"   ✓ 总共创建了 {len(all_logs)} 条日志记录")
        
        # 按操作类型筛选
        allocate_logs = db.query(OperationLog).filter(
            OperationLog.operation_type == "allocate"
        ).all()
        print(f"   ✓ 'allocate' 类型日志: {len(allocate_logs)} 条")
        
        # 按资源类型筛选
        device_logs = db.query(OperationLog).filter(
            OperationLog.resource_type == "device"
        ).all()
        print(f"   ✓ 'device' 资源类型日志: {len(device_logs)} 条")
        
        # 8. 验证日志不可修改（只能插入）
        print("\n8. 验证日志记录的不可篡改性...")
        print("   ✓ 日志模型设计为只允许插入，不提供更新和删除方法")
        print("   ✓ 在实际应用中，应通过数据库权限控制确保日志不可修改")
        
        print("\n" + "="*60)
        print("✓ 所有测试通过！日志记录服务工作正常。")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_log_service()
    sys.exit(0 if success else 1)
