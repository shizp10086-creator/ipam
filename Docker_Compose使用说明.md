# Docker Compose 使用说明

## 当前状态

由于网络连接 Docker Hub 不稳定，系统目前使用**本地开发模式**运行。

## Docker Hub 连接问题

### 问题表现
```
failed to fetch oauth token: Post "https://auth.docker.io/token"
dial tcp 157.240.17.36:443: connectex: A connection attempt failed
```

### 原因分析
- Docker Hub 服务器连接超时
- 可能是网络防火墙或代理问题
- 可能是 DNS 解析问题

---

## 解决方案

### 方案 1: 配置 Docker 镜像加速器（推荐）

#### 1.1 使用阿里云镜像加速

1. 打开 Docker Desktop
2. 点击右上角设置图标 ⚙️
3. 选择 "Docker Engine"
4. 在 JSON 配置中添加：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

5. 点击 "Apply & Restart"
6. 等待 Docker 重启完成

#### 1.2 验证配置

```powershell
docker info | findstr "Registry Mirrors"
```

应该显示配置的镜像地址。

### 方案 2: 配置代理

如果你有 HTTP 代理，可以配置 Docker 使用代理：

1. 打开 Docker Desktop 设置
2. 选择 "Resources" → "Proxies"
3. 启用 "Manual proxy configuration"
4. 输入代理地址，例如：
   - HTTP Proxy: `http://proxy.example.com:8080`
   - HTTPS Proxy: `http://proxy.example.com:8080`
5. 点击 "Apply & Restart"

### 方案 3: 使用本地镜像（当前方案）

继续使用本地开发模式，不依赖 Docker Compose。

---

## 使用 Docker Compose（网络正常后）

### 前置准备

1. **停止本地开发模式的服务**
   ```powershell
   # 停止后端和前端（在各终端按 Ctrl+C）
   # 或运行
   STOP_ALL.bat
   ```

2. **停止独立的 MySQL 容器**
   ```powershell
   docker stop mysql8.0
   ```

3. **更新后端配置**
   
   编辑 `backend/.env`，修改数据库配置：
   ```env
   MYSQL_HOST=mysql          # 改为 mysql（Docker Compose 服务名）
   MYSQL_USER=ipam           # 改为 ipam
   MYSQL_PASSWORD=ipam_password  # 改为 ipam_password
   ```

### 启动 Docker Compose

```powershell
# 构建并启动所有服务
docker compose up -d --build

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql
```

### 停止 Docker Compose

```powershell
# 停止所有服务
docker compose down

# 停止并删除数据卷（⚠️ 会删除数据库数据）
docker compose down -v
```

### 重启服务

```powershell
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend
docker compose restart frontend
docker compose restart mysql
```

---

## Docker Compose vs 本地开发模式对比

| 特性 | Docker Compose | 本地开发模式 |
|------|----------------|--------------|
| 启动速度 | 较慢（需要构建镜像） | 快速 |
| 资源占用 | 较高 | 较低 |
| 环境隔离 | 完全隔离 | 依赖本地环境 |
| 热重载 | 支持（通过卷挂载） | 支持 |
| 生产环境 | 推荐 | 不推荐 |
| 开发调试 | 较复杂 | 简单 |
| 网络依赖 | 首次需要下载镜像 | 无 |

---

## 当前推荐方案

### 开发阶段（当前）
✅ **使用本地开发模式**
- 启动快速
- 调试方便
- 不依赖网络

启动方式：
```powershell
START_BACKEND.bat
START_FRONTEND.bat
```

### 生产部署（未来）
✅ **使用 Docker Compose**
- 环境一致性
- 易于部署
- 易于扩展

前提条件：
1. 配置好 Docker 镜像加速器
2. 或在有稳定网络的服务器上部署

---

## 故障排查

### 问题 1: Docker Compose 构建失败

**症状**：
```
failed to fetch oauth token
failed to authorize
```

**解决**：
1. 配置镜像加速器（见方案 1）
2. 检查网络连接
3. 检查 Docker Desktop 是否正常运行
4. 尝试重启 Docker Desktop

### 问题 2: 容器无法启动

**症状**：
```
docker compose ps
# 显示容器状态为 Exited
```

**解决**：
```powershell
# 查看容器日志
docker compose logs <service_name>

# 常见问题：
# - 端口被占用：停止占用端口的程序
# - 配置错误：检查 .env 文件
# - 数据库连接失败：检查 MySQL 容器是否正常
```

### 问题 3: 数据库数据丢失

**症状**：
重启后数据消失

**原因**：
使用了 `docker compose down -v` 删除了数据卷

**解决**：
1. 定期备份数据（使用 BACKUP.bat）
2. 停止服务时使用 `docker compose down`（不加 -v）
3. 从备份恢复数据

---

## 迁移到 Docker Compose

当网络稳定后，可以按以下步骤迁移：

### 步骤 1: 备份数据

```powershell
BACKUP.bat
```

### 步骤 2: 停止本地服务

```powershell
STOP_ALL.bat
docker stop mysql8.0
```

### 步骤 3: 更新配置

编辑 `backend/.env`：
```env
MYSQL_HOST=mysql
MYSQL_USER=ipam
MYSQL_PASSWORD=ipam_password
```

### 步骤 4: 启动 Docker Compose

```powershell
docker compose up -d --build
```

### 步骤 5: 恢复数据（如需要）

```powershell
# 等待 MySQL 启动完成
timeout /t 20

# 恢复数据
docker compose exec -T mysql mysql -uipam -pipam_password ipam_db < backups\<backup_folder>\ipam_db.sql
```

### 步骤 6: 验证

访问：
- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/api/docs

---

## 创建启动脚本（Docker Compose 版本）

创建 `START_DOCKER.bat`：

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo 启动 IPAM 系统 (Docker Compose)
echo ========================================
echo.

echo 🚀 正在启动所有服务...
docker compose up -d

echo.
echo ⏳ 等待服务启动...
timeout /t 10 >nul

echo.
echo 📊 服务状态:
docker compose ps

echo.
echo ========================================
echo 启动完成！
echo ========================================
echo.
echo 访问地址:
echo - 前端: http://localhost:5173
echo - 后端: http://localhost:8000
echo - API 文档: http://localhost:8000/api/docs
echo.
echo 查看日志: docker compose logs -f
echo 停止服务: docker compose down
echo.
pause
```

---

## 总结

**当前状态**: 使用本地开发模式 ✅

**未来计划**: 
1. 配置 Docker 镜像加速器
2. 测试 Docker Compose 启动
3. 迁移到 Docker Compose（可选）

**建议**: 
- 开发阶段继续使用本地模式
- 生产部署时使用 Docker Compose
- 定期备份数据

---

**文档版本**: 1.0  
**最后更新**: 2026-02-07
