"""
Device Management API Endpoints
提供设备的创建、查询、更新、删除等 API 接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListQuery,
    DeviceWithIPsResponse
)
from app.schemas.ip_address import IPAddressResponse
from app.services.device_service import DeviceService
from app.services.log_service import LogService
from app.utils.device_utils import search_devices, get_device_by_id
from app.api.deps import get_current_active_user, require_user_or_admin, allow_readonly, get_client_ip

router = APIRouter()


@router.get("/", response_model=dict)
async def get_devices(
    keyword: Optional[str] = Query(None, description="搜索关键词（在名称、MAC、责任人中搜索）"),
    device_type: Optional[str] = Query(None, description="按设备类型筛选"),
    owner: Optional[str] = Query(None, description="按责任人筛选"),
    department: Optional[str] = Query(None, description="按部门筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取设备列表
    支持模糊搜索和多条件筛?

    - **keyword**: 搜索关键词（在设备名称、MAC 地址、责任人中搜索）
    - **device_type**: 按设备类型筛?
    - **owner**: 按责任人筛?
    - **department**: 按部门筛?
    - **page**: 页码（从 1 开始）
    - **page_size**: 每页数量?-100?
    """
    devices, total = search_devices(
        db=db,
        keyword=keyword,
        device_type=device_type,
        owner=owner,
        department=department,
        page=page,
        page_size=page_size
    )

    # 计算总页?
    total_pages = (total + page_size - 1) // page_size

    return {
        "code": 200,
        "message": "Success",
        "data": {
            "items": [DeviceResponse.from_orm(device) for device in devices],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    }


@router.post("/", response_model=dict)
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    创建设备

    - **name**: 设备名称（必填）
    - **mac_address**: MAC 地址（必填，支持格式：AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, AABBCCDDEEFF?
    - **owner**: 责任人（必填?
    - **device_type**: 设备类型（可选）
    - **manufacturer**: 制造商（可选）
    - **model**: 型号（可选）
    - **department**: 部门（可选）
    - **location**: 物理位置（可选）
    - **description**: 描述（可选）

    注意：MAC 地址必须唯一，不能重?
    """
    success, message, created_device = DeviceService.create_device(
        db=db,
        name=device.name,
        mac_address=device.mac_address,
        owner=device.owner,
        device_type=device.device_type,
        manufacturer=device.manufacturer,
        model=device.model,
        department=device.department,
        location=device.location,
        description=device.description,
        created_by=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=message
        )

    # 记录操作日志
    try:
        device_data = {
            "name": created_device.name,
            "mac_address": created_device.mac_address,
            "owner": created_device.owner,
            "device_type": created_device.device_type,
            "department": created_device.department,
            "location": created_device.location
        }

        LogService.log_device_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            operation_type="create",
            device_id=created_device.id,
            device_data=device_data,
            client_ip=client_ip
        )
    except Exception as e:
        # 日志记录失败不应影响主要操作
        print(f"Failed to log device creation: {e}")

    return {
        "code": 201,
        "message": message,
        "data": DeviceResponse.from_orm(created_device)
    }


@router.get("/{device_id}", response_model=dict)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    获取设备详情

    - **device_id**: 设备 ID

    返回设备的完整信?
    """
    device = get_device_by_id(db, device_id)

    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    return {
        "code": 200,
        "message": "Success",
        "data": DeviceResponse.from_orm(device)
    }


@router.put("/{device_id}", response_model=dict)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    更新设备信息

    - **device_id**: 设备 ID
    - **device_update**: 更新数据（所有字段都是可选的?

    注意?
    - 更新设备信息不会影响其关联的 IP 地址
    - 如果更新 MAC 地址，新 MAC 地址必须唯一
    """
    update_data = device_update.dict(exclude_unset=True)

    success, message, updated_device = DeviceService.update_device(
        db=db,
        device_id=device_id,
        **update_data
    )

    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        else:
            raise HTTPException(status_code=400, detail=message)

    # 记录操作日志
    try:
        device_data = {
            "name": updated_device.name,
            "mac_address": updated_device.mac_address,
            "owner": updated_device.owner,
            "device_type": updated_device.device_type,
            "department": updated_device.department,
            "location": updated_device.location,
            "updated_fields": list(update_data.keys())
        }

        LogService.log_device_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            operation_type="update",
            device_id=updated_device.id,
            device_data=device_data,
            client_ip=client_ip
        )
    except Exception as e:
        # 日志记录失败不应影响主要操作
        print(f"Failed to log device update: {e}")

    return {
        "code": 200,
        "message": message,
        "data": DeviceResponse.from_orm(updated_device)
    }


@router.delete("/{device_id}", response_model=dict)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_or_admin),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    删除设备

    - **device_id**: 设备 ID

    注意?
    - 删除设备时，会自动回收该设备关联的所?IP 地址
    - 被回收的 IP 地址状态将变为"空闲"（available?
    - 此操作不可撤销，请谨慎操作
    """
    # 获取设备信息用于日志记录
    device = get_device_by_id(db, device_id)
    device_data = None
    if device:
        device_data = {
            "name": device.name,
            "mac_address": device.mac_address,
            "owner": device.owner,
            "device_type": device.device_type
        }

    success, message = DeviceService.delete_device(db, device_id)

    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        else:
            raise HTTPException(status_code=400, detail=message)

    # 记录操作日志
    if device_data:
        try:
            LogService.log_device_operation(
                db=db,
                user_id=current_user.id,
                username=current_user.username,
                operation_type="delete",
                device_id=device_id,
                device_data=device_data,
                client_ip=client_ip
            )
        except Exception as e:
            # 日志记录失败不应影响主要操作
            print(f"Failed to log device deletion: {e}")

    return {
        "code": 200,
        "message": message,
        "data": None
    }


@router.get("/{device_id}/ips", response_model=dict)
async def get_device_ips(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    获取设备关联的所?IP 地址

    - **device_id**: 设备 ID

    返回该设备当前关联的所?IP 地址列表
    """
    success, message, ips = DeviceService.get_device_ips(db, device_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=message
        )

    return {
        "code": 200,
        "message": message,
        "data": {
            "device_id": device_id,
            "ip_count": len(ips),
            "ips": [IPAddressResponse.from_orm(ip) for ip in ips]
        }
    }
