"""
Global Exception Handlers
全局异常处理器
"""
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器
    捕获所有未处理的异常并返回统一格式的错误响应
    """
    # 记录完整的堆栈跟踪
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}\n"
        f"Path: {request.method} {request.url.path}\n"
        f"Client: {request.client.host}\n"
        f"Traceback:\n{traceback.format_exc()}"
    )
    
    # 返回通用错误响应（不暴露内部错误详情）
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later."
        }
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
        content={
            "code": 422,
            "message": "Validation error",
            "detail": "Request validation failed",
            "errors": errors
        }
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
            content={
                "code": 409,
                "message": "Database constraint violation",
                "detail": "The operation violates a database constraint. "
                         "This may be due to duplicate data or foreign key constraints."
            }
        )
    
    # 其他数据库错误
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "Database error",
            "detail": "A database error occurred. Please try again later."
        }
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
        content={
            "code": 400,
            "message": "Invalid value",
            "detail": str(exc)
        }
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到 FastAPI 应用
    
    Args:
        app: FastAPI 应用实例
    """
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    
    logger.info("Exception handlers registered")
