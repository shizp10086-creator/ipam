"""
验证用户管理模块的实现
"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, PasswordChangeRequest
from app.core.security import get_password_hash, verify_password


def test_user_schemas():
    """测试用户数据模式"""
    print("测试用户数据模式...")
    
    # 测试 UserCreate
    user_create = UserCreate(
        username="testuser",
        password="password123",
        email="test@example.com",
        full_name="Test User",
        role="user",
        is_active=True
    )
    assert user_create.username == "testuser"
    assert user_create.role == "user"
    print("✓ UserCreate 模式验证通过")
    
    # 测试无效角色
    try:
        invalid_user = UserCreate(
            username="testuser",
            password="password123",
            email="test@example.com",
            full_name="Test User",
            role="invalid_role",
            is_active=True
        )
        print("✗ 应该拒绝无效角色")
        return False
    except Exception as e:
        print(f"✓ 正确拒绝无效角色: {str(e)}")
    
    # 测试 UserUpdate
    user_update = UserUpdate(
        email="newemail@example.com",
        full_name="Updated Name"
    )
    assert user_update.email == "newemail@example.com"
    print("✓ UserUpdate 模式验证通过")
    
    # 测试 PasswordChangeRequest
    password_change = PasswordChangeRequest(
        old_password="oldpass123",
        new_password="newpass123"
    )
    assert password_change.old_password == "oldpass123"
    print("✓ PasswordChangeRequest 模式验证通过")
    
    return True


def test_user_model():
    """测试用户模型"""
    print("\n测试用户模型...")
    
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # 创建用户
        hashed_password = get_password_hash("password123")
        user = User(
            username="testuser",
            hashed_password=hashed_password,
            email="test@example.com",
            full_name="Test User",
            role="admin",
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.role == "admin"
        print(f"✓ 用户创建成功: ID={user.id}, username={user.username}")
        
        # 验证密码
        assert verify_password("password123", user.hashed_password)
        print("✓ 密码验证成功")
        
        # 查询用户
        found_user = session.query(User).filter(User.username == "testuser").first()
        assert found_user is not None
        assert found_user.email == "test@example.com"
        print("✓ 用户查询成功")
        
        # 更新用户
        found_user.full_name = "Updated Name"
        session.commit()
        session.refresh(found_user)
        assert found_user.full_name == "Updated Name"
        print("✓ 用户更新成功")
        
        # 删除用户
        session.delete(found_user)
        session.commit()
        deleted_user = session.query(User).filter(User.id == user.id).first()
        assert deleted_user is None
        print("✓ 用户删除成功")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def test_api_imports():
    """测试 API 模块导入"""
    print("\n测试 API 模块导入...")
    
    try:
        from app.api import users
        print("✓ users API 模块导入成功")
        
        # 检查路由是否定义
        assert hasattr(users, 'router')
        print("✓ router 已定义")
        
        # 检查关键函数是否存在
        assert hasattr(users, 'get_users')
        assert hasattr(users, 'create_user')
        assert hasattr(users, 'get_user')
        assert hasattr(users, 'update_user')
        assert hasattr(users, 'delete_user')
        assert hasattr(users, 'change_password')
        print("✓ 所有 API 端点函数已定义")
        
        return True
    except Exception as e:
        print(f"✗ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("验证用户管理模块")
    print("=" * 60)
    
    results = []
    
    # 测试数据模式
    results.append(("数据模式", test_user_schemas()))
    
    # 测试用户模型
    results.append(("用户模型", test_user_model()))
    
    # 测试 API 导入
    results.append(("API 导入", test_api_imports()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n所有测试通过！用户管理模块实现正确。")
        return 0
    else:
        print("\n部分测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
