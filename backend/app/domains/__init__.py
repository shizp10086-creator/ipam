"""
Domain Services Layer

Organized by bounded contexts following DDD principles.
Each domain has its own models, schemas, services, and API routes.

Domains:
- auth: 认证鉴权与多租户 (需求 10, 11, 22, 30, 132)
- ipam: IP 地址管理核心 (需求 1-5, 9, 20, 21, 50-52, 67, 70, 73, 111)
- dcim: 数据中心基础设施 (需求 31-35, 47, 163)
- nac: 网络准入控制 (需求 37-44, 102-106)
- asset: 资产管理 (需求 3, 48, 71, 76-81, 95-99, 116-126)
- collector: 数据采集引擎 (需求 83-87, 149)
- monitor: 监控展示 (需求 7, 82, 88-93, 63)
- alert: 告警与预警 (需求 9, 36, 94, 161-162)
- ticket: 工单与ITSM (需求 45, 64-66, 100, 108-109, 135-145)
- ai: AI 智能分析 (需求 59, 152, 167, 181)
- audit: 合规审计 (需求 6, 23, 43, 53-54, 72, 115, 153-154, 168)
- lowcode: 低代码平台 (需求 15, 26, 129, 131, 164-165)
- netauto: 网络自动化 (需求 19, 46, 124, 133-134, 140, 159)
- value: IT 价值量化 (需求 109, 169, 171-180)
- collab: 运维协作 (需求 58, 74-75, 101, 107, 112-114, 127-128, 147, 160, 170)
"""
