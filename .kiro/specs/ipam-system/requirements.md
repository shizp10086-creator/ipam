# 需求文档：轻量版 IP 地址管理系统（IPAM）

## 简介

本系统是一个轻量级的 IP 地址管理系统（IPAM），旨在为中小型网络环境提供完整的 IP 地址生命周期管理、设备资产管理、操作审计和可视化分析功能。系统采用前后端分离架构，支持 Docker 容器化部署，适合新手开发者学习和实际生产环境使用。

## 术语表

- **IPAM_System**: IP 地址管理系统，本文档描述的核心系统
- **Network_Segment**: 网段，一个连续的 IP 地址范围（如 192.168.1.0/24）
- **IP_Address**: IP 地址，网络中设备的唯一标识符
- **Device**: 设备，网络中的物理或虚拟设备
- **User**: 用户，系统的使用者
- **Administrator**: 管理员，拥有完整系统权限的用户角色
- **Regular_User**: 普通用户，拥有基本操作权限的用户角色
- **ReadOnly_User**: 只读用户，仅能查看数据的用户角色
- **Operation_Log**: 操作日志，记录系统中所有关键操作的审计记录
- **JWT_Token**: JSON Web Token，用于用户身份认证的令牌
- **Allocation_Status**: 分配状态，IP 地址的使用状态（空闲/已用/保留）
- **Conflict_Detection**: 冲突检测，检查 IP 地址是否存在逻辑或物理冲突
- **Usage_Threshold**: 使用率阈值，触发告警的网段使用率百分比
- **Ping_Scanner**: Ping 扫描器，用于检测 IP 地址存活状态的工具
- **ARP_Protocol**: 地址解析协议，用于检测 IP 与 MAC 地址映射关系

## 需求

### 需求 1：网段管理

**用户故事：** 作为管理员，我希望能够创建、编辑和删除网段，以便组织和管理不同的 IP 地址范围。

#### 验收标准

1. WHEN 管理员创建网段时，THE IPAM_System SHALL 验证网段格式（CIDR 表示法）并存储网段信息
2. WHEN 管理员编辑网段时，THE IPAM_System SHALL 更新网段信息并保持已分配 IP 地址的关联关系
3. WHEN 管理员删除网段时，THE IPAM_System SHALL 检查网段内是否存在已分配的 IP 地址
4. IF 网段内存在已分配的 IP 地址，THEN THE IPAM_System SHALL 拒绝删除操作并返回错误信息
5. THE IPAM_System SHALL 计算并显示每个网段的可用 IP 地址总数
6. THE IPAM_System SHALL 计算并显示每个网段的已用 IP 地址数量和使用率

### 需求 2：IP 地址生命周期管理

**用户故事：** 作为普通用户，我希望能够分配、回收和查询 IP 地址，以便管理网络资源的使用情况。

#### 验收标准

1. WHEN 用户分配 IP 地址时，THE IPAM_System SHALL 验证 IP 地址属于已存在的网段
2. WHEN 用户分配 IP 地址时，THE IPAM_System SHALL 执行双重冲突检测（逻辑和物理）
3. WHEN 用户回收 IP 地址时，THE IPAM_System SHALL 将 IP 地址状态更改为"空闲"并解除设备关联
4. THE IPAM_System SHALL 支持三种 IP 地址状态：空闲（Available）、已用（Used）、保留（Reserved）
5. WHEN 用户查询 IP 地址时，THE IPAM_System SHALL 返回 IP 地址的当前状态、关联设备和历史操作记录
6. WHEN 用户手动标记 IP 为保留状态时，THE IPAM_System SHALL 阻止该 IP 被自动分配

### 需求 3：设备资产管理

**用户故事：** 作为普通用户，我希望能够录入和管理设备信息，以便追踪网络中的设备资产。

#### 验收标准

1. WHEN 用户创建设备记录时，THE IPAM_System SHALL 要求提供设备名称、MAC 地址和责任人信息
2. THE IPAM_System SHALL 验证 MAC 地址格式的有效性
3. WHEN 用户关联设备与 IP 地址时，THE IPAM_System SHALL 验证 IP 地址处于可分配状态
4. WHEN 用户编辑设备信息时，THE IPAM_System SHALL 保持设备与 IP 地址的关联关系
5. WHEN 用户删除设备时，THE IPAM_System SHALL 自动回收该设备关联的所有 IP 地址
6. THE IPAM_System SHALL 支持按设备名称、MAC 地址、责任人进行模糊搜索

