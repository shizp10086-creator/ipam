#!/bin/bash
# RADIUS 认证测试脚本
# 使用 radtest 工具测试 FreeRADIUS 是否正常工作
#
# 前置条件：
# 1. docker-compose up -d mysql freeradius
# 2. 数据库中已有 radius_users 表和测试用户
#
# 用法：
# docker exec ipam-freeradius bash /test-radius.sh

echo "=== FreeRADIUS 认证测试 ==="
echo ""

# 测试 1：PAP 密码认证（模拟 Portal 认证）
echo "--- 测试 1: PAP 密码认证 ---"
echo "User-Name=testuser, Password=test123"
radtest testuser test123 127.0.0.1 0 testing123
echo ""

# 测试 2：错误密码（应该被拒绝）
echo "--- 测试 2: 错误密码（应拒绝） ---"
echo "User-Name=testuser, Password=wrongpass"
radtest testuser wrongpass 127.0.0.1 0 testing123
echo ""

# 测试 3：不存在的用户（应该被拒绝）
echo "--- 测试 3: 不存在的用户（应拒绝） ---"
echo "User-Name=nobody, Password=test123"
radtest nobody test123 127.0.0.1 0 testing123
echo ""

echo "=== 测试完成 ==="
echo "如果测试 1 返回 Access-Accept，测试 2/3 返回 Access-Reject，说明 RADIUS 认证正常工作。"
