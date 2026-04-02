# 设计文档：轻量版 IP 地址管理系统（IPAM）

## 概述

本系统采用前后端分离的微服务架构，后端使用 FastAPI 提供 RESTful API，前端使用 Vue 3 构建单页应用。系统通过 Docker Compose 实现容器化部署，支持 Windows 10 开发环境和 Linux 生产环境。

### 技术栈

**后端：**
- Python 3.10
- FastAPI（Web 框架）
- SQLAlchemy（ORM）
- Pydantic（数据验证）
- PyJWT（JWT 认证）
- Alembic（数据库迁移）
- python-multipart（文件上传）
- openpyxl（Excel 处理）
- asyncio（异步 Ping 扫描）

**前端：**
- Vue 3（Composition API）
- Vite（构建工具）
- Element Plus（UI 组件库）
- Vue Router（路由管理）
- Pinia（状态管理）
- Axios（HTTP 客户端）
- ECharts（数据可视化）

**数据库：**
- MySQL 8.0

**容器化：**
- Docker
- Docker Compose

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户浏览器                            │
│                    (Vue 3 + Element Plus)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/HTTP
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      Nginx (可选)                            │
│                   (反向代理 + 静态文件)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼──────────┐            ┌────────▼─────────┐
│   前端容器        │            │    后端容器       │
│  (Vue 3 SPA)     │            │   (FastAPI)      │
│  Port: 5173      │            │   Port: 8000     │
└──────────────────┘            └────────┬─────────┘
                                         │
                                ┌────────▼─────────┐
                                │   数据库容器      │
                                │   (MySQL 8.0)    │
                                │   Port: 3306     │
                                └──────────────────┘
```

## 架构设计

### 后端架构（分层设计）

```
app/
├── main.py                 # FastAPI 应用入口
├── core/                   # 核心配置
│   ├── config.py          # 配置管理
│   ├── security.py        # 安全相关（JWT、密码加密）
│   └── database.py        # 数据库连接
├── models/                 # SQLAlchemy 数据模型
│   ├── user.py
│   ├── network_segment.py
│   ├── ip_address.py
│   ├── device.py
│   ├── operation_log.py
│   └── alert.py
├── schemas/                # Pydantic 数据模式
│   ├── user.py
│   ├── network_segment.py
│   ├── ip_address.py
│   ├── device.py
│   └── common.py
├── api/                    # API 路由
│   ├── deps.py            # 依赖注入
│   ├── auth.py            # 认证相关
│   ├── users.py
│   ├── network_segments.py
│   ├── ip_addresses.py
│   ├── devices.py
│   ├── logs.py
│   ├── dashboard.py
│   └── import_export.py
├── services/               # 业务逻辑层
│   ├── ip_service.py
│   ├── device_service.py
│   ├── conflict_detection.py
│   ├── ping_scanner.py
│   ├── alert_service.py
│   └── excel_service.py
└── utils/                  # 工具函数
    ├── ip_utils.py
    ├── validators.py
    └── logger.py
```

### 前端架构（模块化设计）

```
src/
├── main.js                 # 应用入口
├── App.vue                 # 根组件
├── router/                 # 路由配置
│   └── index.js
├── stores/                 # Pinia 状态管理
│   ├── user.js
│   ├── auth.js
│   └── app.js
├── api/                    # API 请求封装
│   ├── request.js         # Axios 配置
│   ├── auth.js
│   ├── network.js
│   ├── ip.js
│   ├── device.js
│   └── dashboard.js
├── views/                  # 页面组件
│   ├── Login.vue
│   ├── Dashboard.vue
│   ├── NetworkSegment/
│   │   ├── List.vue
│   │   └── Form.vue
│   ├── IPAddress/
│   │   ├── List.vue
│   │   ├── Allocate.vue
│   │   └── Scanner.vue
│   ├── Device/
│   │   ├── List.vue
│   │   └── Form.vue
│   ├── Log/
│   │   └── List.vue
│   └── ImportExport/
│       └── Index.vue
├── components/             # 可复用组件
│   ├── Layout/
│   │   ├── Header.vue
│   │   ├── Sidebar.vue
│   │   └── Main.vue
│   ├── Charts/
│   │   ├── UsageChart.vue
│   │   └── StatusChart.vue
│   └── Common/
│       ├── Pagination.vue
│       └── SearchBar.vue
└── utils/                  # 工具函数
    ├── auth.js
    ├── validators.js
    └── formatters.js
```

## 组件和接口

### 数据模型设计

#### User（用户表）

```python
class User(Base):
    __tablename__ = "users"
    
    id: int                    # 主键
    username: str              # 用户名（唯一）
    hashed_password: str       # 加密密码
    email: str                 # 邮箱
    full_name: str             # 全名
    role: str                  # 角色（admin/user/readonly）
    is_active: bool            # 是否激活
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

#### NetworkSegment（网段表）

```python
class NetworkSegment(Base):
    __tablename__ = "network_segments"
    
    id: int                    # 主键
    name: str                  # 网段名称
    network: str               # 网络地址（如 192.168.1.0）
    prefix_length: int         # 前缀长度（如 24）
    gateway: str               # 网关地址（可选）
    description: str           # 描述
    usage_threshold: int       # 使用率告警阈值（百分比）
    total_ips: int             # 总 IP 数量（计算字段）
    used_ips: int              # 已用 IP 数量（计算字段）
    created_by: int            # 创建人 ID（外键）
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

#### IPAddress（IP 地址表）

```python
class IPAddress(Base):
    __tablename__ = "ip_addresses"
    
    id: int                    # 主键
    segment_id: int            # 所属网段 ID（外键）
    ip_address: str            # IP 地址（唯一）
    status: str                # 状态（available/used/reserved）
    device_id: int             # 关联设备 ID（外键，可空）
    allocated_at: datetime     # 分配时间
    allocated_by: int          # 分配人 ID（外键）
    last_seen: datetime        # 最后扫描时间
    is_online: bool            # 是否在线（最后扫描结果）
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

