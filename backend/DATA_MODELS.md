# IPAM System - Data Models Documentation

## Overview

This document describes the database models for the IPAM (IP Address Management) System. The system uses SQLAlchemy ORM with MySQL 8.0 as the database backend.

## Models Summary

The system consists of 7 core models:

1. **User** - 用户表：存储系统用户信息
2. **NetworkSegment** - 网段表：存储网络段信息
3. **IPAddress** - IP 地址表：存储 IP 地址及其状态
4. **Device** - 设备表：存储网络设备信息
5. **OperationLog** - 操作日志表：记录所有关键操作
6. **Alert** - 告警表：存储系统告警信息
7. **ScanHistory** - 扫描历史表：记录 IP 扫描历史

## Model Details

### 1. User Model (用户表)

**Table Name:** `users`

**Purpose:** 存储系统用户信息，包括认证和授权相关数据

**Columns:**
- `id` (Integer, PK): 主键
- `username` (String(50), Unique, Indexed): 用户名
- `hashed_password` (String(255)): 加密密码
- `email` (String(100)): 邮箱
- `full_name` (String(100)): 全名
- `role` (String(20), Indexed): 角色 (admin/user/readonly)
- `is_active` (Boolean): 是否激活
- `created_at` (DateTime): 创建时间
- `updated_at` (DateTime): 更新时间

**Relationships:**
- `network_segments`: 用户创建的网段 (One-to-Many)
- `allocated_ips`: 用户分配的 IP 地址 (One-to-Many)
- `devices`: 用户创建的设备 (One-to-Many)
- `operation_logs`: 用户的操作日志 (One-to-Many)
- `scan_histories`: 用户发起的扫描 (One-to-Many)

**Indexes:**
- `idx_users_username` on `username` (Unique)
- `idx_users_role` on `role`

---

### 2. NetworkSegment Model (网段表)

**Table Name:** `network_segments`

**Purpose:** 存储网络段信息，包括网络地址、前缀长度、网关等

**Columns:**
- `id` (Integer, PK): 主键
- `name` (String(100)): 网段名称
- `network` (String(45), Indexed): 网络地址 (如 192.168.1.0)
- `prefix_length` (Integer, Indexed): 前缀长度 (如 24)
- `gateway` (String(45)): 网关地址
- `description` (Text): 描述
- `usage_threshold` (Integer): 使用率告警阈值（百分比）
- `created_by` (Integer, FK): 创建人 ID
- `created_at` (DateTime): 创建时间
- `updated_at` (DateTime): 更新时间

**Relationships:**
- `creator`: 创建者 (Many-to-One to User)
- `ip_addresses`: 网段内的 IP 地址 (One-to-Many, Cascade Delete)
- `alerts`: 网段的告警 (One-to-Many, Cascade Delete)
- `scan_histories`: 网段的扫描历史 (One-to-Many, Cascade Delete)

**Indexes:**
- `idx_segments_network` on `(network, prefix_length)`

**Foreign Keys:**
- `created_by` → `users.id`

---

### 3. IPAddress Model (IP 地址表)

**Table Name:** `ip_addresses`

**Purpose:** 存储 IP 地址信息，包括状态、关联设备、分配信息等

**Columns:**
- `id` (Integer, PK): 主键
- `ip_address` (String(45), Unique, Indexed): IP 地址
- `status` (String(20), Indexed): 状态 (available/used/reserved)
- `segment_id` (Integer, FK, Indexed): 所属网段 ID
- `device_id` (Integer, FK, Indexed): 关联设备 ID
- `allocated_by` (Integer, FK): 分配人 ID
- `allocated_at` (DateTime): 分配时间
- `last_seen` (DateTime): 最后扫描时间
- `is_online` (Boolean): 是否在线（最后扫描结果）
- `created_at` (DateTime): 创建时间
- `updated_at` (DateTime): 更新时间

**Relationships:**
- `segment`: 所属网段 (Many-to-One to NetworkSegment)
- `device`: 关联设备 (Many-to-One to Device)
- `allocator`: 分配人 (Many-to-One to User)

**Indexes:**
- `idx_ip_address` on `ip_address` (Unique)
- `idx_ip_segment` on `segment_id`
- `idx_ip_status` on `status`
- `idx_ip_device` on `device_id`

