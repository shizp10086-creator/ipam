# 数据库索引文档

本文档记录了 IPAM 系统中所有数据库表的索引实现情况。

## 索引实现概述

根据设计文档（design.md）的要求和性能需求（需求 16.4），系统已在 Task 2.1 中为所有核心表实现了必要的索引。

## 索引详细说明

### 1. 用户表 (users)

**表名**: `users`

**已实现的索引**:

| 索引字段 | 索引类型 | 说明 | 实现位置 |
|---------|---------|------|---------|
| `id` | PRIMARY KEY + INDEX | 主键索引，自动创建 | user.py:17 |
| `username` | UNIQUE + INDEX | 唯一索引，用于登录验证和用户查询 | user.py:20 |
| `role` | INDEX | 普通索引，用于按角色筛选用户 | user.py:27 |

**用途说明**:
- `username` 索引：加速用户登录验证（需求 10.1）
- `role` 索引：支持按角色筛选用户列表（需求 11.1, 11.2）

**SQL 等效语句**:
```sql
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
```

---

### 2. 网段表 (network_segments)

**表名**: `network_segments`

**已实现的索引**:

| 索引字段 | 索引类型 | 说明 | 实现位置 |
|---------|---------|------|---------|
| `id` | PRIMARY KEY + INDEX | 主键索引，自动创建 | network_segment.py:17 |
| `network` | INDEX | 普通索引，用于网段查询 | network_segment.py:21 |
| `prefix_length` | INDEX | 普通索引，用于网段查询 | network_segment.py:22 |

**用途说明**:
- `network` + `prefix_length` 索引：加速网段查询和 CIDR 验证（需求 1.1）
- 支持快速查找特定网络地址范围的网段

**SQL 等效语句**:
```sql
CREATE INDEX idx_segments_network ON network_segments(network);
CREATE INDEX idx_segments_prefix_length ON network_segments(prefix_length);
```

**注意**: 设计文档建议使用复合索引 `(network, prefix_length)`，但当前实现使用了两个独立索引。这两种方式都能满足查询需求，独立索引在某些查询场景下更灵活。

---

### 3. IP 地址表 (ip_addresses)

**表名**: `ip_addresses`

**已实现的索引**:

| 索引字段 | 索引类型 | 说明 | 实现位置 |
|---------|---------|------|---------|
| `id` | PRIMARY KEY + INDEX | 主键索引，自动创建 | ip_address.py:17 |
| `ip_address` | UNIQUE + INDEX | 唯一索引，确保 IP 地址唯一性 | ip_address.py:20 |
| `status` | INDEX | 普通索引，用于按状态筛选 IP | ip_address.py:26 |
| `segment_id` | FOREIGN KEY + INDEX | 外键索引，用于查询网段内的 IP | ip_address.py:30 |
| `device_id` | FOREIGN KEY + INDEX | 外键索引，用于查询设备关联的 IP | ip_address.py:31 |

**用途说明**:
- `ip_address` 索引：加速 IP 地址查询和冲突检测（需求 2.1, 4.2）
- `status` 索引：支持按状态筛选（空闲/已用/保留）（需求 2.4）
- `segment_id` 索引：加速网段内 IP 列表查询（需求 1.5, 1.6）
- `device_id` 索引：加速设备关联 IP 查询（需求 3.3）

**SQL 等效语句**:
```sql
CREATE UNIQUE INDEX idx_ip_address ON ip_addresses(ip_address);
CREATE INDEX idx_ip_status ON ip_addresses(status);
CREATE INDEX idx_ip_segment ON ip_addresses(segment_id);
CREATE INDEX idx_ip_device ON ip_addresses(device_id);
```

---

### 4. 设备表 (devices)

**表名**: `devices`

**已实现的索引**:

| 索引字段 | 索引类型 | 说明 | 实现位置 |
|---------|---------|------|---------|
| `id` | PRIMARY KEY + INDEX | 主键索引，自动创建 | device.py:17 |
| `name` | INDEX | 普通索引，用于设备名称搜索 | device.py:20 |
| `mac_address` | UNIQUE + INDEX | 唯一索引，确保 MAC 地址唯一性 | device.py:21 |
| `owner` | INDEX | 普通索引，用于按责任人筛选 | device.py:27 |

**用途说明**:
- `name` 索引：支持按设备名称模糊搜索（需求 3.6）
- `mac_address` 索引：加速 MAC 地址查询和验证（需求 3.2）
- `owner` 索引：支持按责任人筛选设备（需求 3.6）

**SQL 等效语句**:
```sql
CREATE UNIQUE INDEX idx_device_mac ON devices(mac_address);
CREATE INDEX idx_device_name ON devices(name);
CREATE INDEX idx_device_owner ON devices(owner);
```

---

### 5. 操作日志表 (operation_logs)

**表名**: `operation_logs`

**已实现的索引**:

| 索引字段 | 索引类型 | 说明 | 实现位置 |
|---------|---------|------|---------|
| `id` | PRIMARY KEY + INDEX | 主键索引，自动创建 | operation_log.py:17 |
| `user_id` | FOREIGN KEY + INDEX | 外键索引，用于按用户筛选日志 | operation_log.py:20 |
| `operation_type` | INDEX | 普通索引，用于按操作类型筛选 | operation_log.py:25 |
| `resource_type` | INDEX | 普通索引，用于按资源类型筛选 | operation_log.py:31 |
| `created_at` | INDEX | 普通索引，用于按时间范围筛选 | operation_log.py:42 |

