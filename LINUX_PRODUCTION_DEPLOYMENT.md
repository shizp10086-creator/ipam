# IPAM 系统 - Linux 生产环境部署指南

## 系统要求

### 硬件要求
- **CPU**: 2 核心或以上
- **内存**: 4GB 或以上（推荐 8GB）
- **磁盘**: 20GB 或以上可用空间
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: 
  - Ubuntu 20.04/22.04 LTS（推荐）
  - CentOS 7/8 / Rocky Linux 8/9
  - Debian 10/11
  - Red Hat Enterprise Linux 8/9
- **Docker**: 20.10 或以上
- **Docker Compose**: 2.0 或以上
- **Python**: 3.8 或以上（用于 Ping 代理服务）

## 快速部署（推荐）

### 1. 安装 Docker 和 Docker Compose

#### Ubuntu/Debian
```bash
# 更新包索引
sudo apt update

# 安装依赖
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

#### CentOS/RHEL/Rocky Linux
```bash
# 安装依赖
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

### 2. 克隆项目

```bash
# 克隆项目到服务器
cd /opt
sudo git clone <repository-url> ipam-system
cd ipam-system

# 设置权限
sudo chown -R $USER:$USER /opt/ipam-system
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑配置文件
nano backend/.env
```

**关键配置项**：
```bash
# 数据库配置（生产环境建议修改密码）
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=ipam
MYSQL_PASSWORD=your_secure_password_here  # ⚠️ 修改为强密码
MYSQL_DATABASE=ipam_db

# JWT 配置（生产环境必须修改）
SECRET_KEY=your_secret_key_here  # ⚠️ 使用 openssl rand -hex 32 生成
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置（根据实际域名修改）
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://your-domain.com"]

# Ping 代理配置
USE_PING_PROXY=true
PING_PROXY_URL=http://172.17.0.1:8001  # Linux Docker 网桥 IP
PING_SOURCE_IP=  # 根据实际网络配置

# 日志级别
LOG_LEVEL=INFO  # 生产环境使用 INFO
```

**生成安全密钥**：
```bash
# 生成 JWT 密钥
openssl rand -hex 32

# 生成数据库密码
openssl rand -base64 32
```

### 4. 配置 Docker Compose（生产环境优化）

编辑 `docker-compose.yml`，更新数据库密码：

```bash
nano docker-compose.yml
```

修改 MySQL 密码：
```yaml
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: your_root_password_here  # 修改
      MYSQL_PASSWORD: your_secure_password_here     # 与 .env 一致
```

### 5. 部署 Ping 代理服务（Systemd）

#### 安装 Python 依赖
```bash
# 安装 Python 3 和 pip
sudo apt install -y python3 python3-pip  # Ubuntu/Debian
# 或
sudo yum install -y python3 python3-pip  # CentOS/RHEL

# 安装 Ping 代理依赖
cd /opt/ipam-system/ping-proxy
sudo pip3 install -r requirements.txt
```

#### 创建 Systemd 服务
```bash
# 创建服务文件
sudo nano /etc/systemd/system/ipam-ping-proxy.service
```

**服务配置内容**：
```ini
[Unit]
Description=IPAM Ping Proxy Service
After=network.target
Documentation=https://github.com/your-repo/ipam-system

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ipam-system/ping-proxy
ExecStart=/usr/bin/python3 /opt/ipam-system/ping-proxy/ping_proxy.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 安全配置
NoNewPrivileges=true
PrivateTmp=true

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

#### 启动服务
```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ipam-ping-proxy

# 设置开机自启
sudo systemctl enable ipam-ping-proxy

# 检查状态
sudo systemctl status ipam-ping-proxy

# 查看日志
sudo journalctl -u ipam-ping-proxy -f
```

### 6. 配置防火墙

#### UFW (Ubuntu/Debian)
```bash
# 启用防火墙
sudo ufw enable

# 允许 SSH（重要！）
sudo ufw allow 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许 IPAM 服务端口
sudo ufw allow 8000/tcp  # 后端 API
sudo ufw allow 5173/tcp  # 前端（开发）或 80（生产）
sudo ufw allow 8001/tcp  # Ping 代理（仅本地访问）

# 限制 Ping 代理只能本地访问
sudo ufw deny from any to any port 8001
sudo ufw allow from 172.17.0.0/16 to any port 8001  # Docker 网络