### 需求 4：双重 IP 冲突检测

**用户故事：** 作为系统管理员，我希望系统能够自动检测 IP 地址冲突，以便避免网络配置错误。

#### 验收标准

1. WHEN 用户尝试分配 IP 地址时，THE IPAM_System SHALL 首先执行逻辑冲突检测
2. THE IPAM_System SHALL 在数据库中查询该 IP 地址是否已被标记为"已用"或"保留"
3. IF 逻辑冲突检测通过，THEN THE IPAM_System SHALL 执行物理冲突检测
4. THE IPAM_System SHALL 通过 Ping 或 ARP 协议检测 IP 地址在网络中的实际使用状态
5. IF 物理冲突检测发现 IP 已被使用，THEN THE IPAM_System SHALL 拒绝分配并记录冲突信息
6. THE IPAM_System SHALL 在冲突检测失败时返回详细的错误信息（逻辑冲突或物理冲突）

### 需求 5：IP Ping 扫描

**用户故事：** 作为网络管理员，我希望能够批量扫描网段内的 IP 地址存活状态，以便发现未注册的设备或验证 IP 使用情况。

#### 验收标准

1. WHEN 用户启动 Ping 扫描时，THE IPAM_System SHALL 允许用户选择要扫描的网段
2. THE IPAM_System SHALL 并发执行 Ping 操作以提高扫描效率
3. WHEN 扫描进行时，THE IPAM_System SHALL 实时更新扫描进度和结果
4. THE IPAM_System SHALL 记录每个 IP 地址的响应状态（在线/离线）和响应时间
5. WHEN 扫描完成时，THE IPAM_System SHALL 生成扫描报告并标识未注册的在线 IP
6. THE IPAM_System SHALL 将扫描结果持久化存储并支持历史扫描记录查询

### 需求 6：操作日志记录

**用户故事：** 作为审计人员，我希望系统能够记录所有关键操作，以便追踪变更历史和问题排查。

#### 验收标准

1. WHEN 用户执行 IP 分配操作时，THE IPAM_System SHALL 记录操作人、操作时间、IP 地址和关联设备
2. WHEN 用户执行 IP 回收操作时，THE IPAM_System SHALL 记录操作人、操作时间和 IP 地址
3. WHEN 用户创建、编辑或删除设备时，THE IPAM_System SHALL 记录完整的操作详情
4. WHEN 用户创建、编辑或删除网段时，THE IPAM_System SHALL 记录网段信息和操作类型
5. THE IPAM_System SHALL 支持按操作人、操作类型、时间范围筛选日志
6. THE IPAM_System SHALL 保证日志记录的不可篡改性

### 需求 7：数据可视化展示

**用户故事：** 作为管理员，我希望通过图表直观地了解网络资源使用情况，以便做出合理的资源规划决策。

#### 验收标准

1. THE IPAM_System SHALL 显示所有网段的使用率柱状图或饼图
2. THE IPAM_System SHALL 显示 IP 地址状态分布图（空闲/已用/保留）
3. THE IPAM_System SHALL 显示设备数量统计和增长趋势图
4. THE IPAM_System SHALL 在仪表板上显示关键指标（总 IP 数、已用 IP 数、设备总数）
5. WHEN 用户访问仪表板时，THE IPAM_System SHALL 实时计算并更新统计数据
6. THE IPAM_System SHALL 支持按时间范围筛选统计数据

### 需求 8：Excel 导入导出

**用户故事：** 作为数据管理员，我希望能够批量导入和导出数据，以便快速迁移数据或进行离线分析。

#### 验收标准

1. THE IPAM_System SHALL 提供 Excel 模板下载功能，包含必填字段说明
2. WHEN 用户上传 Excel 文件时，THE IPAM_System SHALL 验证文件格式和数据完整性
3. THE IPAM_System SHALL 在导入前执行数据校验（IP 格式、MAC 格式、必填字段）
4. IF 导入数据存在错误，THEN THE IPAM_System SHALL 返回详细的错误报告并拒绝导入
5. WHEN 用户导出数据时，THE IPAM_System SHALL 生成包含所有字段的 Excel 文件
6. THE IPAM_System SHALL 支持导出筛选后的数据子集

