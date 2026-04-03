"""
全局异常处理器。
统一使用 APIResponse 格式返回错误信息。
"""
import logging
import traceback
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from app.core.response import APIResponse

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器
    捕获所有未处理的异常并返回统一格式的错误响应
    注意：HTTPException 由 FastAPI 内置处理器处理，不会进入此处
    """
    # 如果是 HTTPException，交给 FastAPI 内置处理器
    if isinstance(exc, HTTPException):
        raise exc

    # 记录完整的堆栈跟踪
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}\n"
        f"Path: {request.method} {request.url.path}\n"
        f"Client: {request.client.host}\n"
        f"Traceback:\n{traceback.format_exc()}"
    )

    # 返回统一格式错误响应（不暴露内部错误详情）
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse.error(
            code=500,
            message="服务器内部错误，请稍后重试",
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    请求验证异常处理器
    处理 Pydantic 验证错误
    """
    logger.warning(
        f"Validation error: {request.method} {request.url.path}\n"
        f"Client: {request.client.host}\n"
        f"Errors: {exc.errors()}"
    )

    # 格式化验证错误
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=APIResponse.error(
            code=422,
            message="请求参数验证失败",
            data={"errors": errors},
        )
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    数据库异常处理器
    处理 SQLAlchemy 数据库错误
    """
    logger.error(
        f"Database error: {type(exc).__name__}: {str(exc)}\n"
        f"Path: {request.method} {request.url.path}\n"
        f"Client: {request.client.host}\n"
        f"Traceback:\n{traceback.format_exc()}"
    )

    # 检查是否是完整性约束错误
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=APIResponse.error(
                code=409,
                message="数据约束冲突，可能存在重复数据或外键约束",
            )
        )

    # 其他数据库错误
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse.error(
            code=500,
            message="数据库错误，请稍后重试",
        )
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    值错误处理器
    处理 ValueError 异常
    """
    logger.warning(
        f"Value error: {str(exc)}\n"
        f"Path: {request.method} {request.url.path}\n"
        f"Client: {request.client.host}"
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=APIResponse.error(
            code=400,
            message=str(exc),
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP 异常处理器
    确保 HTTPException（如 401、403）正常返回给前端，
    不会被全局 Exception 处理器拦截为 500 错误
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    # 注意：HTTPException 处理器必须在 Exception 之前注册，
    # 确保 401/403 等认证错误不会被全局处理器吞掉
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)

    logger.info("Exception handlers registered")
