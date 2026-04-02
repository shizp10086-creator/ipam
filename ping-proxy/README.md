# Ping 代理服务

## 功能说明

这是一个轻量级的 HTTP 代理服务，运行在宿主机上，为容器化的后端提供 ping 功能。

## 为什么需要这个服务？

在生产环境中，后端服务通常运行在容器或独立服务器上，由于网络隔离，无法直接访问目标网络。Ping 代理服务解决了这个问题：

- 运行在宿主机上，可以访问所有网络
- 提供 HTTP API，容器可以通过网络调用
- 支持单个和批量 ping 请求
- 支持并发控制

## 安装

```bash
cd ping-proxy
pip install -r requirements.txt
```

## 运行

```bash
python ping_proxy.py
```

服务将在 `http://0.0.0.0:8001` 上运行。

## API 文档

### 1. Ping 单个 IP

**请求**：
```http
POST /ping
Content-Type: application/json

{
  "ip_address": "172.18.201.56",
  "timeout": 2,
  "count": 1
}
```

**响应**：
```json
{
  "ip_address": "172.18.201.56",
  "is_online": true,
  "output": "...",
  "error": null
}
```

### 2. Ping 批量 IP

**请求**：
```http
POST /ping/batch
Content-Type: application/json

{
  "ip_addresses": ["172.18.201.1", "172.18.201.2", "172.18.201.56"],
  "timeout": 2,
  "count": 1,
  "max_concurrent": 50
}
```

**响应**：
```json
{
  "results": [
    {
      "ip_address": "172.18.201.1",
      "is_online": false,
      "error": "Timeout"
    },
    {
      "ip_address": "172.18.201.56",
      "is_online": true,
      "output": "..."
    }
  ],
  "total": 3,
  "online": 1
}
```

### 3. 健康检查

**请求**：
```http
GET /health
```

**响应**：
```json
{
  "status": "healthy"
}
```

## 部署建议

### 开发环境

直接运行 Python 脚本：
```bash
python ping_proxy.py
```

### 生产环境

使用 systemd 服务：

1. 创建服务文件 `/etc/systemd/system/ping-proxy.service`：
```ini
[Unit]
Description=Ping Proxy Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ping-proxy
ExecStart=/usr/bin/python3 /opt/ping-proxy/ping_proxy.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. 启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable ping-proxy
sudo systemctl start ping-proxy
```

### Docker 部署

如果需要在 Docker 中运行（使用 host 网络）：

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ping_proxy.py .
CMD ["python", "ping_proxy.py"]
```

```bash
docker build -t ping-proxy .
docker run -d --name ping-proxy --network host ping-proxy
```

## 安全建议

1. **访问控制**：添加 API 密钥认证
2. **IP 白名单**：限制可以 ping 的 IP 范围
3. **速率限制**：防止滥用
4. **日志记录**：记录所有 ping 请求

## 性能

- 支持高并发（默认 50 个并发 ping）
- 异步 I/O，不阻塞
- 轻量级，资源占用少