#### Device（设备表）

```python
class Device(Base):
    __tablename__ = "devices"
    
    id: int                    # 主键
    name: str                  # 设备名称
    mac_address: str           # MAC 地址（唯一）
    device_type: str           # 设备类型（服务器/交换机/路由器/终端等）
    manufacturer: str          # 制造商
    model: str                 # 型号
    owner: str                 # 责任人
    department: str            # 部门
    location: str              # 物理位置
    description: str           # 描述
    created_by: int            # 创建人 ID（外键）
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

#### OperationLog（操作日志表）

```python
class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id: int                    # 主键
    user_id: int               # 操作人 ID（外键）
    username: str              # 操作人用户名（冗余字段）
    operation_type: str        # 操作类型（create/update/delete/allocate/release）
    resource_type: str         # 资源类型（ip/device/segment/user）
    resource_id: int           # 资源 ID
    details: str               # 操作详情（JSON 格式）
    ip_address: str            # 客户端 IP
    created_at: datetime       # 操作时间
```

#### Alert（告警表）

```python
class Alert(Base):
    __tablename__ = "alerts"
    
    id: int                    # 主键
    segment_id: int            # 网段 ID（外键）
    alert_type: str            # 告警类型（usage_threshold）
    severity: str              # 严重程度（warning/critical）
    message: str               # 告警消息
    current_usage: float       # 当前使用率
    threshold: float           # 阈值
    is_resolved: bool          # 是否已解决
    resolved_at: datetime      # 解决时间
    created_at: datetime       # 创建时间
```

#### ScanHistory（扫描历史表）

```python
class ScanHistory(Base):
    __tablename__ = "scan_history"
    
    id: int                    # 主键
    segment_id: int            # 网段 ID（外键）
    scan_type: str             # 扫描类型（ping/arp）
    total_ips: int             # 扫描 IP 总数
    online_ips: int            # 在线 IP 数量
    duration: float            # 扫描耗时（秒）
    results: str               # 扫描结果（JSON 格式）
    created_by: int            # 发起人 ID（外键）
    created_at: datetime       # 扫描时间
```

### 数据库索引设计

```sql
-- 用户表索引
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

-- 网段表索引
CREATE INDEX idx_segments_network ON network_segments(network, prefix_length);

-- IP 地址表索引
CREATE UNIQUE INDEX idx_ip_address ON ip_addresses(ip_address);
CREATE INDEX idx_ip_segment ON ip_addresses(segment_id);
CREATE INDEX idx_ip_status ON ip_addresses(status);
CREATE INDEX idx_ip_device ON ip_addresses(device_id);

-- 设备表索引
CREATE UNIQUE INDEX idx_device_mac ON devices(mac_address);
CREATE INDEX idx_device_name ON devices(name);
CREATE INDEX idx_device_owner ON devices(owner);

-- 操作日志表索引
CREATE INDEX idx_log_user ON operation_logs(user_id);
CREATE INDEX idx_log_type ON operation_logs(operation_type, resource_type);
CREATE INDEX idx_log_time ON operation_logs(created_at);

-- 告警表索引
CREATE INDEX idx_alert_segment ON alerts(segment_id);
CREATE INDEX idx_alert_resolved ON alerts(is_resolved);
CREATE INDEX idx_alert_time ON alerts(created_at);
```

### API 接口设计

#### 认证接口

```
POST   /api/v1/auth/login          # 用户登录
POST   /api/v1/auth/refresh        # 刷新 Token
POST   /api/v1/auth/logout         # 用户登出
GET    /api/v1/auth/me             # 获取当前用户信息
```

#### 用户管理接口

```
GET    /api/v1/users               # 获取用户列表
POST   /api/v1/users               # 创建用户（仅管理员）
GET    /api/v1/users/{id}          # 获取用户详情
PUT    /api/v1/users/{id}          # 更新用户信息
DELETE /api/v1/users/{id}          # 删除用户（仅管理员）
PUT    /api/v1/users/{id}/password # 修改密码
```

#### 网段管理接口

```
GET    /api/v1/segments            # 获取网段列表
POST   /api/v1/segments            # 创建网段
GET    /api/v1/segments/{id}       # 获取网段详情
PUT    /api/v1/segments/{id}       # 更新网段
DELETE /api/v1/segments/{id}       # 删除网段
GET    /api/v1/segments/{id}/stats # 获取网段统计信息
```

#### IP 地址管理接口

```
GET    /api/v1/ips                 # 获取 IP 地址列表
POST   /api/v1/ips/allocate        # 分配 IP 地址
POST   /api/v1/ips/release         # 回收 IP 地址
GET    /api/v1/ips/{id}            # 获取 IP 详情
PUT    /api/v1/ips/{id}            # 更新 IP 信息
POST   /api/v1/ips/check-conflict  # 检查 IP 冲突
POST   /api/v1/ips/scan            # 扫描网段
GET    /api/v1/ips/scan-history    # 获取扫描历史
```

#### 设备管理接口

```
GET    /api/v1/devices             # 获取设备列表
POST   /api/v1/devices             # 创建设备
GET    /api/v1/devices/{id}        # 获取设备详情
PUT    /api/v1/devices/{id}        # 更新设备信息
DELETE /api/v1/devices/{id}        # 删除设备
GET    /api/v1/devices/{id}/ips    # 获取设备关联的 IP
```

#### 操作日志接口

```
GET    /api/v1/logs                # 获取操作日志列表
GET    /api/v1/logs/{id}           # 获取日志详情
```

#### 告警管理接口

```
GET    /api/v1/alerts              # 获取告警列表
GET    /api/v1/alerts/{id}         # 获取告警详情
PUT    /api/v1/alerts/{id}/resolve # 解决告警
```

#### 仪表板接口

```
GET    /api/v1/dashboard/stats     # 获取统计数据
GET    /api/v1/dashboard/charts    # 获取图表数据
```

#### 导入导出接口

```
GET    /api/v1/import-export/template      # 下载 Excel 模板
POST   /api/v1/import-export/import        # 导入 Excel 数据
GET    /api/v1/import-export/export        # 导出 Excel 数据
```

### API 响应格式

#### 成功响应

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    // 响应数据
  }
}
```