# 查看规则
sudo ufw status numbered
```

#### Firewalld (CentOS/RHEL)
```bash
# 启动防火墙
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 允许服务
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5173/tcp
sudo firewall-cmd --permanent --add-port=8001/tcp

# 限制 Ping 代理访问
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="172.17.0.0/16" port port="8001" protocol="tcp" accept'

# 重新加载
sudo firewall-cmd --reload

# 查看规则
sudo firewall-cmd --list-all
```

### 7. 启动 IPAM 系统

```bash
# 进入项目目录
cd /opt/ipam-system

# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 等待服务启动（约 30 秒）
sleep 30

# 检查健康状态
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### 8. 验证部署

```bash
# 检查所有容器是否运行
docker compose ps

# 预期输出：
# NAME              STATUS          PORTS
# ipam-mysql        Up (healthy)    0.0.0.0:3306->3306/tcp
# ipam-backend      Up (healthy)    0.0.0.0:8000->8000/tcp
# ipam-frontend     Up              0.0.0.0:5173->5173/tcp

# 测试后端 API
curl http://localhost:8000/api/docs

# 测试 Ping 代理
curl -X POST http://localhost:8001/ping \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "8.8.8.8", "timeout": 2}'
```

### 9. 访问系统

- **前端界面**: http://your-server-ip:5173
- **后端 API 文档**: http://your-server-ip:8000/api/docs
- **默认管理员账户**:
  - 用户名: `admin`
  - 密码: `admin123`
  - ⚠️ **首次登录后立即修改密码！**

## 生产环境优化

### 1. 使用 Nginx 反向代理（推荐）

#### 安装 Nginx
```bash
sudo apt install -y nginx  # Ubuntu/Debian
# 或
sudo yum install -y nginx  # CentOS/RHEL
```

#### 配置 Nginx
```bash
sudo nano /etc/nginx/sites-available/ipam
```

**Nginx 配置**：
```nginx
# 前端服务
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API 文档
    location /api/docs {
        proxy_pass http://localhost:8000/api/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # 日志
    access_log /var/log/nginx/ipam_access.log;
    error_log /var/log/nginx/ipam_error.log;
}
```

#### 启用配置
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/ipam /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 2. 配置 HTTPS（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx  # Ubuntu/Debian
# 或
sudo yum install -y certbot python3-certbot-nginx  # CentOS/RHEL

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 数据库备份自动化

#### 创建备份脚本
```bash
sudo nano /opt/ipam-system/scripts/backup-database.sh
```

**备份脚本内容**：
```bash
#!/bin/bash

# 配置
BACKUP_DIR="/opt/ipam-backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="ipam_backup_${DATE}.sql"
RETENTION_DAYS=7

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec ipam-mysql mysqldump -u ipam -pipam_password ipam_db > $BACKUP_DIR/$BACKUP_FILE

# 压缩备份
gzip $BACKUP_DIR/$BACKUP_FILE

# 删除旧备份
find $BACKUP_DIR -name "ipam_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

#### 设置权限和定时任务
```bash
# 设置执行权限
sudo chmod +x /opt/ipam-system/scripts/backup-database.sh

# 添加到 crontab（每天凌晨 2 点备份）
sudo crontab -e

# 添加以下行：
0 2 * * * /opt/ipam-system/scripts/backup-database.sh >> /var/log/ipam-backup.log 2>&1
```

### 4. 日志轮转配置

```bash
sudo nano /etc/logrotate.d/ipam
```

**日志轮转配置**：
```
/opt/ipam-system/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker compose -f /opt/ipam-system/docker-compose.yml restart backend
    endscript
}
```

### 5. 系统监控

#### 安装监控工具
```bash
# 安装 htop 和 netstat
sudo apt install -y htop net-tools  # Ubuntu/Debian
# 或
sudo yum install -y htop net-tools  # CentOS/RHEL
```

#### 监控脚本
```bash
# 创建监控脚本
sudo nano /opt/ipam-system/scripts/monitor.sh
```

**监控脚本内容**：
```bash
#!/bin/bash

echo "=== IPAM System Status ==="
echo ""

echo "Docker Containers:"
docker compose -f /opt/ipam-system/docker-compose.yml ps
echo ""

echo "Ping Proxy Service:"
systemctl status ipam-ping-proxy --no-pager
echo ""

echo "Disk Usage:"
df -h | grep -E '(Filesystem|/opt|/var)'
echo ""

echo "Memory Usage:"
free -h
echo ""

