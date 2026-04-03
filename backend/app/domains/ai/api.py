"""
AI 智能分析API

多模型适配+ AI 对话 + 智能搜索 + 知识库问答
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = None  # 上下文（如当前查看的设备/IP
    model: Optional[str] = None  # 指定模型（默认自动选择

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


# ==================== AI 对话 ====================

@router.post("/chat", summary="AI 运维助手对话")
async def ai_chat(data: ChatRequest):
    """
    AI 运维助手。支持自然语言查询资源状态、获取配置建议、分析异常事件

    当前为模拟实现，后续对接真实 LLM（OpenAI/DeepSeek/通义等）
    """
    # 简单的意图识别和模拟回
    msg = data.message.lower()

    if "ip" in msg and ("分配" in msg or "申请" in msg):
        reply = "您可以通过以下步骤分配 IP：\n1. 进入 IP 管理 > 网段管理\n2. 选择目标网段\n3. 点击「分配 IP」按钮\n4. 选择手动指定或自动分配"
    elif "告警" in msg:
        reply = "当前系统告警情况：\n- 您可以在「告警中心」查看所有告警\n- 支持按级别（警告/严重）筛选\n- 告警处理后可填写处理备注"
    elif "网段" in msg and "使用" in msg:
        reply = "网段使用率可以在以下位置查看：\n1. IP 管理 网段管理（列表中显示使用率）\n2. 运维仪表盘（使用率柱状图）\n3. IP 矩阵视图（颜色直观展示）"
    elif "故障" in msg or "排查" in msg:
        reply = "故障排查建议：\n1. 检查告警中心是否有相关告警\n2. 查看操作日志确认最近变更\n3. 使用 Ping 扫描检测设备在线状态\n4. 查看网络拓扑确认链路状态"
    else:
        reply = f"收到您的问题：「{data.message}」\n\nAI 分析引擎正在处理..\n（当前为模拟回复，后续对接真实 LLM 后将提供精准分析"

    return APIResponse.success(data={
        "reply": reply,
        "model": data.model or "mock",
        "timestamp": datetime.now().isoformat(),
    })


# ==================== 智能搜索 ====================

@router.get("/search", summary="智能搜索（意图识别）")
async def smart_search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    db: Session = Depends(get_db),
):
    """
    智能搜索：自动识别输入类型（IP/MAC/设备人名），返回聚合结果
    """
    import re

    results = {"type": "unknown", "items": []}

    # IP 地址识别
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', q):
        results["type"] = "ip"
        from app.models.ip_address import IPAddress
        ips = db.query(IPAddress).filter(IPAddress.ip_address == q).all()
        results["items"] = [{"ip": ip.ip_address, "status": ip.status, "segment_id": ip.segment_id} for ip in ips]

    # MAC 地址识别
    elif re.match(r'^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$', q):
        results["type"] = "mac"
        from app.models.device import Device
        devices = db.query(Device).filter(Device.mac_address.contains(q)).all()
        results["items"] = [{"id": d.id, "name": d.name, "mac": d.mac_address} for d in devices]

    # CIDR 识别
    elif '/' in q and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', q):
        results["type"] = "segment"
        from app.models.network_segment import NetworkSegment
        segs = db.query(NetworkSegment).filter(NetworkSegment.cidr == q).all()
        results["items"] = [{"id": s.id, "name": s.name, "cidr": s.cidr} for s in segs]

    # 通用文本搜索
    else:
        results["type"] = "text"
        from app.models.device import Device
        from app.models.network_segment import NetworkSegment
        devices = db.query(Device).filter(Device.name.contains(q)).limit(10).all()
        segments = db.query(NetworkSegment).filter(NetworkSegment.name.contains(q)).limit(10).all()
        results["items"] = (
            [{"type": "device", "id": d.id, "name": d.name} for d in devices] +
            [{"type": "segment", "id": s.id, "name": s.name, "cidr": s.cidr} for s in segments]
        )

    results["total"] = len(results["items"])
    return APIResponse.success(data=results)


# ==================== AI 模型配置 ====================

@router.get("/models", summary="获取可用 AI 模型列表")
async def list_ai_models():
    """返回系统支持AI 模型列表"""
    models = [
        {"id": "openai-gpt4", "name": "GPT-4", "provider": "OpenAI", "status": "available"},
        {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "DeepSeek", "status": "available"},
        {"id": "qwen-turbo", "name": "通义千问 Turbo", "provider": "阿里云", "status": "available"},
        {"id": "ollama-local", "name": "本地 Ollama", "provider": "本地部署", "status": "not_configured"},
    ]
    return APIResponse.success(data={"items": models, "total": len(models)})