#### 错误响应

```json
{
  "code": 400,
  "message": "Invalid request parameters",
  "errors": [
    {
      "field": "ip_address",
      "message": "Invalid IP address format"
    }
  ]
}
```

#### 分页响应

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

## 数据模型

### IP 地址状态机

```mermaid
stateDiagram-v2
    [*] --> Available: 创建网段时自动生成
    Available --> Used: 分配给设备
    Available --> Reserved: 手动标记为保留
    Used --> Available: 回收 IP
    Reserved --> Available: 取消保留
    Reserved --> Used: 分配给设备
    Used --> [*]: 删除网段
    Available --> [*]: 删除网段
    Reserved --> [*]: 删除网段
```

### 网段使用率计算

```python
def calculate_segment_usage(segment: NetworkSegment) -> dict:
    """
    计算网段使用率
    
    Args:
        segment: 网段对象
        
    Returns:
        {
            'total_ips': int,      # 总 IP 数量
            'used_ips': int,       # 已用 IP 数量
            'available_ips': int,  # 可用 IP 数量
            'reserved_ips': int,   # 保留 IP 数量
            'usage_rate': float    # 使用率（百分比）
        }
    """
    # 计算总 IP 数量（排除网络地址和广播地址）
    total_ips = 2 ** (32 - segment.prefix_length) - 2
    
    # 查询各状态 IP 数量
    used_ips = count_ips_by_status(segment.id, 'used')
    reserved_ips = count_ips_by_status(segment.id, 'reserved')
    available_ips = total_ips - used_ips - reserved_ips
    
    # 计算使用率
    usage_rate = (used_ips + reserved_ips) / total_ips * 100
    
    return {
        'total_ips': total_ips,
        'used_ips': used_ips,
        'available_ips': available_ips,
        'reserved_ips': reserved_ips,
        'usage_rate': round(usage_rate, 2)
    }
```

### IP 地址冲突检测流程