**Foreign Keys:**
- `segment_id` → `network_segments.id`
- `device_id` → `devices.id`
- `allocated_by` → `users.id`

---

### 4. Device Model (设备表)

**Table Name:** `devices`

**Purpose:** 存储网络设备信息，包括设备名称、MAC 地址、责任人等

**Columns:**
- `id` (Integer, PK): 主键
- `name` (String(100), Indexed): 设备名称
- `mac_address` (String(17), Unique, Indexed): MAC 地址
- `device_type` (String(50)): 设备类型（服务器/交换机/路由器/终端等）
- `manufacturer` (String(100)): 制造商
- `model` (String(100)): 型号
- `owner` (String(100), Indexed): 责任人
- `department` (String(100)): 部门
- `location` (String(200)): 物理位置
- `description` (Text): 描述
- `created_by` (Integer, FK): 创建人 ID
- `created_at` (DateTime): 创建时间
- `updated_at` (DateTime): 更新时间

**Relationships:**
- `creator`: 创建者 (Many-to-One to User)
- `ip_addresses`: 设备关联的 IP 地址 (One-to-Many)

**Indexes:**
- `idx_device_mac` on `mac_address` (Unique)
- `idx_device_name` on `name`
- `idx_device_owner` on `owner`

**Foreign Keys:**
- `created_by` → `users.id`

---

### 5. OperationLog Model (操作日志表)

**Table Name:** `operation_logs`

**Purpose:** 记录系统中所有关键操作的审计记录

**Columns:**
- `id` (Integer, PK): 主键
- `user_id` (Integer, FK, Indexed): 操作人 ID
- `username` (String(50)): 操作人用户名（冗余字段）
- `operation_type` (String(20), Indexed): 操作类型 (create/update/delete/allocate/release)
- `resource_type` (String(20), Indexed): 资源类型 (ip/device/segment/user)
- `resource_id` (Integer): 资源 ID
- `details` (Text): 操作详情（JSON 格式）
- `ip_address` (String(45)): 客户端 IP
- `created_at` (DateTime, Indexed): 操作时间

**Relationships:**
- `user`: 操作人 (Many-to-One to User)

**Indexes:**
- `idx_log_user` on `user_id`
- `idx_log_type` on `(operation_type, resource_type)`
- `idx_log_time` on `created_at`

**Foreign Keys:**
- `user_id` → `users.id`

**Note:** 日志记录应该是只读的，不允许修改或删除，以保证审计追踪的完整性。

---

### 6. Alert Model (告警表)

**Table Name:** `alerts`

**Purpose:** 存储系统告警信息，主要用于网段使用率告警

**Columns:**
- `id` (Integer, PK): 主键
- `segment_id` (Integer, FK, Indexed): 网段 ID
- `alert_type` (String(50)): 告警类型 (usage_threshold)
- `severity` (String(20)): 严重程度 (warning/critical)
- `message` (Text): 告警消息
- `current_usage` (Float): 当前使用率
- `threshold` (Float): 阈值
- `is_resolved` (Boolean, Indexed): 是否已解决
- `resolved_at` (DateTime): 解决时间
- `created_at` (DateTime, Indexed): 创建时间

**Relationships:**
- `segment`: 关联网段 (Many-to-One to NetworkSegment)

**Indexes:**
- `idx_alert_segment` on `segment_id`
- `idx_alert_resolved` on `is_resolved`
- `idx_alert_time` on `created_at`

**Foreign Keys:**
- `segment_id` → `network_segments.id`

---

### 7. ScanHistory Model (扫描历史表)

**Table Name:** `scan_history`

**Purpose:** 记录 IP 扫描的历史记录和结果

**Columns:**
- `id` (Integer, PK): 主键
- `segment_id` (Integer, FK): 网段 ID
- `created_by` (Integer, FK): 发起人 ID
- `scan_type` (String(20)): 扫描类型 (ping/arp)
- `total_ips` (Integer): 扫描 IP 总数
- `online_ips` (Integer): 在线 IP 数量
- `duration` (Float): 扫描耗时（秒）
- `results` (Text): 扫描结果（JSON 格式）
- `created_at` (DateTime): 扫描时间

