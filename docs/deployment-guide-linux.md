# IT 智维平台 — Linux Ubuntu 部署指南

## 目录

1. [环境要求](#1-环境要求)
2. [服务器准备](#2-服务器准备)
3. [项目部署](#3-项目部署)
4. [生产环境配置](#4-生产环境配置)
5. [docker-compose 生产配置](#5-docker-compose-生产配置)
6. [Nginx 反向代理配置](#6-nginx-反向代理配置)
7. [Ping 代理服务配置](#7-ping-代理服务配置)
8. [启动与验证](#8-启动与验证)
9. [数据备份与恢复](#9-数据备份与恢复)
10. [日志管理](#10-日志管理)
11. [监控与告警](#11-监控与告警)
12. [常见问题排查](#12-常见问题排查)
13. [安全加固](#13-安全加固)

---

## 1. 环境要求

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 40 GB | 100 GB+ SSD |
| 网络 | 能访问被管理网段 | 多网卡（管理网+业务网） |

### 软件要求

| 软件 | 版本 |
|------|------|
| Ubuntu | 22.04 LTS / 24.04 LTS |
| Docker | 24.0+ |
| Docker Compose | v2.20+ |
| Git | 2.x |

### 端口规划

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | HTTP 入口 |
| 443 | Nginx | HTTPS 入口（可选） |
| 8000 | Backend API | FastAPI（仅内部访问） |
| 3306 | MySQL | 数据库（仅内部访问） |
| 6379 | Redis | 缓存（仅内部访问） |
| 5672 | RabbitMQ | 消息队列（仅内部访问） |
| 15672 | RabbitMQ | 管理界面 |
| 8001 | Ping Proxy | Ping 代理（宿主机） |
| 9000 | MinIO | 对象存储 API |
| 9001 | MinIO | 对象存储控制台 |
| 1812/udp | FreeRADIUS | RADIUS 认证 |
| 1813/udp | FreeRADIUS | RADIUS 计费 |

---

## 2. 服务器准备

### 2.1 系统更新

```bash
sudo apt update && sudo apt upgrade -y
sudo timedatectl set-timezone Asia/Shanghai
```

### 2.2 安装 Docker

```bash
# 安装依赖
sudo apt install -y ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
newgrp docker

# 验证
docker --version
docker compose version
```

> 如果服务器无法访问 Docker 官方源，可使用国内镜像：
</text>
</invoke>