```mermaid
flowchart TD
    A[开始分配 IP] --> B[逻辑冲突检测]
    B --> C{数据库中是否存在?}
    C -->|是| D[检查状态]
    D --> E{状态是否为 available?}
    E -->|否| F[返回逻辑冲突错误]
    E -->|是| G[物理冲突检测]
    C -->|否| G
    G --> H[执行 Ping 测试]
    H --> I{是否有响应?}
    I -->|是| J[返回物理冲突错误]
    I -->|否| K[执行 ARP 检测]
    K --> L{是否发现 MAC?}
    L -->|是| M[返回物理冲突错误]
    L -->|否| N[分配 IP 成功]
    F --> O[结束]
    J --> O
    M --> O
    N --> O
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 网段管理属性

**属性 1：CIDR 格式验证**
*对于任何* 输入的网段字符串，如果它符合有效的 CIDR 表示法（如 192.168.1.0/24），系统应该接受它；如果格式无效，系统应该拒绝并返回错误。
**验证需求：1.1**

**属性 2：网段编辑保持 IP 关联**
*对于任何* 已存在的网段，当更新其信息（名称、描述等）时，该网段内所有已分配 IP 地址的关联关系应该保持不变。
**验证需求：1.2**

**属性 3：删除网段前检查 IP 分配**
*对于任何* 包含已分配 IP 地址的网段，删除操作应该被拒绝并返回错误信息。
**验证需求：1.3, 1.4**

**属性 4：网段可用 IP 计算正确性**
*对于任何* CIDR 网段，计算的总 IP 数量应该等于 2^(32 - prefix_length) - 2（排除网络地址和广播地址）。
**验证需求：1.5**

**属性 5：网段使用率计算正确性**
*对于任何* 网段，使用率应该等于 (已用 IP 数 + 保留 IP 数) / 总 IP 数 × 100%。
**验证需求：1.6**

### IP 地址生命周期管理属性

**属性 6：IP 地址必须属于已存在网段**
*对于任何* IP 地址分配请求，只有当 IP 地址在某个已存在网段的范围内时，系统才应该接受该请求。
**验证需求：2.1**

**属性 7：IP 回收状态转换**
*对于任何* 状态为"已用"的 IP 地址，回收操作后其状态应该变为"空闲"，且设备关联应该被解除（device_id 为 null）。
**验证需求：2.3**

**属性 8：IP 状态枚举完整性**
*对于任何* IP 地址，其状态只能是以下三种之一：Available（空闲）、Used（已用）、Reserved（保留）。
**验证需求：2.4**

**属性 9：IP 查询返回完整信息**
*对于任何* IP 地址查询请求，返回的数据应该包含当前状态、关联设备信息和历史操作记录。
**验证需求：2.5**

**属性 10：保留 IP 不可自动分配**
*对于任何* 状态为"保留"的 IP 地址，自动分配操作应该跳过该 IP，不将其分配给任何设备。
**验证需求：2.6**

### 设备资产管理属性

**属性 11：设备创建必填字段验证**
*对于任何* 设备创建请求，如果缺少设备名称、MAC 地址或责任人信息中的任何一项，系统应该拒绝该请求。
**验证需求：3.1**

**属性 12：MAC 地址格式验证**
*对于任何* MAC 地址输入，系统应该验证其格式（如 AA:BB:CC:DD:EE:FF 或 AA-BB-CC-DD-EE-FF），只接受有效格式。
**验证需求：3.2**

**属性 13：设备关联 IP 状态验证**
*对于任何* 设备与 IP 的关联操作，只有当 IP 地址状态为"空闲"或"保留"时，系统才应该允许关联。
**验证需求：3.3**

**属性 14：设备编辑保持 IP 关联**
*对于任何* 设备信息更新操作，该设备关联的所有 IP 地址应该保持不变。
**验证需求：3.4**

**属性 15：设备删除级联回收 IP**
*对于任何* 设备删除操作，该设备关联的所有 IP 地址应该自动被回收（状态变为"空闲"）。
**验证需求：3.5**

**属性 16：设备模糊搜索结果正确性**
*对于任何* 设备搜索请求，返回的所有设备记录应该在设备名称、MAC 地址或责任人字段中包含搜索关键词。
**验证需求：3.6**

### IP 冲突检测属性

**属性 17：逻辑冲突检测**
*对于任何* IP 分配请求，如果该 IP 在数据库中已被标记为"已用"或"保留"，系统应该拒绝分配并返回逻辑冲突错误。
**验证需求：4.2**

**属性 18：冲突错误信息完整性**
*对于任何* 冲突检测失败的情况，返回的错误信息应该明确指出是逻辑冲突还是物理冲突。
**验证需求：4.6**

### IP 扫描属性

**属性 19：扫描结果数据完整性**
*对于任何* IP 扫描操作，每个被扫描 IP 的结果应该包含响应状态（在线/离线）和响应时间。
**验证需求：5.4**

**属性 20：扫描报告标识未注册 IP**
*对于任何* 扫描完成后的报告，应该明确标识出在网络中在线但未在数据库中注册的 IP 地址。
**验证需求：5.5**

**属性 21：扫描结果持久化**
*对于任何* 完成的扫描操作，其结果应该被存储到数据库中，并可通过历史记录查询接口检索。
**验证需求：5.6**

### 操作日志属性

**属性 22：IP 分配操作日志完整性**
*对于任何* IP 分配操作，系统应该创建一条日志记录，包含操作人、操作时间、IP 地址和关联设备信息。
**验证需求：6.1**

**属性 23：IP 回收操作日志完整性**
*对于任何* IP 回收操作，系统应该创建一条日志记录，包含操作人、操作时间和 IP 地址。
**验证需求：6.2**

**属性 24：设备操作日志完整性**
*对于任何* 设备的创建、编辑或删除操作，系统应该创建一条日志记录，包含完整的操作详情。
**验证需求：6.3**

**属性 25：网段操作日志完整性**
*对于任何* 网段的创建、编辑或删除操作，系统应该创建一条日志记录，包含网段信息和操作类型。
**验证需求：6.4**

**属性 26：日志筛选结果正确性**
*对于任何* 带筛选条件的日志查询，返回的所有日志记录应该匹配指定的操作人、操作类型或时间范围条件。
**验证需求：6.5**

### 数据可视化属性

**属性 27：网段使用率统计正确性**
*对于任何* 网段使用率统计请求，返回的每个网段的使用率数据应该与实际数据库中的 IP 分配情况一致。
**验证需求：7.1**

**属性 28：IP 状态分布统计正确性**
*对于任何* IP 状态分布统计请求，返回的空闲、已用、保留 IP 数量总和应该等于所有网段的总 IP 数量。
**验证需求：7.2**

**属性 29：设备统计数据正确性**
*对于任何* 设备统计请求，返回的设备总数应该等于数据库中设备表的记录数。
**验证需求：7.3**

**属性 30：仪表板关键指标完整性**
*对于任何* 仪表板数据请求，返回的数据应该包含总 IP 数、已用 IP 数和设备总数这三个关键指标。
**验证需求：7.4**

**属性 31：统计数据实时性**
*对于任何* 统计数据请求，返回的数据应该反映当前数据库的最新状态（不使用过期缓存）。
**验证需求：7.5**

**属性 32：时间范围筛选正确性**
*对于任何* 带时间范围的统计请求，返回的数据应该只包含指定时间范围内的记录。
**验证需求：7.6**

### Excel 导入导出属性

**属性 33：导入数据格式验证**
*对于任何* Excel 导入请求，如果文件中存在格式错误（无效 IP、无效 MAC、缺少必填字段），系统应该拒绝整个导入并返回详细错误报告。
**验证需求：8.2, 8.3, 8.4**

**属性 34：导出数据完整性**
*对于任何* 数据导出请求，生成的 Excel 文件应该包含所有数据字段（不丢失任何列）。
**验证需求：8.5**

**属性 35：导出筛选结果正确性**
*对于任何* 带筛选条件的导出请求，导出的数据应该只包含符合筛选条件的记录。
**验证需求：8.6**

### 告警管理属性

**属性 36：使用率告警触发条件**
*对于任何* 网段，当其使用率达到或超过设置的阈值时，系统应该自动生成一条告警记录。
**验证需求：9.2**

**属性 37：告警记录数据完整性**
*对于任何* 生成的告警记录，应该包含触发时间、网段信息、当前使用率和阈值。
**验证需求：9.4**

**属性 38：告警自动解除条件**
*对于任何* 活跃的告警，当对应网段的使用率降低到阈值以下时，系统应该自动将告警标记为已解除。
**验证需求：9.5**

**属性 39：告警查询筛选正确性**
*对于任何* 带筛选条件的告警查询，返回的告警记录应该匹配指定的筛选条件。
**验证需求：9.6**

### 认证与授权属性

**属性 40：JWT Token 内容完整性**
*对于任何* 成功登录后生成的 JWT Token，解码后应该包含用户 ID、角色和过期时间信息。
**验证需求：10.3**

**属性 41：过期 Token 拒绝访问**
*对于任何* 使用过期 JWT Token 的 API 请求，系统应该返回 401 未授权错误。
**验证需求：10.4, 10.5**

**属性 42：角色枚举完整性**
*对于任何* 用户，其角色只能是以下三种之一：Administrator、Regular_User、ReadOnly_User。
**验证需求：11.1**

**属性 43：管理员权限完整性**
*对于任何* 角色为 Administrator 的用户，应该能够执行所有操作（创建、读取、更新、删除）。
**验证需求：11.2**

**属性 44：普通用户权限限制**
*对于任何* 角色为 Regular_User 的用户，尝试创建/删除网段或管理用户的操作应该被拒绝并返回 403 错误。
**验证需求：11.4**

**属性 45：只读用户权限限制**
*对于任何* 角色为 ReadOnly_User 的用户，所有修改操作（POST、PUT、DELETE）应该被拒绝并返回 403 错误。
**验证需求：11.5**

**属性 46：权限拒绝错误码**
*对于任何* 超出用户权限的操作请求，系统应该返回 403 禁止访问错误。
**验证需求：11.6**

**属性 47：日志记录包含角色信息**
*对于任何* 操作日志记录，应该包含执行操作的用户的角色信息。
**验证需求：11.7**

### 数据持久化属性

**属性 48：事务原子性**
*对于任何* 包含多个数据库操作的事务，如果任何一步失败，所有操作应该被回滚，不留下部分数据。
**验证需求：13.2, 13.3**

### API 接口属性

**属性 49：HTTP 状态码正确性**
*对于任何* API 响应，应该使用适当的 HTTP 状态码：成功操作返回 2xx，客户端错误返回 4xx，服务器错误返回 5xx。
**验证需求：14.2**

**属性 50：响应格式统一性**
*对于任何* API 响应，JSON 格式应该包含 code、message 和 data 字段。
**验证需求：14.3**

**属性 51：验证错误详细信息**
*对于任何* 参数验证失败的请求，返回的错误信息应该包含具体的字段名和错误原因。
**验证需求：14.5**

**属性 52：分页排序筛选支持**
*对于任何* 列表查询接口，应该支持 page、page_size、sort_by 和 filter 等查询参数。
**验证需求：15.3**

**属性 53：日志格式完整性**
*对于任何* 系统日志记录，应该包含时间戳、日志级别、模块名称和详细信息。
**验证需求：17.2**



## 错误处理

### 错误分类

系统采用分层错误处理策略，将错误分为以下几类：

1. **验证错误（Validation Errors）**：输入数据格式或内容不符合要求
2. **业务逻辑错误（Business Logic Errors）**：违反业务规则（如删除包含 IP 的网段）
3. **资源不存在错误（Not Found Errors）**：请求的资源不存在
4. **权限错误（Permission Errors）**：用户无权执行该操作
5. **冲突错误（Conflict Errors）**：资源状态冲突（如 IP 地址已被占用）
6. **系统错误（System Errors）**：数据库连接失败、外部服务不可用等

### 错误响应格式

```json
{
  "code": 400,
  "message": "Validation failed",
  "errors": [
    {
      "field": "ip_address",
      "message": "Invalid IP address format",
      "value": "192.168.1.999"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/ips/allocate"
}
```

### 错误处理策略

#### 1. 验证错误处理

```python
from pydantic import BaseModel, validator, ValidationError
from fastapi import HTTPException

class IPAllocationRequest(BaseModel):
    ip_address: str
    segment_id: int
    device_id: int
    
    @validator('ip_address')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address format')
        return v

@app.post("/api/v1/ips/allocate")
async def allocate_ip(request: IPAllocationRequest):
    try:
        # 业务逻辑
        pass
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "message": "Validation failed",
                "errors": e.errors()
            }
        )