### 需求 9：网段使用率告警

**用户故事：** 作为网络管理员，我希望在网段使用率达到阈值时收到告警，以便及时扩容或调整资源分配。

#### 验收标准

1. THE IPAM_System SHALL 允许管理员为每个网段设置使用率告警阈值（百分比）
2. WHEN 网段使用率达到或超过阈值时，THE IPAM_System SHALL 生成告警记录
3. THE IPAM_System SHALL 在用户界面显示告警通知
4. THE IPAM_System SHALL 记录告警历史，包括触发时间、网段信息和使用率
5. WHEN 网段使用率降低到阈值以下时，THE IPAM_System SHALL 自动解除告警状态
6. THE IPAM_System SHALL 支持查询和筛选历史告警记录

### 需求 10：用户认证与 JWT 鉴权

**用户故事：** 作为系统用户，我希望通过安全的方式登录系统，以便保护我的账户和数据安全。

#### 验收标准

1. WHEN 用户提交登录凭证时，THE IPAM_System SHALL 验证用户名和密码的正确性
2. IF 凭证验证成功，THEN THE IPAM_System SHALL 生成 JWT_Token 并返回给客户端
3. THE IPAM_System SHALL 在 JWT_Token 中包含用户 ID、角色和过期时间信息
4. WHEN 用户访问受保护的 API 端点时，THE IPAM_System SHALL 验证 JWT_Token 的有效性
5. IF JWT_Token 过期，THEN THE IPAM_System SHALL 拒绝请求并返回 401 未授权错误
6. THE IPAM_System SHALL 提供 Token 刷新机制，允许用户在 Token 过期前获取新 Token
7. WHEN 用户登出时，THE IPAM_System SHALL 使客户端的 JWT_Token 失效

### 需求 11：RBAC 基础权限控制

**用户故事：** 作为系统管理员，我希望能够为不同用户分配不同的角色和权限，以便实现细粒度的访问控制。

#### 验收标准

1. THE IPAM_System SHALL 支持三种预定义角色：Administrator、Regular_User、ReadOnly_User
2. THE IPAM_System SHALL 允许 Administrator 执行所有操作（创建、读取、更新、删除）
3. THE IPAM_System SHALL 允许 Regular_User 执行 IP 分配、回收、设备管理等日常操作
4. THE IPAM_System SHALL 限制 Regular_User 不能创建或删除网段、不能管理用户
5. THE IPAM_System SHALL 限制 ReadOnly_User 仅能查看数据，不能执行任何修改操作
6. WHEN 用户尝试执行超出其权限的操作时，THE IPAM_System SHALL 返回 403 禁止访问错误
7. THE IPAM_System SHALL 在操作日志中记录用户的角色信息

### 需求 12：系统部署与配置

**用户故事：** 作为运维人员，我希望系统能够通过 Docker 快速部署，以便简化安装和维护流程。

#### 验收标准

1. THE IPAM_System SHALL 提供完整的 Docker Compose 配置文件
2. THE IPAM_System SHALL 支持通过环境变量配置数据库连接、JWT 密钥等关键参数
3. WHEN 运维人员执行 docker-compose up 命令时，THE IPAM_System SHALL 自动启动所有服务
4. THE IPAM_System SHALL 在首次启动时自动初始化数据库表结构
5. THE IPAM_System SHALL 在首次启动时创建默认管理员账户
6. THE IPAM_System SHALL 提供健康检查端点，用于监控服务状态
7. THE IPAM_System SHALL 支持在 Windows 10 和 Linux 环境中运行

### 需求 13：数据持久化与备份

**用户故事：** 作为数据管理员，我希望系统数据能够可靠存储并支持备份恢复，以便防止数据丢失。

#### 验收标准

1. THE IPAM_System SHALL 使用 MySQL 8.0 作为持久化存储引擎
2. THE IPAM_System SHALL 使用事务确保数据操作的原子性
3. WHEN 执行关键操作时，THE IPAM_System SHALL 在事务失败时自动回滚
4. THE IPAM_System SHALL 支持数据库连接池以提高并发性能
5. THE IPAM_System SHALL 在 Docker 容器中使用数据卷持久化数据库文件
6. THE IPAM_System SHALL 提供数据库备份和恢复的操作指南

