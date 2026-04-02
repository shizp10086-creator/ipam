"""
Integration tests for User API endpoints
测试用户管理 API 接口
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash
from app.core.database import get_db


def override_get_db(db_session):
    """覆盖数据库依赖"""
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


class TestUserAPI:
    """测试用户管理 API"""
    
    def test_create_user_success(self, db_session):
        """测试创建用户成功"""
        app.dependency_overrides[get_db] = override_get_db(db_session)
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/users/",
            json={
                "username": "testuser123",
                "password": "password123",
                "email": "testuser123@example.com",
                "full_name": "Test User",
                "role": "user",
                "is_active": True
            }
        )
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 201
        assert data["data"]["username"] == "testuser123"
        assert data["data"]["email"] == "testuser123@example.com"
        assert data["data"]["role"] == "user"
        assert "password" not in data["data"]  # 密码不应该在响应中
    
    def test_create_user_duplicate_username(self, db_session, test_user):
        """测试创建重复用户名的用户"""
        response = client.post(
            "/api/v1/users/",
            json={
                "username": test_user.username,  # 使用已存在的用户名
                "password": "password123",
                "email": "newemail@example.com",
                "full_name": "New User",
                "role": "user"
            }
        )
        
        assert response.status_code == 400
        assert "已存在" in response.json()["detail"]
    
    def test_create_user_duplicate_email(self, db_session, test_user):
        """测试创建重复邮箱的用户"""
        response = client.post(
            "/api/v1/users/",
            json={
                "username": "newuser123",
                "password": "password123",
                "email": test_user.email,  # 使用已存在的邮箱
                "full_name": "New User",
                "role": "user"
            }
        )
        
        assert response.status_code == 400
        assert "已被使用" in response.json()["detail"]
    
    def test_create_user_invalid_role(self, db_session):
        """测试创建用户时使用无效角色"""
        response = client.post(
            "/api/v1/users/",
            json={
                "username": "testuser456",
                "password": "password123",
                "email": "testuser456@example.com",
                "full_name": "Test User",
                "role": "invalid_role"  # 无效角色
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_user_short_password(self, db_session):
        """测试创建用户时使用过短的密码"""
        response = client.post(
            "/api/v1/users/",
            json={
                "username": "testuser789",
                "password": "12345",  # 少于6个字符
                "email": "testuser789@example.com",
                "full_name": "Test User",
                "role": "user"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_users_list(self, db_session, test_user):
        """测试获取用户列表"""
        # 创建几个测试用户
        for i in range(3):
            user = User(
                username=f"listuser{i}",
                hashed_password=get_password_hash("password123"),
                email=f"listuser{i}@example.com",
                full_name=f"List User {i}",
                role="user"
            )
            db_session.add(user)
        db_session.commit()
        
        response = client.get("/api/v1/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) >= 3
    
    def test_get_users_with_search(self, db_session, test_user):
        """测试用户搜索功能"""
        # 创建测试用户
        user = User(
            username="searchuser",
            hashed_password=get_password_hash("password123"),
            email="searchuser@example.com",
            full_name="Search User Special",
            role="user"
        )
        db_session.add(user)
        db_session.commit()
        
        # 搜索用户名
        response = client.get("/api/v1/users/?keyword=searchuser")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) >= 1
        assert any("searchuser" in item["username"] for item in data["data"]["items"])
    
    def test_get_users_filter_by_role(self, db_session, test_user):
        """测试按角色筛选用户"""
        # 创建不同角色的用户
        admin_user = User(
            username="adminuser",
            hashed_password=get_password_hash("password123"),
            email="adminuser@example.com",
            full_name="Admin User",
            role="admin"
        )
        db_session.add(admin_user)
        db_session.commit()
        
        # 筛选管理员
        response = client.get("/api/v1/users/?role=admin")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert all(item["role"] == "admin" for item in data["data"]["items"])
    
    def test_get_user_by_id(self, db_session, test_user):
        """测试获取用户详情"""
        response = client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == test_user.id
        assert data["data"]["username"] == test_user.username
    
    def test_get_user_not_found(self, db_session):
        """测试获取不存在的用户"""
        response = client.get("/api/v1/users/99999")
        
        assert response.status_code == 404
    
    def test_update_user_success(self, db_session, test_user):
        """测试更新用户信息成功"""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json={
                "full_name": "Updated Name",
                "email": "updated@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["full_name"] == "Updated Name"
        assert data["data"]["email"] == "updated@example.com"
    
    def test_update_user_duplicate_email(self, db_session, test_user):
        """测试更新用户时使用已存在的邮箱"""
        # 创建另一个用户
        other_user = User(
            username="otheruser",
            hashed_password=get_password_hash("password123"),
            email="other@example.com",
            full_name="Other User",
            role="user"
        )
        db_session.add(other_user)
        db_session.commit()
        
        # 尝试将 test_user 的邮箱改为 other_user 的邮箱
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json={
                "email": other_user.email
            }
        )
        
        assert response.status_code == 400
        assert "已被使用" in response.json()["detail"]
    
    def test_delete_user_success(self, db_session):
        """测试删除用户成功"""
        # 创建一个用户用于删除
        user = User(
            username="deleteuser",
            hashed_password=get_password_hash("password123"),
            email="deleteuser@example.com",
            full_name="Delete User",
            role="user"
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        response = client.delete(f"/api/v1/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        
        # 验证用户已被删除
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None
    
    def test_delete_user_not_found(self, db_session):
        """测试删除不存在的用户"""
        response = client.delete("/api/v1/users/99999")
        
        assert response.status_code == 404
    
    def test_change_password_success(self, db_session, test_user):
        """测试修改密码成功"""
        response = client.put(
            f"/api/v1/users/{test_user.id}/password",
            json={
                "old_password": "password123",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "密码修改成功"
    
    def test_change_password_wrong_old_password(self, db_session, test_user):
        """测试修改密码时旧密码错误"""
        response = client.put(
            f"/api/v1/users/{test_user.id}/password",
            json={
                "old_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 400
        assert "旧密码不正确" in response.json()["detail"]
    
    def test_change_password_same_as_old(self, db_session, test_user):
        """测试修改密码时新密码与旧密码相同"""
        response = client.put(
            f"/api/v1/users/{test_user.id}/password",
            json={
                "old_password": "password123",
                "new_password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "不能与旧密码相同" in response.json()["detail"]
    
    def test_change_password_user_not_found(self, db_session):
        """测试修改不存在用户的密码"""
        response = client.put(
            "/api/v1/users/99999/password",
            json={
                "old_password": "password123",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 404