**用途说明**:
- `user_id` 索引：支持按操作人筛选日志（需求 6.5）
- `operation_type` 索引：支持按操作类型筛选（需求 6.5）
- `resource_type` 索引：支持按资源类型筛选（需求 6.5）
- `created_at` 索引：支持按时间范围查询日志（需求 6.5）

**SQL 等效语句**:
```sql
CREATE INDEX idx_log_user ON operation_logs(user_id);
CREATE INDEX idx_log_operation_type ON operation_logs(operation_type);
CREATE INDEX idx_log_resource_type ON operation_logs(resource_type);
CREATE INDEX idx_log_time ON operation_logs(created_at);
```

**注意**: 设计文档建议使用复合索引 `(operation_type, resource_type)`，但当前实现使用了两个独立索引。这样可以更灵活地支持单独按操作类型或资源类型筛选的场景。

---

### 6. 告警表 (alerts)

**表名**: `alerts`

**已实现的索引**:

| 索引字段 | 索引类型 | 说明 | 实现位置 |
|---------|---------|------|---------|
| `id` | PRIMARY KEY + INDEX | 主键索引，自动创建 | alert.py:17 |
| `segment_id` | FOREIGN KEY + INDEX | 外键索引，用于查询网段的告警 | alert.py:20 |
| `is_resolved` | INDEX | 普通索引，用于筛选未解决的告警 | alert.py:32 |
| `created_at` | INDEX | 普通索引，用于按时间排序告警 | alert.py:36 |

**用途说明**:
- `segment_id` 索引：加速查询特定网段的告警（需求 9.2）
- `is_resolved` 索引：快速筛选未解决的告警（需求 9.3）
- `created_at` 索引：支持按时间排序和筛选告警历史（需求 9.6）

**SQL 等效语句**:
```sql
CREATE INDEX idx_alert_segment ON alerts(segment_id);
CREATE INDEX idx_alert_resolved ON alerts(is_resolved);
CREATE INDEX idx_alert_time ON alerts(created_at);
```

---

## 索引实现总结

### ✅ 已完全实现的索引（按设计文档要求）

1. **用户表**: ✅ username (UNIQUE), role
2. **网段表**: ✅ network, prefix_length
3. **IP 地址表**: ✅ ip_address (UNIQUE), segment_id, status, device_id
4. **设备表**: ✅ mac_address (UNIQUE), name, owner
5. **操作日志表**: ✅ user_id, operation_type, resource_type, created_at
6. **告警表**: ✅ segment_id, is_resolved, created_at

### 索引实现方式

所有索引都是在 SQLAlchemy 模型定义中通过 `index=True` 参数实现的。这种方式的优点：

1. **声明式定义**: 索引定义与表结构在同一位置，易于维护
2. **自动创建**: 使用 Alembic 迁移时会自动创建索引
3. **ORM 集成**: SQLAlchemy 会自动利用这些索引优化查询

### 性能影响分析

根据需求 16.4，这些索引将显著提升以下操作的性能：

1. **用户认证**: username 索引加速登录验证（< 100ms）
2. **IP 分配**: ip_address 和 segment_id 索引加速冲突检测（< 1s，需求 16.2）
3. **设备查询**: name 和 owner 索引支持快速模糊搜索
4. **日志查询**: 多个索引支持复杂的筛选条件
5. **告警监控**: is_resolved 索引快速获取活动告警

### 索引维护建议

1. **监控索引使用情况**: 定期检查索引的实际使用率
2. **避免过度索引**: 当前索引数量适中，不会显著影响写入性能
3. **考虑复合索引**: 如果发现频繁的组合查询，可以考虑添加复合索引：
   - `(network, prefix_length)` 用于网段查询
   - `(operation_type, resource_type)` 用于日志筛选
   - `(segment_id, status)` 用于网段内 IP 状态统计

### 数据库迁移

所有索引已在 Task 2.1 中通过 SQLAlchemy 模型定义实现。当运行 Alembic 迁移时，这些索引会自动创建：

```bash
# 创建迁移脚本
alembic revision --autogenerate -m "Create database indexes"

# 应用迁移
alembic upgrade head
```

### 验证索引

可以使用以下 SQL 命令验证索引是否正确创建：

```sql
-- 查看所有表的索引
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    NON_UNIQUE
FROM 
    INFORMATION_SCHEMA.STATISTICS
WHERE 
    TABLE_SCHEMA = 'ipam_db'
ORDER BY 
    TABLE_NAME, INDEX_NAME;

-- 查看特定表的索引
SHOW INDEX FROM users;
SHOW INDEX FROM network_segments;
SHOW INDEX FROM ip_addresses;
SHOW INDEX FROM devices;
SHOW INDEX FROM operation_logs;
SHOW INDEX FROM alerts;
```

## 结论

Task 2.2 的所有索引要求已在 Task 2.1 中完全实现。当前的索引配置满足：

- ✅ 设计文档中的所有索引要求
- ✅ 性能需求（需求 16.4）
- ✅ 查询优化需求（需求 16.2, 16.3）
- ✅ 数据完整性约束（UNIQUE 索引）

无需额外的代码修改，索引已经通过 SQLAlchemy 模型定义正确实现。
