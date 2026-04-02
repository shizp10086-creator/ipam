# IPAM 系统完整运维指南

## 📋 目录

1. [系统架构说明](#系统架构说明)
2. [首次启动](#首次启动)
3. [日常启动](#日常启动)
4. [停止服务](#停止服务)
5. [重启服务](#重启服务)
6. [服务状态检查](#服务状态检查)
7. [日常运维](#日常运维)
8. [故障排查](#故障排查)
9. [数据备份与恢复](#数据备份与恢复)
10. [性能监控](#性能监控)

---

## 系统架构说明

IPAM 系统采用前后端分离架构：

```
┌─────────────────────────────────────────┐
│         前端 (Vue 3 + Vite)             │
│      http://localhost:5173              │
└──────────────┬──────────────────────────┘
               │ HTTP API 调用
┌──────────────▼──────────────────────────┐
│      后端 (FastAPI + Python)            │
│      http://localhost:8000              │
└──────────────┬──────────────────────────┘
               │ SQL 查询
┌──────────────▼──────────────────────────┐
│    数据库 (MySQL 8.0 Docker)            │
│      localhost:3306                     │
└─────────────────────────────────────────┘
```

**运行模式**: 
- 本地开发模式（推荐用于开发和测试）
- Docker Compose 模式（推荐用于生产部署）

详细说明请参考: `部署模式说明.md` 和 `Docker部署说明.md`

---

## 首次启动

### 前置条件检查

在首次启动前，确保以下服务已安装并运行：

```powershell
# 检查 Python
python --version
# 应显示: Python 3.10.11

# 检查 Node.js
node --version
# 应显示: v24.x.x

# 检查 Docker
docker --version
# 应显示: Docker version 29.x.x

# 检查 MySQL 容器
docker ps | findstr mysql
# 应显示 mysql8.0 容器正在运行
```

### 启动步骤

#### 1. 启动 MySQL 数据库（如果未运行）

```powershell
docker start mysql8.0
```

#### 2. 启动后端服务

**方式 A：使用启动脚本（推荐）**
```powershell
# 双击运行或在命令行执行
START_BACKEND.bat
```

**方式 B：手动启动**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**启动成功标志**：
- 看到 `Application startup complete`
- 看到 `Uvicorn running on http://0.0.0.0:8000`
- 首次启动会自动创建数据表和默认管理员账户

#### 3. 启动前端服务（新开终端窗口）

**方式 A：使用启动脚本（推荐）**
```powershell
# 双击运行或在命令行执行
START_FRONTEND.bat
```

**方式 B：手动启动**
```powershell
cd frontend
npm run dev
```

**启动成功标志**：
- 看到 `Local: http://localhost:5173`
- 看到 `ready in xxx ms`

---

## 日常启动

日常启动顺序：**数据库 → 后端 → 前端**

### 快速启动流程

1. **检查 MySQL 是否运行**
   ```powershell
   docker ps | findstr mysql
   ```
   如果没有运行：
   ```powershell
   docker start mysql8.0
   ```

2. **启动后端**
   ```powershell
   # 双击运行
   START_BACKEND.bat
   ```

3. **启动前端**（新终端）
   ```powershell
   # 双击运行
   START_FRONTEND.bat
   ```

### 验证启动成功

访问以下地址确认服务正常：

- ✅ 后端健康检查: http://localhost:8000/health
- ✅ API 文档: http://localhost:8000/api/docs
- ✅ 前端界面: http://localhost:5173

---

## 停止服务

### 停止前端服务

1. 找到运行前端的终端窗口
2. 按 `Ctrl + C`
3. 如果提示 "终止批处理操作吗(Y/N)?"，输入 `Y` 并回车

### 停止后端服务

1. 找到运行后端的终端窗口
2. 按 `Ctrl + C`
3. 如果提示 "终止批处理操作吗(Y/N)?"，输入 `Y` 并回车

### 停止 MySQL 数据库（可选）

```powershell
docker stop mysql8.0
```

**注意**: 通常不需要停止 MySQL，让它保持运行即可。

### 强制停止（紧急情况）

如果服务无法正常停止，可以强制结束进程：

```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000    # 后端
netstat -ano | findstr :5173    # 前端

# 强制结束进程（替换 <PID> 为实际进程ID）
taskkill /PID <PID> /F
```

---

## 重启服务

### 重启后端

1. 在后端终端按 `Ctrl + C` 停止
2. 重新运行 `START_BACKEND.bat`

### 重启前端

1. 在前端终端按 `Ctrl + C` 停止
2. 重新运行 `START_FRONTEND.bat`

### 重启 MySQL

```powershell
docker restart mysql8.0
```

### 完全重启系统

```powershell
# 1. 停止所有服务（在各终端按 Ctrl+C）
# 2. 重启 MySQL
docker restart mysql8.0

# 3. 等待 10 秒让 MySQL 完全启动
timeout /t 10

# 4. 启动后端
START_BACKEND.bat

# 5. 启动前端（新终端）
START_FRONTEND.bat
```

---

## 服务状态检查

### 检查所有服务状态

```powershell
# 检查 MySQL
docker ps | findstr mysql

# 检查后端（访问健康检查接口）
curl http://localhost:8000/health

# 检查前端（访问首页）
curl http://localhost:5173
```

### 查看服务日志

**后端日志**：
- 实时日志：在后端终端窗口查看
- 日志文件：`backend/logs/` 目录

**前端日志**：
- 实时日志：在前端终端窗口查看
- 浏览器控制台：F12 打开开发者工具

**MySQL 日志**：
```powershell
docker logs mysql8.0
# 查看最近 100 行
docker logs --tail 100 mysql8.0
# 实时查看
docker logs -f mysql8.0
```

### 检查端口占用

```powershell
# 检查所有相关端口
netstat -ano | findstr "3306 8000 5173"
```

---

## 日常运维

### 每日检查清单

- [ ] MySQL 容器运行正常
- [ ] 后端服务响应正常
- [ ] 前端界面可访问
- [ ] 数据库连接正常
- [ ] 磁盘空间充足

### 每周维护任务

#### 1. 数据库备份

```powershell
# 创建备份目录
mkdir backups

# 备份数据库
docker exec mysql8.0 mysqldump -uroot -pputailai123 ipam_db > backups\ipam_db_backup_%date:~0,4%%date:~5,2%%date:~8,2%.sql
```

#### 2. 清理日志文件

```powershell
# 清理 30 天前的日志
forfiles /p "backend\logs" /s /m *.log /d -30 /c "cmd /c del @path"
```

#### 3. 检查磁盘空间

```powershell
# 查看磁盘使用情况
wmic logicaldisk get name,size,freespace
```

### 每月维护任务

#### 1. 更新依赖包

**后端依赖**：
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip list --outdated
# 谨慎更新，先在测试环境验证
pip install --upgrade <package_name>
```

**前端依赖**：
```powershell
cd frontend
npm outdated
# 谨慎更新，先在测试环境验证
npm update
```

#### 2. 数据库优化

```powershell
# 连接到 MySQL
docker exec -it mysql8.0 mysql -uroot -pputailai123 ipam_db

# 在 MySQL 中执行
OPTIMIZE TABLE users;
OPTIMIZE TABLE network_segments;
OPTIMIZE TABLE ip_addresses;
OPTIMIZE TABLE devices;
OPTIMIZE TABLE operation_logs;
```

#### 3. 检查数据库大小

```powershell
docker exec mysql8.0 mysql -uroot -pputailai123 -e "SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)' FROM information_schema.tables WHERE table_schema = 'ipam_db' GROUP BY table_schema;"
```

---

## 故障排查

### 问题 1: 后端无法启动 - 数据库连接失败

**症状**：
```
ERROR - Database connection failed
ERROR - Cannot connect to database
```

**解决方案**：
```powershell
# 1. 检查 MySQL 是否运行
docker ps | findstr mysql

# 2. 如果未运行，启动 MySQL
docker start mysql8.0

# 3. 等待 10 秒让 MySQL 完全启动
timeout /t 10

# 4. 测试数据库连接
docker exec mysql8.0 mysql -uroot -pputailai123 -e "SELECT 1"

# 5. 重新启动后端
START_BACKEND.bat
```

### 问题 2: 端口被占用

**症状**：
```
Address already in use
Port 8000 is already in use
```

**解决方案**：
```powershell
# 1. 查找占用端口的进程
netstat -ano | findstr :8000

# 2. 记下 PID（最后一列数字）

# 3. 结束进程
taskkill /PID <PID> /F

# 4. 重新启动服务
```

### 问题 3: 前端无法连接后端

**症状**：
- 前端页面显示网络错误
- API 请求失败

**解决方案**：
```powershell
# 1. 确认后端正在运行
curl http://localhost:8000/health

# 2. 检查 CORS 配置
# 编辑 backend/.env，确保包含：
# BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# 3. 重启后端服务

# 4. 清除浏览器缓存并刷新前端
```

### 问题 4: MySQL 容器无法启动

**症状**：
```
Error starting container
```

**解决方案**：
```powershell
# 1. 查看容器日志
docker logs mysql8.0

# 2. 如果数据损坏，停止并删除容器
docker stop mysql8.0
docker rm mysql8.0

# 3. 重新创建容器（注意：会丢失数据）
docker run -d --name mysql8.0 -e MYSQL_ROOT_PASSWORD=putailai123 -e MYSQL_DATABASE=ipam_db -p 3306:3306 -v D:/mysql-data:/var/lib/mysql mysql:8.0

# 4. 等待启动完成
timeout /t 20

# 5. 重新初始化数据库
cd backend
.\venv\Scripts\python.exe app/utils/db_init.py
```

### 问题 5: 虚拟环境损坏

**症状**：
```
ModuleNotFoundError
ImportError
```

**解决方案**：
```powershell
# 1. 删除虚拟环境
cd backend
rmdir /s /q venv

# 2. 重新创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 4. 重新安装依赖
pip install -r requirements.txt

# 5. 重新启动后端
```

---

## 数据备份与恢复

### 完整备份

```powershell
# 创建备份目录
mkdir backups\%date:~0,4%%date:~5,2%%date:~8,2%

# 备份数据库
docker exec mysql8.0 mysqldump -uroot -pputailai123 --single-transaction --routines --triggers ipam_db > backups\%date:~0,4%%date:~5,2%%date:~8,2%\ipam_db.sql

# 备份配置文件
copy backend\.env backups\%date:~0,4%%date:~5,2%%date:~8,2%\.env.backup
copy frontend\.env backups\%date:~0,4%%date:~5,2%%date:~8,2%\frontend.env.backup
```

### 恢复数据库

```powershell
# 停止后端服务（Ctrl+C）

# 恢复数据库
docker exec -i mysql8.0 mysql -uroot -pputailai123 ipam_db < backups\20260207\ipam_db.sql

# 重新启动后端
START_BACKEND.bat
```

### 自动备份脚本

创建 `BACKUP.bat`：

```batch
@echo off
set BACKUP_DIR=backups\%date:~0,4%%date:~5,2%%date:~8,2%
mkdir %BACKUP_DIR%

echo 正在备份数据库...
docker exec mysql8.0 mysqldump -uroot -pputailai123 --single-transaction ipam_db > %BACKUP_DIR%\ipam_db.sql

echo 正在备份配置文件...
copy backend\.env %BACKUP_DIR%\.env.backup
copy frontend\.env %BACKUP_DIR%\frontend.env.backup

echo 备份完成！保存在: %BACKUP_DIR%
pause
```

---

## 性能监控

### 监控后端性能

```powershell
# 查看后端进程资源使用
tasklist /FI "IMAGENAME eq python.exe" /V

# 访问性能指标（如果已配置）
curl http://localhost:8000/metrics
```

### 监控数据库性能

```powershell
# 连接到 MySQL
docker exec -it mysql8.0 mysql -uroot -pputailai123

# 查看当前连接
SHOW PROCESSLIST;

# 查看慢查询
SHOW VARIABLES LIKE 'slow_query%';

# 查看表状态
USE ipam_db;
SHOW TABLE STATUS;
```

### 监控 Docker 容器

```powershell
# 查看容器资源使用
docker stats mysql8.0

# 查看容器详细信息
docker inspect mysql8.0
```

---

## 访问地址

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs
- **健康检查**: http://localhost:8000/health

## 默认管理员账户

- 用户名: `admin`
- 密码: `admin123`
- **⚠️ 重要**: 首次登录后请立即修改密码！

## 数据库信息

- 主机: `localhost`
- 端口: `3306`
- 用户: `root`
- 密码: `putailai123`
- 数据库: `ipam_db`

---

## 快速参考

### 常用命令速查

```powershell
# 启动服务
START_BACKEND.bat          # 启动后端
START_FRONTEND.bat         # 启动前端

# 停止服务
Ctrl + C                   # 在终端中停止服务

# 检查状态
docker ps                  # 查看 Docker 容器
netstat -ano | findstr :8000  # 检查后端端口
netstat -ano | findstr :5173  # 检查前端端口

# 数据库操作
docker start mysql8.0      # 启动 MySQL
docker stop mysql8.0       # 停止 MySQL
docker restart mysql8.0    # 重启 MySQL
docker logs mysql8.0       # 查看 MySQL 日志

# 备份
docker exec mysql8.0 mysqldump -uroot -pputailai123 ipam_db > backup.sql
```

---

## 技术支持

如遇到问题：

1. 查看本文档的故障排查章节
2. 检查服务日志文件
3. 查看 `DEVELOPMENT.md` 了解开发细节
4. 查看 `ENVIRONMENT_SETUP.md` 了解环境配置

---

**文档版本**: 1.0  
**最后更新**: 2026-02-07  
**维护者**: IPAM 开发团队

祝使用愉快！🎉
