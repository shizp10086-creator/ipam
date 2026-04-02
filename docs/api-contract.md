# API 契约文档

## 基础规范

### 基础路径
```
/api/v1
```

### 统一响应格式
```json
{
    "code": 200,
    "message": "success",
    "data": {},
    "trace_id": "uuid-string",
    "timestamp": "2026-01-01T00:00:00Z"
}
```

### 分页参数（游标分页）
```
GET /api/v1/ips?cursor=123&limit=50
```
响应：
```json
{
    "code": 200,
    "data": {
        "items": [],
        "total": 1000,
        "cursor": "173",
        "has_more": true
    }
}
```

### 错误码规范
| HTTP 状态码 | 含义 |
|------------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突（乐观锁/唯一约束） |
| 422 | 数据验证失败 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |

---

## 认证接口

### POST /api/v1/login
登录获取 Token。

请求：
```json
{"username": "admin", "password": "admin123"}
```
响应：
```json
{
    "code": 200,
    "data": {
        "access_token": "jwt-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
        "expires_in": 1800
    }
}
```

### POST /api/v1/token/refresh
刷新 Token。

### GET /api/v1/users/me
获取当前用户信息。

---

## 网段接口

### GET /api/v1/segments
获取网段列表。

查询参数：
- `cursor`: 游标（上一页最后一条的 ID）
- `limit`: 每页数量（默认 50）
- `group_id`: 按分组筛选
- `tags`: 按标签筛选（逗号分隔）
- `usage_min` / `usage_max`: 使用率范围筛选
- `search`: 搜索关键词

### POST /api/v1/segments
创建网段。

请求：
```json
{
    "cidr": "192.168.1.0/24",
    "description": "办公网段",
    "group_id": 1,
    "tags": ["办公", "核心"],
    "alert_threshold_warning": 80,
    "alert_threshold_critical": 90
}
```

### GET /api/v1/segments/{id}
获取网段详情（含使用率统计）。

### PUT /api/v1/segments/{id}
更新网段。

### DELETE /api/v1/segments/{id}?force=false
删除网段。`force=true` 强制删除。

---

## IP 地址接口

### GET /api/v1/ips
获取 IP 列表。

查询参数：
- `segment_id`: 按网段筛选
- `status`: 按状态筛选（available/used/reserved/temporary）
- `device_id`: 按设备筛选
- `tags`: 按标签筛选
- `search`: 搜索（IP/MAC/主机名/责任人）

### POST /api/v1/ips/allocate
分配 IP。

请求：
```json
{
    "segment_id": 1,
    "ip_address": "192.168.1.100",
    "device_id": 1,
    "responsible_person": "张三",
    "reason": "新服务器上线",
    "tags": ["服务器"]
}
```
自动分配（不指定 ip_address）：
```json
{
    "segment_id": 1,
    "device_id": 1,
    "auto_allocate": true
}
```

### POST /api/v1/ips/batch-allocate
批量分配 IP。

### POST /api/v1/ips/{id}/release
回收 IP。

### PUT /api/v1/ips/{id}/status
变更 IP 状态。

### GET /api/v1/ips/{id}/history
获取 IP 生命周期日志。

### GET /api/v1/segments/{id}/matrix
获取网段 IP 矩阵视图数据。

---

## 设备接口

### GET /api/v1/devices
获取设备列表。

### POST /api/v1/devices
创建设备。

### GET /api/v1/devices/{id}
获取设备详情。

### PUT /api/v1/devices/{id}
更新设备。

### DELETE /api/v1/devices/{id}
删除设备（逻辑删除）。

---

## 告警接口

### GET /api/v1/alerts
获取告警列表。

### PUT /api/v1/alerts/{id}/acknowledge
确认告警。

### PUT /api/v1/alerts/{id}/resolve
解决告警。

---

## 事件总线消息 Schema

### Exchange: ipam.ip
| Routing Key | 事件 | 消息体 |
|-------------|------|--------|
| ip.allocated | IP 已分配 | `{ip_address, segment_id, device_id, operator_id}` |
| ip.released | IP 已回收 | `{ip_address, segment_id, reason, operator_id}` |
| ip.conflict.detected | IP 冲突 | `{ip_address, conflict_type, details}` |
| ip.status.changed | 状态变更 | `{ip_address, old_status, new_status}` |

### Exchange: ipam.device
| Routing Key | 事件 | 消息体 |
|-------------|------|--------|
| device.created | 设备创建 | `{device_id, name, mac_address}` |
| device.deleted | 设备删除 | `{device_id, name, associated_ips}` |

### Exchange: ipam.alert
| Routing Key | 事件 | 消息体 |
|-------------|------|--------|
| alert.triggered | 告警触发 | `{alert_id, type, level, resource}` |
| alert.resolved | 告警恢复 | `{alert_id, resolved_by}` |
