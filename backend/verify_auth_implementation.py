"""
验证认证和授权实现
"""
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from datetime import timedelta


def test_password_hashing():
    """测试密码加密和验证"""
    print("测试密码加密和验证...")
    
    password = "testpass123"
    hashed = get_password_hash(password)
    
    # 验证密码
    assert verify_password(password, hashed), "密码验证失败"
    assert not verify_password("wrongpass", hashed), "错误密码应该验证失败"
    
    print("✓ 密码加密和验证功能正常")


def test_jwt_tokens():
    """测试 JWT token 生成和验证"""
    print("\n测试 JWT token 生成和验证...")
    
    # 测试数据
    user_data = {
        "sub": 1,  # 会被自动转换为字符串
        "role": "admin",
        "username": "testuser"
    }
    
    # 生成 access token
    access_token = create_access_token(data=user_data)
    assert access_token, "Access token 生成失败"
    print(f"✓ Access token 生成成功: {access_token[:50]}...")
    
    # 验证 access token
    payload = verify_token(access_token, token_type="access")
    assert payload is not None, "Access token 验证失败"
    assert payload["sub"] == "1", "Token payload 中的 user_id 不正确"
    assert payload["role"] == "admin", "Token payload 中的 role 不正确"
    assert payload["type"] == "access", "Token type 不正确"
    print("✓ Access token 验证成功")
    
    # 生成 refresh token
    refresh_token = create_refresh_token(data=user_data)
    assert refresh_token, "Refresh token 生成失败"
    print(f"✓ Refresh token 生成成功: {refresh_token[:50]}...")
    
    # 验证 refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    assert payload is not None, "Refresh token 验证失败"
    assert payload["sub"] == "1", "Token payload 中的 user_id 不正确"
    assert payload["type"] == "refresh", "Token type 不正确"
    print("✓ Refresh token 验证成功")
    
    # 测试 token 类型验证
    payload = verify_token(access_token, token_type="refresh")
    assert payload is None, "Access token 不应该通过 refresh token 验证"
    print("✓ Token 类型验证正常")
    
    # 测试无效 token
    payload = verify_token("invalid_token", token_type="access")
    assert payload is None, "无效 token 应该验证失败"
    print("✓ 无效 token 验证正常")


def test_token_expiration():
    """测试 token 过期"""
    print("\n测试 token 过期...")
    
    user_data = {
        "sub": 1,
        "role": "admin"
    }
    
    # 创建一个已过期的 token（过期时间为 -1 秒）
    expired_token = create_access_token(
        data=user_data,
        expires_delta=timedelta(seconds=-1)
    )
    
    # 验证过期 token
    payload = verify_token(expired_token, token_type="access")
    assert payload is None, "过期 token 应该验证失败"
    print("✓ Token 过期验证正常")


def test_role_definitions():
    """测试角色定义"""
    print("\n测试角色定义...")
    
    valid_roles = ["admin", "user", "readonly"]
    
    for role in valid_roles:
        user_data = {
            "sub": 1,
            "role": role
        }
        token = create_access_token(data=user_data)
        payload = verify_token(token, token_type="access")
        assert payload["role"] == role, f"角色 {role} 验证失败"
    
    print(f"✓ 所有角色定义正常: {', '.join(valid_roles)}")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始验证认证和授权实现")
    print("=" * 60)
    
    try:
        test_password_hashing()
        test_jwt_tokens()
        test_token_expiration()
        test_role_definitions()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！认证和授权功能实现正确。")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
