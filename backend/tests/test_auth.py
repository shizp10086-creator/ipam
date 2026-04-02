"""
Authentication Tests
测试认证和授权功能
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash, verify_token
from app.core.database import get_db


def override_get_db(db_session):
    """覆盖数据库依赖"""
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


@pytest.fixture
def client(db_session):
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_login_success(client, db_session: Session, test_user: User):
    """测试成功登录"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    
    # 验证 access token
    payload = verify_token(data["access_token"], token_type="access")
    assert payload is not None
    assert payload["sub"] == test_user.id
    assert payload["role"] == test_user.role
    
    # 验证 refresh token
    payload = verify_token(data["refresh_token"], token_type="refresh")
    assert payload is not None
    assert payload["sub"] == test_user.id


def test_login_invalid_username(client, db_session: Session):
    """测试使用无效用户名登录"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


def test_login_invalid_password(client, db_session: Session, test_user: User):
    """测试使用错误密码登录"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


def test_login_inactive_user(client, db_session: Session):
    """测试使用已禁用账户登录"""
    # 创建一个禁用的用户
    inactive_user = User(
        username="inactive_user",
        hashed_password=get_password_hash("testpass123"),
        email="inactive@test.com",
        full_name="Inactive User",
        role="user",
        is_active=False
    )
    db_session.add(inactive_user)
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "inactive_user",
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 403
    assert "已被禁用" in response.json()["detail"]


def test_refresh_token_success(client, db_session: Session, test_user: User):
    """测试成功刷新令牌"""
    # 先登录获取 refresh token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    refresh_token = login_response.json()["refresh_token"]
    
    # 使用 refresh token 获取新的 tokens
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # 验证新的 access token
    payload = verify_token(data["access_token"], token_type="access")
    assert payload is not None
    assert payload["sub"] == test_user.id


def test_refresh_token_invalid(client, db_session: Session):
    """测试使用无效的 refresh token"""
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid_token"
        }
    )
    
    assert response.status_code == 401
    assert "无效的刷新令牌" in response.json()["detail"]


def test_refresh_token_with_access_token(client, db_session: Session, test_user: User):
    """测试使用 access token 作为 refresh token（应该失败）"""
    # 先登录获取 access token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # 尝试使用 access token 刷新（应该失败）
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": access_token
        }
    )
    
    assert response.status_code == 401


def test_get_current_user_info(client, db_session: Session, test_user: User):
    """测试获取当前用户信息"""
    # 先登录获取 token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # 使用 token 获取用户信息
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role


def test_get_current_user_info_no_token(client, db_session: Session):
    """测试未提供 token 时获取用户信息"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 403  # FastAPI HTTPBearer 返回 403


def test_get_current_user_info_invalid_token(client, db_session: Session):
    """测试使用无效 token 获取用户信息"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


def test_logout(client, db_session: Session, test_user: User):
    """测试登出"""
    # 先登录获取 token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # 登出
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "登出成功" in data["message"]


def test_role_based_access_admin(client, db_session: Session, test_admin: User):
    """测试管理员角色访问"""
    # 登录管理员账户
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # 验证 token 中包含正确的角色
    payload = verify_token(access_token, token_type="access")
    assert payload["role"] == "admin"


def test_role_based_access_regular_user(client, db_session: Session, test_user: User):
    """测试普通用户角色访问"""
    # 登录普通用户账户
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # 验证 token 中包含正确的角色
    payload = verify_token(access_token, token_type="access")
    assert payload["role"] == "user"


def test_role_based_access_readonly_user(client, db_session: Session):
    """测试只读用户角色访问"""
    # 创建只读用户
    readonly_user = User(
        username="readonly_user",
        hashed_password=get_password_hash("testpass123"),
        email="readonly@test.com",
        full_name="Readonly User",
        role="readonly",
        is_active=True
    )
    db_session.add(readonly_user)
    db_session.commit()
    
    # 登录只读用户账户
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "readonly_user",
            "password": "testpass123"
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # 验证 token 中包含正确的角色
    payload = verify_token(access_token, token_type="access")
    assert payload["role"] == "readonly"
