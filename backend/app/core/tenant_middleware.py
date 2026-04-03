"""
租户隔离中间件。

从 JWT Token 中提取 tenant_id，注入到请求上下文中。
所有数据库查询自动附加 tenant_id 条件，确保租户间数据完全隔离。

设计思路：
- 用 ContextVar 存储当前请求的 tenant_id，Service 层通过 get_current_tenant_id() 获取
- 超级管理员（tenant_id=None 或 role=superadmin）可以跨租户查询
- 公共接口（如 /health、/api/docs）不需要租户隔离，通过白名单跳过
"""
import logging
from typing import Optional
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# 当前请求的租户 ID 上下文变量
current_tenant_id: ContextVar[Optional[int]] = ContextVar("current_tenant_id", default=None)
# 当前请求的用户 ID
current_user_id: ContextVar[Optional[int]] = ContextVar("current_user_id", default=None)
# 当前请求的用户角色
current_user_role: ContextVar[Optional[str]] = ContextVar("current_user_role", default=None)

# 不需要租户隔离的路径白名单
TENANT_BYPASS_PATHS = {
    "/", "/health", "/api/docs", "/api/redoc", "/api/openapi.json",
    "/api/v1/login", "/api/v1/auth/login", "/api/v1/token/refresh", "/api/v1/auth/refresh",
}


def get_current_tenant_id() -> Optional[int]:
    """获取当前请求的租户 ID。Service 层调用此函数获取租户上下文。"""
    return current_tenant_id.get(None)


def get_current_user_id() -> Optional[int]:
    """获取当前请求的用户 ID。"""
    return current_user_id.get(None)


def get_current_user_role() -> Optional[str]:
    """获取当前请求的用户角色。"""
    return current_user_role.get(None)


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    租户隔离中间件。

    工作流程：
    1. 从请求头 Authorization 中解析 JWT Token
    2. 从 Token payload 中提取 tenant_id、user_id、role
    3. 设置到 ContextVar 中
    4. 后续的 Service/Repository 层通过 get_current_tenant_id() 获取
    5. 所有查询自动附加 WHERE tenant_id = ?
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 白名单路径跳过
        if request.url.path in TENANT_BYPASS_PATHS:
            return await call_next(request)

        # 从请求头获取 Token（如果有的话）
        auth_header = request.headers.get("Authorization", "")
        tenant_id = None
        user_id = None
        user_role = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                from app.core.security import verify_token
                payload = verify_token(token, token_type="access")
                if payload:
                    tenant_id = payload.get("tenant_id", 1)  # 默认租户 1
                    user_id = int(payload.get("sub", 0)) if payload.get("sub") else None
                    user_role = payload.get("role")
            except Exception:
                pass  # Token 无效时不设置租户，后续认证中间件会拦截

        # 设置上下文变量
        t_token = current_tenant_id.set(tenant_id)
        u_token = current_user_id.set(user_id)
        r_token = current_user_role.set(user_role)

        try:
            response = await call_next(request)
            return response
        finally:
            current_tenant_id.reset(t_token)
            current_user_id.reset(u_token)
            current_user_role.reset(r_token)
