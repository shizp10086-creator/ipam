# IPAM 系统 Docker Compose 部署说明

## 📋 当前状态

- ✅ Docker 镜像加速器已配置（使用可用的国内镜像源）
- ✅ `backend/.env` 已更新为 Docker Compose 模式
- ✅ 独立 MySQL 容器已停止
- ⏳ 等待重启 Docker Desktop 并启动服务

## 🔧 已配置的镜像源

根据测试，以下镜像源可用：
- `https://docker.1panel.live` ✅ 可用
- `https://dockerproxy.cn`
- `https://docker.chenby.cn`

配置文件位置: `C:\Users\admin\.docker\daemon.json`

## 📝 下一步操作

### 方式 A: 使用自动部署脚本（推荐）

1. **运行部署脚本**
   ```
   完整Docker部署.bat
   ```

2. **按照提示操作**
   - 脚本会自动更新 Docker 配置
   - 提示你手动重启 Docker Desktop
   - 等待 Docker 启动后自动启动服务

### 方式 B: 手动部署

1. **重启 Docker Desktop**
   - 右键点击任务栏的 Docker 图标
   - 选择 "Restart Docker Desktop"
   - 等待 Docker 完全启动（约 30-60 秒）

2. **验证 Docker 状态**
   ```powershell
   docker info
   ```

3. **启动 Docker Compose**
   ```powershell
   docker compose up -d --build
   ```

4. **等待服务启动**（首次约 5-10 分钟）
   ```powershell
   # 查看启动进度
   docker compose logs -f
   ```

5. **验证服务状态**
   ```powershell
   docker compose ps
   ```

## 🌐 访问地址

启动成功后，访问以下地址：

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs
- **健康检查**: http://localhost:8000/health

## 👤 默认管理员账户

- 用户名: `admin`
- 密码: `admin123`

## 🐳 Docker Compose 服务说明

### MySQL 数据库
- 容器名: `ipam-mysql`
- 端口: `3306`
- 用户: `ipam`
- 密码: `ipam_password`
- 数据库: `ipam_db`

### 后端服务
- 容器名: `ipam-backend`
- 端口: `8000`
- 技术栈: FastAPI + Python 3.10

### 前端服务
- 容器名: `ipam-frontend`
- 端口: `5173`
- 技术栈: Vue 3 + Vite

## 📊 常用命令

### 查看服务状态
```powershell
docker compose ps
```

### 查看日志
```powershell
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql
```

### 重启服务
```powershell
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend
docker compose restart frontend
```

### 停止服务
```powershell
# 停止所有服务（保留数据）
docker compose down

# 停止并删除所有数据
docker compose down -v
```

### 重新构建并启动
```powershell
docker compose up -d --build
```

## 🔍 故障排查

### 问题 1: 镜像拉取失败

**症状**:
```
failed to resolve source metadata
encountered unknown type text/html
```

**解决方案**:
1. 确认 Docker Desktop 已重启
2. 验证镜像加速器配置: `C:\Users\admin\.docker\daemon.json`
3. 测试镜像源连接
4. 如果仍然失败，考虑使用本地开发模式

### 问题 2: 服务启动失败

**症状**:
```
docker compose ps
显示服务状态为 Exited 或 Restarting
```

**解决方案**:
```powershell
# 查看详细日志
docker compose logs backend
docker compose logs frontend
docker compose logs mysql

# 根据日志信息排查问题
```

### 问题 3: 端口被占用

**症状**:
```
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**解决方案**:
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 结束进程
taskkill /PID <PID> /F

# 重新启动服务
docker compose up -d
```

### 问题 4: 数据库连接失败

**症状**:
后端日志显示无法连接到 MySQL

**解决方案**:
```powershell
# 检查 MySQL 容器状态
docker compose ps mysql

# 查看 MySQL 日志
docker compose logs mysql

# 确认 backend/.env 配置正确
# MYSQL_HOST=mysql
# MYSQL_USER=ipam
# MYSQL_PASSWORD=ipam_password
```

## 🔄 切换回本地开发模式

如果 Docker Compose 部署遇到问题，可以切换回本地开发模式：

1. **停止 Docker Compose**
   ```powershell
   docker compose down
   ```

2. **启动独立 MySQL 容器**
   ```powershell
   docker start mysql8.0
   ```

3. **更新 backend/.env**
   ```env
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=putailai123
   ```

4. **启动服务**
   ```powershell
   START_BACKEND.bat
   START_FRONTEND.bat
   ```

## 📚 相关文档

- `IPAM系统完整运维指南.md` - 完整运维文档
- `Docker_Compose使用说明.md` - Docker Compose 详细说明
- `部署模式说明.md` - 本地开发模式 vs Docker Compose 模式对比

## ⚠️ 重要提示

1. **首次启动时间**: Docker Compose 首次启动需要下载镜像，可能需要 5-10 分钟
2. **网络要求**: 需要稳定的网络连接来下载 Docker 镜像
3. **资源要求**: Docker Desktop 需要足够的内存和磁盘空间
4. **数据持久化**: 数据存储在 Docker volumes 中，使用 `docker compose down -v` 会删除所有数据

---

**文档版本**: 1.0  
**最后更新**: 2026-02-07  
**维护者**: IPAM 开发团队