**Relationships:**
- `segment`: 关联网段 (Many-to-One to NetworkSegment)
- `creator`: 发起人 (Many-to-One to User)

**Foreign Keys:**
- `segment_id` → `network_segments.id`
- `created_by` → `users.id`

---

## Entity Relationship Diagram

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       │ creates
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────────┐  ┌──────────┐
│ NetworkSegment  │  │  Device  │
└────────┬────────┘  └────┬─────┘
         │                │
         │ contains       │ has
         │                │
         ▼                ▼
    ┌────────────┐◄───────┘
    │ IPAddress  │
    └────────────┘
         │
         │ generates
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
    ┌─────────┐      ┌──────────┐      ┌──────────────┐
    │  Alert  │      │   Log    │      │ ScanHistory  │
    └─────────┘      └──────────┘      └──────────────┘
```

## Cascade Delete Behavior

The following cascade delete rules are implemented:

1. **NetworkSegment deletion** → Cascades to:
   - All IPAddress records in that segment
   - All Alert records for that segment
   - All ScanHistory records for that segment

2. **User deletion** → Does NOT cascade (to preserve audit trail)
   - Foreign keys should be set to NULL or handled at application level

3. **Device deletion** → Does NOT cascade to IPAddress
   - IP addresses are released (device_id set to NULL) at application level

## Data Integrity Rules

1. **Unique Constraints:**
   - User.username must be unique
   - IPAddress.ip_address must be unique
   - Device.mac_address must be unique

2. **Required Fields:**
   - All models require created_at timestamp
   - User requires: username, hashed_password, email, full_name, role
   - NetworkSegment requires: name, network, prefix_length, created_by
   - IPAddress requires: ip_address, status, segment_id
   - Device requires: name, mac_address, owner, created_by
   - OperationLog requires: user_id, username, operation_type, resource_type
   - Alert requires: segment_id, alert_type, severity, message, current_usage, threshold
   - ScanHistory requires: segment_id, created_by, scan_type, total_ips, online_ips, duration

3. **Foreign Key Constraints:**
   - All foreign keys are enforced at database level
   - Referential integrity is maintained

## Usage Examples

### Creating a User
```python
from app.models import User
from app.core.security import get_password_hash

user = User(
    username="admin",
    hashed_password=get_password_hash("password123"),
    email="admin@example.com",
    full_name="Administrator",
    role="admin",
    is_active=True
)
db.add(user)
db.commit()
```

### Creating a Network Segment
```python
from app.models import NetworkSegment

segment = NetworkSegment(
    name="Office Network",
    network="192.168.1.0",
    prefix_length=24,
    gateway="192.168.1.1",
    description="Main office network",
    usage_threshold=80,
    created_by=user.id
)
db.add(segment)
db.commit()
```

### Allocating an IP Address
```python
from app.models import IPAddress
from datetime import datetime

ip = IPAddress(
    ip_address="192.168.1.100",
    status="used",
    segment_id=segment.id,
    device_id=device.id,
    allocated_by=user.id,
    allocated_at=datetime.now()
)
db.add(ip)
db.commit()
```

## Database Initialization

To initialize the database with all tables:

```python
from app.utils.init_db import init_db
from app.core.database import SessionLocal

db = SessionLocal()
try:
    init_db(db)
finally:
    db.close()
```

This will:
1. Create all database tables
2. Create the default admin user (from settings)

## Migration Strategy

For production deployments, use Alembic for database migrations:

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "Create initial tables"

# Apply migrations
alembic upgrade head
```

## Performance Considerations

1. **Indexes:** All frequently queried columns have indexes
2. **Connection Pooling:** Configured in database.py (pool_size=10, max_overflow=20)
3. **Lazy Loading:** Relationships use lazy loading by default
4. **Eager Loading:** Use `joinedload()` for frequently accessed relationships

## Security Considerations

1. **Password Hashing:** Uses bcrypt for password hashing
2. **SQL Injection:** Protected by SQLAlchemy parameterized queries
3. **Audit Trail:** All operations logged in OperationLog
4. **Soft Deletes:** Consider implementing for critical data

## Testing

Run the model verification script:

```bash
cd backend
python verify_models.py
```

This will verify:
- All models can be imported
- All table names and columns are correct
- All relationships are properly defined
- All foreign keys are in place
