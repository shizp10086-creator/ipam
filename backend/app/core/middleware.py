"""
Security Middleware
提供安全相关的中间件功能
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求频率限制中间件
    防止暴力破解和 DDoS 攻击
    """

    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        初始化频率限制中间件

        Args:
            app: FastAPI 应用实例
            calls: 时间窗口内允许的最大请求数
            period: 时间窗口（秒）
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)

        # 登录端点的特殊限制
        self.login_calls = 20
        self.login_period = 300  # 5 分钟
        self.login_clients = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并应用频率限制
        """
        # 获取客户端 IP
        client_ip = request.client.host

        # 检查是否是登录端点
        is_login = request.url.path.endswith('/login')

        if is_login:
            # 登录端点使用更严格的限制
            if not self._check_rate_limit(
                client_ip,
                self.login_clients,
                self.login_calls,
                self.login_period
            ):
                logger.warning(f"Rate limit exceeded for login from {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many login attempts. Please try again later."
                    }
                )
        else:
            # 普通端点使用标准限制
            if not self._check_rate_limit(
                client_ip,
                self.clients,
                self.calls,
                self.period
            ):
                logger.warning(f"Rate limit exceeded from {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many requests. Please slow down."
                    }
                )

        response = await call_next(request)
        return response

    def _check_rate_limit(
        self,
        client_ip: str,
        clients_dict: dict,
        max_calls: int,
        period: int
    ) -> bool:
        """
        检查客户端是否超过频率限制

        Returns:
            True 如果在限制内，False 如果超过限制
        """
        now = time.time()

        # 清理过期的请求记录
        clients_dict[client_ip] = [
            req_time for req_time in clients_dict[client_ip]
            if now - req_time < period
        ]

        # 检查是否超过限制
        if len(clients_dict[client_ip]) >= max_calls:
            return False

        # 记录当前请求
        clients_dict[client_ip].append(now)
        return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全响应头中间件
    添加安全相关的 HTTP 响应头
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        添加安全响应头
        """
        response = await call_next(request)

        # XSS 防护
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HTTPS 强制（生产环境）
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 内容安全策略
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # 引用策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class SecurityLogMiddleware(BaseHTTPMiddleware):
    """
    安全日志中间件
    记录可疑活动和安全事件
    """

    def __init__(self, app):
        super().__init__(app)
        self.failed_login_attempts = defaultdict(list)
        self.suspicious_threshold = 3
        self.time_window = 300  # 5 分钟

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        记录安全相关的请求
        """
        client_ip = request.client.host
        path = request.url.path
        method = request.method

        # 记录请求开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录登录失败
        if path.endswith('/login') and response.status_code == 401:
            self._log_failed_login(client_ip)

        # 记录权限违规
        if response.status_code == 403:
            logger.warning(
                f"Permission denied: {method} {path} from {client_ip}"
            )

        # 记录异常慢的请求（可能是攻击）
        if process_time > 10:
            logger.warning(
                f"Slow request detected: {method} {path} from {client_ip} "
                f"took {process_time:.2f}s"
            )

        return response

    def _log_failed_login(self, client_ip: str):
        """
        记录登录失败并检测可疑活动
        """
        now = time.time()

        # 清理过期记录
        self.failed_login_attempts[client_ip] = [
            attempt_time for attempt_time in self.failed_login_attempts[client_ip]
            if now - attempt_time < self.time_window
        ]

        # 记录当前失败
        self.failed_login_attempts[client_ip].append(now)

        # 检查是否达到可疑阈值
        if len(self.failed_login_attempts[client_ip]) >= self.suspicious_threshold:
            logger.error(
                f"SECURITY ALERT: Multiple failed login attempts from {client_ip}. "
                f"Count: {len(self.failed_login_attempts[client_ip])} "
                f"in last {self.time_window}s"
            )


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    请求验证中间件
    验证请求的基本安全性
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        验证请求
        """
        # 检查请求大小（防止大文件攻击）
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                # 限制请求大小为 10MB（除了导入端点）
                max_size = 10 * 1024 * 1024
                if size > max_size and not request.url.path.endswith('/import'):
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Request entity too large"}
                    )
            except ValueError:
                pass

        # 检查 User-Agent（基本的机器人检测）
        user_agent = request.headers.get('user-agent', '')
        if not user_agent and request.url.path not in ['/health', '/']:
            logger.warning(f"Request without User-Agent from {request.client.host}")

        response = await call_next(request)
        return response


class TraceIDMiddleware(BaseHTTPMiddleware):
    """
    链路追踪中间件。

    为每个请求生成唯一 TraceID，贯穿整个请求生命周期。
    TraceID 会出现在：响应头、日志、统一响应体中。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        from app.core.response import trace_id_var

        # 优先使用客户端传入的 TraceID，否则自动生成
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))

        # 设置到上下文变量（供 APIResponse 使用）
        token = trace_id_var.set(trace_id)

        try:
            response = await call_next(request)
            # 在响应头中返回 TraceID
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            trace_id_var.reset(token)


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """
    响应时间记录中间件。

    在响应头中添加 X-Process-Time，便于性能监控。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response
