"""
IPAM System - Main Application Entry Point
"""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.utils.db_init import initialize_database, check_database_connection
from app.core.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    SecurityLogMiddleware,
    RequestValidationMiddleware,
    TraceIDMiddleware,
    ResponseTimeMiddleware,
)
from app.core.tenant_middleware import TenantIsolationMiddleware
from app.core.exceptions import register_exception_handlers

# Configure logging
os.makedirs("logs", exist_ok=True)  # 确保日志目录存在
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log') if settings.ENVIRONMENT == 'production' else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info("Application startup: Initializing database...")

    # Check database connection
    if not check_database_connection():
        logger.error("Cannot connect to database. Please check your database configuration.")
        raise Exception("Database connection failed")

    # Run migrations and create default admin
    if not initialize_database():
        logger.error("Database initialization failed")
        raise Exception("Database initialization failed")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Application shutdown")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    # IP Address Management System (IPAM)

    轻量版 IP 地址管理系统，提供网段管理、IP 地址分配、设备管理等功能。

    ## 主要功能

    * **网段管理** - 创建、查询、更新、删除网段
    * **IP 地址管理** - IP 分配、回收、保留、冲突检测
    * **设备管理** - 设备资产管理和 IP 关联
    * **IP 扫描** - Ping 扫描网段内的 IP 地址
    * **告警管理** - 网段使用率告警
    * **操作日志** - 记录所有操作历史
    * **数据导入导出** - Excel 批量导入导出
    * **数据可视化** - 仪表板和统计图表

    ## 认证方式

    使用 JWT (JSON Web Token) 进行身份认证。

    1. 调用 `/api/v1/login` 端点获取 access_token
    2. 在后续请求的 Header 中添加：`Authorization: Bearer <access_token>`

    ## 用户角色

    * **Administrator** - 管理员，拥有所有权限
    * **Regular_User** - 普通用户，可以查看和操作 IP、设备
    * **ReadOnly_User** - 只读用户，只能查看数据

    ## 错误码

    * **200** - 成功
    * **201** - 创建成功
    * **400** - 请求参数错误
    * **401** - 未认证
    * **403** - 权限不足
    * **404** - 资源不存在
    * **409** - 资源冲突
    * **422** - 数据验证失败
    * **429** - 请求频率超限
    * **500** - 服务器内部错误
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "IPAM System",
        "email": "support@ipam.local"
    },
    license_info={
        "name": "MIT License"
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加中间件（注意顺序：最先添加的最后执行）
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(SecurityLogMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)
app.add_middleware(TenantIsolationMiddleware)
app.add_middleware(ResponseTimeMiddleware)
app.add_middleware(TraceIDMiddleware)

# Register exception handlers
register_exception_handlers(app)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring service status
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to IPAM System API",
        "docs": "/api/docs",
        "health": "/health"
    }


# Include API routers
from app.api import ip_addresses, devices, network_segments, users, auth, alerts, logs, dashboard, import_export, search, tenants, designer
from app.domains.dcim.api import router as dcim_router
from app.domains.collector.api import router as collector_router
from app.domains.nac.api import router as nac_router
from app.domains.nac.radius_api import router as radius_router
from app.domains.collab.api import router as collab_router
from app.domains.collab.change_api import router as change_router
from app.domains.asset.lifecycle_api import router as lifecycle_router
from app.domains.auth.integration_api import router as integration_router
from app.domains.ipam.data_governance_api import router as governance_router
from app.domains.asset.terminal_api import router as terminal_router
from app.domains.ticket.api import router as ticket_router
from app.domains.ai.api import router as ai_router
from app.domains.value.api import router as value_router
from app.domains.ai.ppt_api import router as ppt_router

app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(designer.router, prefix="/api/v1/designer", tags=["Designer"])
app.include_router(dcim_router, prefix="/api/v1/dcim", tags=["DCIM"])
app.include_router(collector_router, prefix="/api/v1/collector", tags=["Collector"])
app.include_router(nac_router, prefix="/api/v1/nac", tags=["NAC"])
app.include_router(radius_router, prefix="/api/v1/nac", tags=["RADIUS"])
app.include_router(collab_router, prefix="/api/v1/collab", tags=["Collaboration"])
app.include_router(change_router, prefix="/api/v1/collab", tags=["Change Management"])
app.include_router(lifecycle_router, prefix="/api/v1/assets", tags=["Asset Lifecycle"])
app.include_router(integration_router, prefix="/api/v1/auth", tags=["Integrations"])
app.include_router(governance_router, prefix="/api/v1/governance", tags=["Data Governance"])
app.include_router(terminal_router, prefix="/api/v1/assets", tags=["Terminals"])
app.include_router(ticket_router, prefix="/api/v1/tickets", tags=["Tickets"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(value_router, prefix="/api/v1/value", tags=["IT Value"])
app.include_router(ppt_router, prefix="/api/v1/ppt", tags=["PPT"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(ip_addresses.router, prefix="/api/v1/ips", tags=["IP Addresses"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(network_segments.router, prefix="/api/v1/segments", tags=["Network Segments"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["Operation Logs"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(import_export.router, prefix="/api/v1/import-export", tags=["Import/Export"])