echo "Docker Stats:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

```bash
# 设置执行权限
sudo chmod +x /opt/ipam-system/scripts/monitor.sh

# 运行监控
/opt/ipam-system/scripts/monitor.sh
```

## 常用运维命令

### 服务管理
```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f
docker compose logs -f backend
docker compose logs -f mysql

# 查看 Ping 代理日志
sudo journalctl -u ipam-ping-proxy -f
```

### 数据库管理
```bash
# 进入 MySQL 容器
docker exec -it ipam-mysql mysql -u ipam -pipam_password ipam_db

# 备份数据库
docker exec ipam-mysql mysqldump -u ipam -pipam_password ipam_db > backup.sql

# 恢复数据库
docker exec -i ipam-mysql mysql -u ipam -pipam_password ipam_db < backup.sql
```

### 更新系统
```bash
# 拉取最新代码
cd /opt/ipam-system
git pull

# 重新构建镜像
docker compose build

# 重启服务
docker compose down
docker compose up -d
```

### 清理资源
```bash
# 清理未使用的 Docker 资源
docker system prune -a

# 清理日志
docker compose logs --tail=0 -f > /dev/null
```

## 故障排查

### 1. 容器无法启动
```bash
# 查看详细日志
docker compose logs backend
docker compose logs mysql

# 检查端口占用
sudo netstat -tulpn | grep -E '(3306|8000|5173|8001)'

# 检查磁盘空间
df -h
```

### 2. 数据库连接失败
```bash
# 检查 MySQL 容器状态
docker compose ps mysql

# 测试数据库连接
docker exec ipam-mysql mysql -u ipam -pipam_password -e "SELECT 1"

# 检查网络
docker network ls
docker network inspect ipam-system_ipam-network
```

### 3. Ping 扫描不工作
```bash
# 检查 Ping 代理服务
sudo systemctl status ipam-ping-proxy

# 测试 Ping 代理
curl -X POST http://localhost:8001/ping \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "8.8.8.8", "timeout": 2}'

# 检查网络配置
ip addr show
ip route show
```

### 4. 性能问题
```bash
# 查看资源使用
docker stats

# 查看系统负载
htop

# 查看磁盘 I/O
iostat -x 1

# 查看网络连接
netstat -an | grep ESTABLISHED | wc -l
```

## 安全加固

### 1. 限制 SSH 访问
```bash
# 编辑 SSH 配置
sudo nano /etc/ssh/sshd_config

# 修改以下配置：
PermitRootLogin no
PasswordAuthentication no  # 使用密钥认证
Port 2222  # 修改默认端口

# 重启 SSH
sudo systemctl restart sshd
```

### 2. 配置 fail2ban
```bash
# 安装 fail2ban
sudo apt install -y fail2ban

# 配置
sudo nano /etc/fail2ban/jail.local

# 添加：
[sshd]
enabled = true
port = 2222
maxretry = 3
bantime = 3600

# 启动服务
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### 3. 定期更新系统
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y

# 自动安全更新（Ubuntu）
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 性能调优

### 1. Docker 配置优化
```bash
# 编辑 Docker daemon 配置
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  }
}
```

```bash
# 重启 Docker
sudo systemctl restart docker
```

### 2. MySQL 优化
在 `docker-compose.yml` 中添加 MySQL 配置：

```yaml
mysql:
  command: 
    - --max_connections=200
    - --innodb_buffer_pool_size=512M
    - --query_cache_size=32M
```

### 3. 系统参数优化
```bash
# 编辑系统参数
sudo nano /etc/sysctl.conf

# 添加：
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.ip_local_port_range = 10000 65000
fs.file-max = 65536

# 应用配置
sudo sysctl -p
```

## 总结

IPAM 系统在 Linux 生产环境部署具有以下优势：

✅ **稳定性高**：Docker 原生支持，长期运行稳定
✅ **性能优**：网络和 I/O 性能最佳
✅ **易管理**：Systemd 服务管理，日志集中
✅ **安全性好**：防火墙、权限管理完善
✅ **可扩展**：支持负载均衡、集群部署

建议的生产环境配置：
- **操作系统**: Ubuntu 22.04 LTS
- **硬件**: 4 核 CPU + 8GB 内存 + 50GB SSD
- **网络**: 千兆网卡
- **备份**: 每日自动备份 + 异地备份
- **监控**: 配置监控告警系统

如有问题，请参考故障排查章节或联系技术支持。