```

#### 2. 业务逻辑错误处理

```python
class BusinessLogicError(Exception):
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

def delete_segment(segment_id: int):
    segment = db.query(NetworkSegment).filter_by(id=segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    # 检查是否有已分配的 IP
    used_ips = db.query(IPAddress).filter_by(
        segment_id=segment_id,
        status='used'
    ).count()
    
    if used_ips > 0:
        raise BusinessLogicError(
            message=f"Cannot delete segment with {used_ips} allocated IPs",
            code="SEGMENT_HAS_ALLOCATED_IPS"
        )
    
    db.delete(segment)
    db.commit()
```

#### 3. 数据库错误处理

```python
from sqlalchemy.exc import IntegrityError, OperationalError

@app.post("/api/v1/devices")
async def create_device(device: DeviceCreate):
    try:
        db_device = Device(**device.dict())
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        return db_device
    except IntegrityError as e:
        db.rollback()
        if 'mac_address' in str(e):
            raise HTTPException(
                status_code=409,
                detail="Device with this MAC address already exists"
            )
        raise HTTPException(status_code=500, detail="Database integrity error")
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database operational error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        )
```

#### 4. 全局异常处理器

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(BusinessLogicError)
async def business_logic_error_handler(request: Request, exc: BusinessLogicError):
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "message": exc.message,
            "error_code": exc.code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )
```

### 日志记录策略

```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
def setup_logging():
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器（自动轮转）
    file_handler = RotatingFileHandler(
        'logs/ipam.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 使用日志
logger = setup_logging()

# 不同级别的日志示例
logger.debug("Detailed debug information")
logger.info("IP address allocated: 192.168.1.10")
logger.warning("Network segment usage above 80%")
logger.error("Failed to connect to database", exc_info=True)
logger.critical("System critical failure", exc_info=True)
```



## 测试策略

### 双重测试方法

系统采用单元测试和基于属性的测试（Property-Based Testing）相结合的策略，确保全面的代码覆盖和正确性验证。

#### 单元测试（Unit Tests）
- 验证特定示例和边界情况
- 测试错误条件和异常处理
- 测试组件之间的集成点
- 使用 pytest 框架

#### 基于属性的测试（Property-Based Tests）
- 验证跨所有输入的通用属性
- 通过随机化实现全面的输入覆盖
- 使用 Hypothesis 库（Python）
- 每个属性测试最少运行 100 次迭代

