"""
统一 API 响应格式。

所有 API 返回统一的 JSON 结构：
{
    "code": 200,
    "message": "success",
    "data": {},
    "trace_id": "abc-123",
    "timestamp": "2026-01-01T00:00:00Z"
}
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from contextvars import ContextVar
from pydantic import BaseModel

# 请求级别的 TraceID 上下文变量
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class APIResponse(BaseModel):
    """统一 API 响应模型"""
    code: int = 200
    message: str = "success"
    data: Any = None
    trace_id: str = ""
    timestamp: str = ""

    @classmethod
    def success(cls, data: Any = None, message: str = "success", code: int = 200) -> dict:
        """成功响应"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "trace_id": trace_id_var.get(""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def error(
        cls,
        message: str = "error",
        code: int = 400,
        data: Any = None,
    ) -> dict:
        """错误响应"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "trace_id": trace_id_var.get(""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def paginated(
        cls,
        items: list,
        total: int,
        cursor: Optional[str] = None,
        has_more: bool = False,
    ) -> dict:
        """分页响应（游标分页）"""
        return cls.success(
            data={
                "items": items,
                "total": total,
                "cursor": cursor,
                "has_more": has_more,
            }
        )


def generate_trace_id() -> str:
    """生成唯一的 TraceID。"""
    return str(uuid.uuid4())