### 需求 14：API 接口设计

**用户故事：** 作为前端开发者，我希望后端提供清晰、一致的 RESTful API，以便快速集成功能。

#### 验收标准

1. THE IPAM_System SHALL 遵循 RESTful API 设计规范
2. THE IPAM_System SHALL 使用标准 HTTP 状态码表示操作结果（200、201、400、401、403、404、500）
3. THE IPAM_System SHALL 返回统一格式的 JSON 响应（包含 code、message、data 字段）
4. THE IPAM_System SHALL 提供 OpenAPI（Swagger）文档，描述所有 API 端点
5. WHEN API 请求参数验证失败时，THE IPAM_System SHALL 返回详细的错误信息
6. THE IPAM_System SHALL 支持跨域资源共享（CORS）以允许前端访问

### 需求 15：前端用户界面

**用户故事：** 作为最终用户，我希望系统界面友好、响应迅速，以便高效完成工作任务。

#### 验收标准

1. THE IPAM_System SHALL 使用 Vue 3 和 Element Plus 构建响应式用户界面
2. THE IPAM_System SHALL 在所有主要操作上提供即时反馈（加载动画、成功/错误提示）
3. THE IPAM_System SHALL 支持表格数据的分页、排序和筛选
4. THE IPAM_System SHALL 在表单提交前进行客户端验证
5. WHEN 网络请求失败时，THE IPAM_System SHALL 显示友好的错误提示
6. THE IPAM_System SHALL 支持深色和浅色主题切换
7. THE IPAM_System SHALL 在移动设备上提供可用的响应式布局

### 需求 16：性能与可扩展性

**用户故事：** 作为系统架构师，我希望系统能够处理合理规模的数据量并保持良好性能，以便满足生产环境需求。

#### 验收标准

1. THE IPAM_System SHALL 支持管理至少 10,000 个 IP 地址
2. THE IPAM_System SHALL 在 1 秒内完成单个 IP 地址的分配操作
3. THE IPAM_System SHALL 在 5 秒内完成包含 256 个 IP 的网段扫描
4. THE IPAM_System SHALL 使用数据库索引优化查询性能
5. THE IPAM_System SHALL 对频繁访问的数据实施缓存策略
6. WHEN 并发用户数达到 50 时，THE IPAM_System SHALL 保持响应时间在 2 秒以内

### 需求 17：错误处理与日志记录

**用户故事：** 作为运维人员，我希望系统能够记录详细的错误日志，以便快速定位和解决问题。

#### 验收标准

1. THE IPAM_System SHALL 记录所有未捕获的异常到日志文件
2. THE IPAM_System SHALL 在日志中包含时间戳、日志级别、模块名称和详细错误信息
3. THE IPAM_System SHALL 使用不同的日志级别（DEBUG、INFO、WARNING、ERROR、CRITICAL）
4. THE IPAM_System SHALL 支持日志文件自动轮转，防止日志文件过大
5. WHEN 发生严重错误时，THE IPAM_System SHALL 记录完整的堆栈跟踪信息
6. THE IPAM_System SHALL 在生产环境中默认使用 INFO 级别，开发环境使用 DEBUG 级别

### 需求 18：安全性要求

**用户故事：** 作为安全管理员，我希望系统能够防范常见的安全威胁，以便保护系统和数据安全。

#### 验收标准

1. THE IPAM_System SHALL 使用 bcrypt 或 Argon2 算法加密存储用户密码
2. THE IPAM_System SHALL 防止 SQL 注入攻击（使用参数化查询）
3. THE IPAM_System SHALL 防止跨站脚本攻击（XSS）（对用户输入进行转义）
4. THE IPAM_System SHALL 实施请求频率限制，防止暴力破解和 DDoS 攻击
5. THE IPAM_System SHALL 在传输敏感数据时使用 HTTPS 加密
6. THE IPAM_System SHALL 在 JWT_Token 中使用强加密算法（HS256 或 RS256）
7. WHEN 检测到可疑活动时，THE IPAM_System SHALL 记录安全日志并可选地锁定账户