### 测试框架和工具

**后端测试：**
- pytest：测试框架
- pytest-asyncio：异步测试支持
- Hypothesis：基于属性的测试
- pytest-cov：代码覆盖率
- factory_boy：测试数据工厂
- faker：生成随机测试数据

**前端测试：**
- Vitest：单元测试框架
- @vue/test-utils：Vue 组件测试
- fast-check：基于属性的测试（JavaScript）
- Playwright：端到端测试

### 测试组织结构

```
tests/
├── unit/                      # 单元测试
│   ├── test_ip_service.py
│   ├── test_device_service.py
│   ├── test_conflict_detection.py
│   └── test_validators.py
├── property/                  # 基于属性的测试
│   ├── test_network_properties.py
│   ├── test_ip_properties.py
│   ├── test_device_properties.py
│   └── test_auth_properties.py
├── integration/               # 集成测试
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_excel_import_export.py
├── e2e/                       # 端到端测试
│   └── test_user_workflows.py
├── fixtures/                  # 测试固件
│   ├── database.py
│   ├── users.py
│   └── sample_data.py
└── conftest.py               # pytest 配置
```

### 基于属性的测试示例

#### 示例 1：网段 CIDR 格式验证（属性 1）

```python
from hypothesis import given, strategies as st
import ipaddress

# 生成有效的 CIDR 字符串
@st.composite
def valid_cidr(draw):
    # 生成随机 IP 地址
    octets = [draw(st.integers(0, 255)) for _ in range(4)]
    ip = '.'.join(map(str, octets))
    # 生成随机前缀长度
    prefix = draw(st.integers(8, 30))
    return f"{ip}/{prefix}"

# 生成无效的 CIDR 字符串
@st.composite
def invalid_cidr(draw):
    return draw(st.one_of(
        st.text(),  # 随机文本
        st.just("192.168.1.0/33"),  # 无效前缀
        st.just("999.999.999.999/24"),  # 无效 IP
        st.just("192.168.1.0"),  # 缺少前缀
    ))

@given(cidr=valid_cidr())
def test_valid_cidr_accepted(cidr):
    """
    Feature: ipam-system, Property 1: CIDR 格式验证
    对于任何有效的 CIDR 格式，系统应该接受它
    """
    result = validate_cidr(cidr)
    assert result.is_valid == True
    assert result.error is None

@given(cidr=invalid_cidr())
def test_invalid_cidr_rejected(cidr):
    """
    Feature: ipam-system, Property 1: CIDR 格式验证
    对于任何无效的 CIDR 格式，系统应该拒绝它
    """
    result = validate_cidr(cidr)
    assert result.is_valid == False
    assert result.error is not None
```

#### 示例 2：网段使用率计算（属性 5）

```python
from hypothesis import given, strategies as st, assume

@given(
    prefix_length=st.integers(8, 30),
    used_count=st.integers(0, 1000),
    reserved_count=st.integers(0, 1000)
)
def test_segment_usage_calculation(prefix_length, used_count, reserved_count):
    """
    Feature: ipam-system, Property 5: 网段使用率计算正确性
    对于任何网段，使用率应该等于 (已用 + 保留) / 总数 × 100%
    """
    # 计算总 IP 数
    total_ips = 2 ** (32 - prefix_length) - 2
    
    # 确保已用和保留的总数不超过总 IP 数
    assume(used_count + reserved_count <= total_ips)
    
    # 创建测试网段
    segment = create_test_segment(
        prefix_length=prefix_length,
        used_ips=used_count,
        reserved_ips=reserved_count
    )
    
    # 计算使用率
    stats = calculate_segment_usage(segment)
    
    # 验证计算正确性
    expected_usage = (used_count + reserved_count) / total_ips * 100
    assert abs(stats['usage_rate'] - expected_usage) < 0.01
    assert stats['total_ips'] == total_ips
    assert stats['used_ips'] == used_count
    assert stats['reserved_ips'] == reserved_count
```

#### 示例 3：IP 回收状态转换（属性 7）

```python
from hypothesis import given, strategies as st

@st.composite
def used_ip_address(draw):
    """生成一个已使用的 IP 地址"""
    ip = draw(st.ip_addresses(v=4))
    device_id = draw(st.integers(1, 1000))
    return create_test_ip(
        ip_address=str(ip),
        status='used',
        device_id=device_id
    )

@given(ip=used_ip_address())
def test_ip_release_state_transition(ip):
    """
    Feature: ipam-system, Property 7: IP 回收状态转换
    对于任何已用 IP，回收后状态应变为空闲且设备关联解除
    """
    # 记录原始状态
    original_ip = ip.ip_address
    original_device_id = ip.device_id
    
    # 执行回收操作
    result = release_ip(ip.id)
    
    # 验证状态转换
    updated_ip = get_ip_by_id(ip.id)
    assert updated_ip.status == 'available'
    assert updated_ip.device_id is None
    assert updated_ip.ip_address == original_ip  # IP 地址本身不变
```

#### 示例 4：设备删除级联回收 IP（属性 15）

```python
from hypothesis import given, strategies as st

@st.composite
def device_with_ips(draw):
    """生成一个关联了多个 IP 的设备"""
    device = create_test_device()
    ip_count = draw(st.integers(1, 10))
    ips = [
        create_test_ip(
            status='used',
            device_id=device.id
        )
        for _ in range(ip_count)
    ]
    return device, ips

@given(data=device_with_ips())
def test_device_deletion_cascades_ip_release(data):
    """
    Feature: ipam-system, Property 15: 设备删除级联回收 IP
    对于任何设备，删除后其所有关联 IP 应自动回收
    """
    device, ips = data
    ip_ids = [ip.id for ip in ips]
    
    # 删除设备
    delete_device(device.id)
    
    # 验证所有 IP 都被回收
    for ip_id in ip_ids:
        ip = get_ip_by_id(ip_id)
        assert ip.status == 'available'
        assert ip.device_id is None
```

