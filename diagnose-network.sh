#!/bin/bash
# IPAM 系统网络诊断脚本
# 用于诊断 Ping 扫描问题并找到正确的源 IP 配置

echo "========================================="
echo "IPAM 系统网络诊断工具"
echo "========================================="
echo ""

# 检查目标 IP（从参数获取，默认为 172.18.201.56）
TARGET_IP="${1:-172.18.201.56}"
echo "目标 IP: $TARGET_IP"
echo ""

# 1. 显示所有网络接口
echo "1. 宿主机网络接口："
echo "-------------------"
ip addr show | grep -E "^[0-9]+:|inet " | grep -v "127.0.0.1"
echo ""

# 2. 显示路由表
echo "2. 路由表："
echo "-------------------"
ip route
echo ""

# 3. 测试默认路由 ping
echo "3. 测试默认路由 ping："
echo "-------------------"
echo "命令: ping -c 1 -W 2 $TARGET_IP"
if ping -c 1 -W 2 $TARGET_IP > /dev/null 2>&1; then
    echo "✓ 成功：使用默认路由可以 ping 通 $TARGET_IP"
else
    echo "✗ 失败：使用默认路由无法 ping 通 $TARGET_IP"
fi
echo ""

# 4. 查找可能的源 IP
echo "4. 查找可能的源 IP："
echo "-------------------"
# 提取目标 IP 的网段（前三段）
TARGET_NETWORK=$(echo $TARGET_IP | cut -d. -f1-3)
echo "目标网段: $TARGET_NETWORK.0/24"
echo ""

# 查找匹配的网络接口
echo "查找宿主机上属于该网段的 IP："
MATCHING_IPS=$(ip addr show | grep "inet $TARGET_NETWORK" | awk '{print $2}' | cut -d/ -f1)

if [ -z "$MATCHING_IPS" ]; then
    echo "✗ 未找到匹配的 IP 地址"
    echo ""
    echo "建议："
    echo "1. 检查宿主机是否连接到目标网络"
    echo "2. 检查网络配置是否正确"
    echo "3. 尝试手动配置一个该网段的 IP 地址"
else
    echo "✓ 找到匹配的 IP："
    echo "$MATCHING_IPS"
    echo ""
    
    # 5. 测试每个匹配的源 IP
    echo "5. 测试每个源 IP："
    echo "-------------------"
    for SOURCE_IP in $MATCHING_IPS; do
        echo "测试源 IP: $SOURCE_IP"
        echo "命令: ping -I $SOURCE_IP -c 1 -W 2 $TARGET_IP"
        if ping -I $SOURCE_IP -c 1 -W 2 $TARGET_IP > /dev/null 2>&1; then
            echo "✓ 成功：使用源 IP $SOURCE_IP 可以 ping 通 $TARGET_IP"
            echo ""
            echo "========================================="
            echo "推荐配置："
            echo "========================================="
            echo "在 backend/.env 文件中添加："
            echo "PING_SOURCE_IP=$SOURCE_IP"
            echo ""
            echo "完整配置示例："
            echo "USE_PING_PROXY=true"
            echo "PING_PROXY_URL=http://host.docker.internal:8001"
            echo "PING_SOURCE_IP=$SOURCE_IP"
            echo "========================================="
            exit 0
        else
            echo "✗ 失败：使用源 IP $SOURCE_IP 无法 ping 通 $TARGET_IP"
        fi
        echo ""
    done
fi

# 6. 如果所有测试都失败
echo "========================================="
echo "诊断结果：无法 ping 通目标 IP"
echo "========================================="
echo ""
echo "可能的原因："
echo "1. 目标设备不在线或未响应 ICMP 请求"
echo "2. 防火墙阻止了 ICMP 请求"
echo "3. 网络配置错误"
echo "4. 宿主机未连接到目标网络"
echo ""
echo "建议："
echo "1. 检查目标设备是否在线"
echo "2. 检查防火墙规则（iptables -L）"
echo "3. 检查网络连接和路由配置"
echo "4. 尝试从其他设备 ping 目标 IP"
echo ""