#### 示例 5：权限控制（属性 44, 45）

```python
from hypothesis import given, strategies as st

@given(
    user_role=st.sampled_from(['regular_user', 'readonly_user']),
    operation=st.sampled_from(['create_segment', 'delete_segment', 'manage_users'])
)
def test_permission_restrictions(user_role, operation):
    """
    Feature: ipam-system, Property 44, 45: 权限限制
    对于非管理员用户，特定操作应被拒绝
    """
    user = create_test_user(role=user_role)
    token = generate_jwt_token(user)
    
    # 尝试执行操作
    response = execute_operation(operation, token)
    
    # 验证被拒绝
    assert response.status_code == 403
    assert 'forbidden' in response.json()['message'].lower()
```

### 单元测试示例

#### 示例 1：IP 冲突检测

```python
import pytest
from unittest.mock import Mock, patch

def test_logical_conflict_detection():
    """测试逻辑冲突检测"""
    # 创建一个已使用的 IP
    existing_ip = create_test_ip(
        ip_address='192.168.1.10',
        status='used'
    )
    
    # 尝试分配相同 IP
    with pytest.raises(ConflictError) as exc_info:
        allocate_ip('192.168.1.10', device_id=999)
    
    assert 'logical conflict' in str(exc_info.value).lower()

@patch('services.conflict_detection.ping')
def test_physical_conflict_detection(mock_ping):
    """测试物理冲突检测"""
    # 模拟 ping 返回成功（IP 在线）
    mock_ping.return_value = True
    
    # 尝试分配 IP
    with pytest.raises(ConflictError) as exc_info:
        allocate_ip('192.168.1.20', device_id=1)
    
    assert 'physical conflict' in str(exc_info.value).lower()
    mock_ping.assert_called_once_with('192.168.1.20')
```

#### 示例 2：JWT Token 验证

```python
import pytest
from datetime import datetime, timedelta

def test_jwt_token_contains_required_claims():
    """测试 JWT Token 包含必需的声明"""
    user = create_test_user(role='admin')
    token = generate_jwt_token(user)
    
    # 解码 token
    payload = decode_jwt_token(token)
    
    # 验证必需字段
    assert 'user_id' in payload
    assert 'role' in payload
    assert 'exp' in payload
    assert payload['user_id'] == user.id
    assert payload['role'] == user.role

def test_expired_token_rejected():
    """测试过期 token 被拒绝"""
    user = create_test_user()
    # 生成一个已过期的 token
    token = generate_jwt_token(
        user,
        expires_delta=timedelta(seconds=-1)
    )
    
    # 尝试使用过期 token
    with pytest.raises(AuthenticationError) as exc_info:
        verify_jwt_token(token)
    
    assert 'expired' in str(exc_info.value).lower()
```

### 集成测试示例

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
def admin_token(client):
    """获取管理员 token"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    return response.json()['data']['access_token']

def test_create_segment_workflow(client, admin_token):
    """测试创建网段的完整流程"""
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    # 1. 创建网段
    response = client.post('/api/v1/segments', json={
        'name': 'Test Segment',
        'network': '192.168.100.0',
        'prefix_length': 24,
        'description': 'Test segment'
    }, headers=headers)
    
    assert response.status_code == 201
    segment_id = response.json()['data']['id']
    
    # 2. 查询网段
    response = client.get(f'/api/v1/segments/{segment_id}', headers=headers)
    assert response.status_code == 200
    assert response.json()['data']['name'] == 'Test Segment'
    
    # 3. 分配 IP
    response = client.post('/api/v1/ips/allocate', json={
        'ip_address': '192.168.100.10',
        'segment_id': segment_id,
        'device_id': 1
    }, headers=headers)
    
    assert response.status_code == 201
    
    # 4. 尝试删除网段（应该失败，因为有已分配的 IP）
    response = client.delete(f'/api/v1/segments/{segment_id}', headers=headers)
    assert response.status_code == 400
    assert 'allocated' in response.json()['message'].lower()
```

### 测试配置

#### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --hypothesis-show-statistics
markers =
    unit: Unit tests
    property: Property-based tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

#### Hypothesis 配置

```python
from hypothesis import settings, Verbosity

# 配置 Hypothesis
settings.register_profile("default", max_examples=100)
settings.register_profile("ci", max_examples=1000)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)

# 加载配置
settings.load_profile(os.getenv('HYPOTHESIS_PROFILE', 'default'))
```

### 测试覆盖率目标

- 单元测试代码覆盖率：≥ 80%
- 关键业务逻辑覆盖率：≥ 90%
- 所有正确性属性必须有对应的属性测试
- 每个 API 端点必须有集成测试

### 持续集成

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: testpass
          MYSQL_DATABASE: ipam_test
        ports:
          - 3306:3306
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/unit -m unit
      
      - name: Run property tests
        run: pytest tests/property -m property
        env:
          HYPOTHESIS_PROFILE: ci
      
      - name: Run integration tests
        run: pytest tests/integration -m integration
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### 测试数据管理

```python
# tests/fixtures/database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope='session')
def test_db():
    """创建测试数据库"""
    engine = create_engine('mysql://root:testpass@localhost/ipam_test')
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db):
    """创建数据库会话"""
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.rollback()
    session.close()

# tests/fixtures/sample_data.py
from factory import Factory, Faker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db_session
    
    username = Faker('user_name')
    email = Faker('email')
    full_name = Faker('name')
    role = 'regular_user'

class NetworkSegmentFactory(SQLAlchemyModelFactory):
    class Meta:
        model = NetworkSegment
        sqlalchemy_session = db_session
    
    name = Faker('word')
    network = '192.168.1.0'
    prefix_length = 24
    created_by = SubFactory(UserFactory)
```



## 安全实现细节

### 密码加密

```python
from passlib.context import CryptContext

# 使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)
```

### JWT Token 实现

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise AuthenticationError("Invalid token")
```

### 权限装饰器

```python
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        user = get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def require_role(*allowed_roles):
    """角色权限装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required roles: {allowed_roles}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.post("/api/v1/segments")
@require_role("admin")
async def create_segment(
    segment: NetworkSegmentCreate,
    current_user: User = Depends(get_current_user)
):
    # 只有管理员可以创建网段
    pass
```

### SQL 注入防护

```python
# 使用 SQLAlchemy ORM 的参数化查询
from sqlalchemy import select

# ✅ 安全：使用参数化查询
def get_device_by_mac(mac_address: str):
    stmt = select(Device).where(Device.mac_address == mac_address)
    return db.execute(stmt).scalar_one_or_none()

# ❌ 不安全：字符串拼接（永远不要这样做）
def get_device_by_mac_unsafe(mac_address: str):
    query = f"SELECT * FROM devices WHERE mac_address = '{mac_address}'"
    return db.execute(query)
```

### XSS 防护

```python
from html import escape

def sanitize_input(text: str) -> str:
    """清理用户输入，防止 XSS"""
    return escape(text)

# 在 Pydantic 模型中使用
from pydantic import BaseModel, validator

class DeviceCreate(BaseModel):
    name: str
    description: str
    
    @validator('name', 'description')
    def sanitize_text(cls, v):
        return sanitize_input(v)
```

### 请求频率限制

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 应用到路由
@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # 每分钟最多 5 次登录尝试
async def login(request: Request, credentials: LoginRequest):
    # 登录逻辑
    pass

@app.post("/api/v1/ips/allocate")
@limiter.limit("100/minute")  # 每分钟最多 100 次 IP 分配
async def allocate_ip(request: Request, ip_request: IPAllocationRequest):
    # IP 分配逻辑
    pass
```

### CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # 开发环境
        "https://ipam.example.com"  # 生产环境
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 部署配置

### Docker Compose 配置

```yaml
version: '3.8'

services:
  # MySQL 数据库
  mysql:
    image: mysql:8.0
    container_name: ipam-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - ipam-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 后端 API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ipam-backend
    environment:
      DATABASE_URL: mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      JWT_ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - backend_logs:/app/logs
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - ipam-network
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # 前端应用
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ipam-frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_BASE_URL: http://localhost:8000/api/v1
    networks:
      - ipam-network
    command: npm run dev -- --host

  # Nginx 反向代理（生产环境）
  nginx:
    image: nginx:alpine
    container_name: ipam-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_dist:/usr/share/nginx/html
    depends_on:
      - backend
      - frontend
    networks:
      - ipam-network
    profiles:
      - production

volumes:
  mysql_data:
  backend_logs:
  frontend_dist:

networks:
  ipam-network:
    driver: bridge
```

### 后端 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 前端 Dockerfile

```dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 环境变量配置（.env）

```bash
# 数据库配置
MYSQL_ROOT_PASSWORD=your_root_password_here
MYSQL_DATABASE=ipam
MYSQL_USER=ipam_user
MYSQL_PASSWORD=your_password_here

# JWT 配置
JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 日志配置
LOG_LEVEL=INFO

# 应用配置
BACKEND_PORT=8000
FRONTEND_PORT=5173

# CORS 配置
ALLOWED_ORIGINS=http://localhost:5173,https://ipam.example.com
```

### 数据库初始化脚本（init.sql）

```sql
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ipam CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ipam;

-- 创建默认管理员用户
-- 密码：admin123（已使用 bcrypt 加密）
INSERT INTO users (username, hashed_password, email, full_name, role, is_active, created_at, updated_at)
VALUES (
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/1jrPK',
    'admin@example.com',
    'System Administrator',
    'admin',
    TRUE,
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE username=username;

-- 创建示例网段
INSERT INTO network_segments (name, network, prefix_length, description, usage_threshold, created_by, created_at, updated_at)
VALUES (
    'Default Network',
    '192.168.1.0',
    24,
    'Default network segment',
    80,
    1,
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE name=name;
```

### Nginx 配置（生产环境）

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name ipam.example.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ipam.example.com;

    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 日志配置
    access_log /var/log/nginx/ipam_access.log;
    error_log /var/log/nginx/ipam_error.log;
}
```

### 部署步骤

#### 开发环境

```bash
# 1. 克隆代码
git clone https://github.com/your-org/ipam-system.git
cd ipam-system

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置密码和密钥

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 访问应用
# 前端：http://localhost:5173
# 后端 API：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

#### 生产环境

```bash
# 1. 准备服务器
# - 安装 Docker 和 Docker Compose
# - 配置防火墙规则
# - 准备 SSL 证书

# 2. 配置环境变量
cp .env.example .env
# 设置强密码和随机密钥

# 3. 构建生产镜像
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# 4. 启动生产服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d

# 5. 初始化数据库
docker-compose exec backend alembic upgrade head

# 6. 验证服务状态
docker-compose ps
curl https://ipam.example.com/api/v1/health

# 7. 配置备份任务
# 添加 cron 任务定期备份数据库
0 2 * * * /usr/local/bin/backup-ipam-db.sh
```

### 监控和维护

#### 健康检查端点

```python
@app.get("/api/v1/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": db_status,
            "api": "healthy"
        }
    }
```

#### 数据库备份脚本

```bash
#!/bin/bash
# backup-ipam-db.sh

BACKUP_DIR="/var/backups/ipam"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ipam_backup_$DATE.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
docker-compose exec -T mysql mysqldump \
    -u root \
    -p$MYSQL_ROOT_PASSWORD \
    ipam > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 删除 30 天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

#### 日志轮转配置

```bash
# /etc/logrotate.d/ipam
/var/log/ipam/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker-compose restart backend
    endscript
}
```

