"""
DCIM 域 API — 机房、机架、VLAN、线缆管理。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse
from app.domains.dcim.models import DataCenter, Rack, RackInstallation, Vlan, CableConnection

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schema ====================

class DataCenterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    dc_type: str = Field(..., description="site/building/floor/room")
    parent_id: Optional[int] = None
    location: Optional[str] = None
    area: Optional[float] = None
    power_capacity: Optional[float] = None
    description: Optional[str] = None

class DataCenterResponse(BaseModel):
    id: int; tenant_id: int; name: str; dc_type: str
    parent_id: Optional[int] = None; location: Optional[str] = None
    area: Optional[float] = None; power_capacity: Optional[float] = None
    description: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class RackCreate(BaseModel):
    datacenter_id: int
    name: str = Field(..., min_length=1, max_length=100)
    total_u: int = Field(42, ge=1, le=60)
    rated_power: Optional[float] = None
    max_weight: Optional[float] = None
    row_number: Optional[str] = None
    column_number: Optional[str] = None

class RackResponse(BaseModel):
    id: int; tenant_id: int; datacenter_id: int; name: str
    total_u: int; used_u: int; rated_power: Optional[float] = None
    current_power: Optional[float] = None; max_weight: Optional[float] = None
    row_number: Optional[str] = None; column_number: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class InstallDeviceRequest(BaseModel):
    rack_id: int
    device_id: int
    start_u: int = Field(..., ge=1)
    u_size: int = Field(..., ge=1, le=20)
    face: str = Field("front", description="front/rear")
    power_consumption: Optional[float] = None
    pdu_port: Optional[str] = None

class VlanCreate(BaseModel):
    vlan_id: int = Field(..., ge=1, le=4094)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    group_name: Optional[str] = None
    segment_ids: Optional[list[int]] = []

class VlanResponse(BaseModel):
    id: int; tenant_id: int; vlan_id: int; name: str
    description: Optional[str] = None; group_name: Optional[str] = None
    segment_ids: Optional[list] = []; created_at: datetime
    class Config:
        from_attributes = True

class CableCreate(BaseModel):
    device_a_id: Optional[int] = None
    port_a: str
    device_b_id: Optional[int] = None
    port_b: str
    cable_type: Optional[str] = None
    cable_number: Optional[str] = None
    cable_length: Optional[float] = None


# ==================== 机房 API ====================

@router.get("/datacenters", summary="获取机房列表")
def list_datacenters(
    dc_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(DataCenter)
    if dc_type:
        query = query.filter(DataCenter.dc_type == dc_type)
    if parent_id is not None:
        query = query.filter(DataCenter.parent_id == parent_id)
    elif parent_id is None and dc_type is None:
        query = query.filter(DataCenter.parent_id.is_(None))
    if search:
        query = query.filter(DataCenter.name.contains(search))
    items = query.all()
    return APIResponse.success(data={
        "items": [DataCenterResponse.model_validate(d).model_dump() for d in items],
        "total": len(items),
    })

@router.post("/datacenters", status_code=201, summary="创建机房/站点")
def create_datacenter(data: DataCenterCreate, db: Session = Depends(get_db)):
    dc = DataCenter(tenant_id=1, **data.model_dump(exclude_none=True))
    db.add(dc)
    db.commit()
    db.refresh(dc)
    return APIResponse.success(data=DataCenterResponse.model_validate(dc).model_dump(), code=201)

@router.get("/datacenters/{dc_id}", summary="获取机房详情")
def get_datacenter(dc_id: int, db: Session = Depends(get_db)):
    dc = db.query(DataCenter).filter(DataCenter.id == dc_id).first()
    if not dc:
        raise HTTPException(404, "机房不存在")
    rack_count = db.query(Rack).filter(Rack.datacenter_id == dc_id).count()
    result = DataCenterResponse.model_validate(dc).model_dump()
    result["rack_count"] = rack_count
    return APIResponse.success(data=result)


# ==================== 机架 API ====================

@router.get("/racks", summary="获取机架列表")
def list_racks(
    datacenter_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Rack)
    if datacenter_id:
        query = query.filter(Rack.datacenter_id == datacenter_id)
    if search:
        query = query.filter(Rack.name.contains(search))
    items = query.all()
    return APIResponse.success(data={
        "items": [RackResponse.model_validate(r).model_dump() for r in items],
        "total": len(items),
    })

@router.post("/racks", status_code=201, summary="创建机架")
def create_rack(data: RackCreate, db: Session = Depends(get_db)):
    dc = db.query(DataCenter).filter(DataCenter.id == data.datacenter_id).first()
    if not dc:
        raise HTTPException(404, "机房不存在")
    rack = Rack(tenant_id=1, **data.model_dump())
    db.add(rack)
    db.commit()
    db.refresh(rack)
    return APIResponse.success(data=RackResponse.model_validate(rack).model_dump(), code=201)

@router.get("/racks/{rack_id}", summary="获取机架详情（含 U 位视图）")
def get_rack_detail(rack_id: int, db: Session = Depends(get_db)):
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(404, "机架不存在")
    installations = db.query(RackInstallation).filter(
        RackInstallation.rack_id == rack_id,
        RackInstallation.status == "installed",
    ).all()

    # 批量查询关联设备信息
    from app.models.device import Device
    device_ids = [inst.device_id for inst in installations]
    devices_map = {}
    if device_ids:
        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        devices_map = {d.id: d for d in devices}

    u_map = {}
    for inst in installations:
        dev = devices_map.get(inst.device_id)
        for u in range(inst.start_u, inst.start_u + inst.u_size):
            u_map[u] = {
                "device_id": inst.device_id,
                "installation_id": inst.id,
                "device_name": dev.name if dev else f"设备#{inst.device_id}",
                "device_type": getattr(dev, 'device_type', None) or getattr(dev, 'model', None) or "server",
            }

    result = RackResponse.model_validate(rack).model_dump()
    result["u_map"] = u_map
    result["installations"] = [
        {
            "id": i.id,
            "device_id": i.device_id,
            "device_name": devices_map.get(i.device_id, None) and devices_map[i.device_id].name or f"设备#{i.device_id}",
            "device_type": devices_map.get(i.device_id, None) and (getattr(devices_map[i.device_id], 'device_type', None) or "server") or "server",
            "start_u": i.start_u,
            "u_size": i.u_size,
            "face": i.face,
            "pdu_port": i.pdu_port,
            "power_consumption": float(i.power_consumption) if i.power_consumption else None,
        }
        for i in installations
    ]
    return APIResponse.success(data=result)


# ==================== 设备上架/下架 ====================

@router.post("/racks/install", status_code=201, summary="设备上架")
def install_device(data: InstallDeviceRequest, db: Session = Depends(get_db)):
    rack = db.query(Rack).filter(Rack.id == data.rack_id).first()
    if not rack:
        raise HTTPException(404, "机架不存在")
    # 校验 U 位范围
    end_u = data.start_u + data.u_size - 1
    if end_u > rack.total_u:
        raise HTTPException(400, f"U 位超出范围（机架共 {rack.total_u}U，请求 U{data.start_u}-U{end_u}）")
    # 校验 U 位是否空闲
    existing = db.query(RackInstallation).filter(
        RackInstallation.rack_id == data.rack_id,
        RackInstallation.status == "installed",
        RackInstallation.start_u < data.start_u + data.u_size,
        RackInstallation.start_u + RackInstallation.u_size > data.start_u,
    ).first()
    if existing:
        raise HTTPException(409, f"U 位冲突：U{data.start_u}-U{end_u} 已被设备 {existing.device_id} 占用")
    # 安装
    inst = RackInstallation(**data.model_dump())
    db.add(inst)
    rack.used_u += data.u_size
    if data.power_consumption:
        rack.current_power = float(rack.current_power or 0) + data.power_consumption
    db.commit()
    return APIResponse.success(message=f"设备上架成功（U{data.start_u}-U{end_u}）", code=201)

@router.post("/racks/uninstall/{installation_id}", summary="设备下架")
def uninstall_device(installation_id: int, db: Session = Depends(get_db)):
    inst = db.query(RackInstallation).filter(RackInstallation.id == installation_id).first()
    if not inst or inst.status != "installed":
        raise HTTPException(404, "安装记录不存在或已下架")
    rack = db.query(Rack).filter(Rack.id == inst.rack_id).first()
    inst.status = "uninstalled"
    inst.uninstalled_at = datetime.utcnow()
    rack.used_u = max(rack.used_u - inst.u_size, 0)
    if inst.power_consumption:
        rack.current_power = max(float(rack.current_power or 0) - float(inst.power_consumption), 0)
    db.commit()
    return APIResponse.success(message="设备下架成功")


# ==================== VLAN API ====================

@router.get("/vlans", summary="获取 VLAN 列表")
def list_vlans(
    search: Optional[str] = None,
    group_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Vlan)
    if search:
        query = query.filter((Vlan.name.contains(search)) | (Vlan.vlan_id == int(search) if search.isdigit() else False))
    if group_name:
        query = query.filter(Vlan.group_name == group_name)
    items = query.order_by(Vlan.vlan_id).all()
    return APIResponse.success(data={
        "items": [VlanResponse.model_validate(v).model_dump() for v in items],
        "total": len(items),
    })

@router.post("/vlans", status_code=201, summary="创建 VLAN")
def create_vlan(data: VlanCreate, db: Session = Depends(get_db)):
    existing = db.query(Vlan).filter(Vlan.tenant_id == 1, Vlan.vlan_id == data.vlan_id).first()
    if existing:
        raise HTTPException(409, f"VLAN ID {data.vlan_id} 已存在")
    vlan = Vlan(tenant_id=1, **data.model_dump())
    db.add(vlan)
    db.commit()
    db.refresh(vlan)
    return APIResponse.success(data=VlanResponse.model_validate(vlan).model_dump(), code=201)


# ==================== 线缆连接 API ====================

@router.get("/cables", summary="获取线缆连接列表")
def list_cables(device_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(CableConnection).filter(CableConnection.status == "active")
    if device_id:
        query = query.filter(
            (CableConnection.device_a_id == device_id) | (CableConnection.device_b_id == device_id)
        )
    items = query.all()
    return APIResponse.success(data={"items": [
        {"id": c.id, "device_a_id": c.device_a_id, "port_a": c.port_a,
         "device_b_id": c.device_b_id, "port_b": c.port_b,
         "cable_type": c.cable_type, "cable_number": c.cable_number}
        for c in items
    ], "total": len(items)})

@router.post("/cables", status_code=201, summary="创建线缆连接")
def create_cable(data: CableCreate, db: Session = Depends(get_db)):
    # 校验端口未被占用
    existing = db.query(CableConnection).filter(
        CableConnection.status == "active",
        ((CableConnection.device_a_id == data.device_a_id) & (CableConnection.port_a == data.port_a)) |
        ((CableConnection.device_b_id == data.device_b_id) & (CableConnection.port_b == data.port_b)) |
        ((CableConnection.device_a_id == data.device_b_id) & (CableConnection.port_a == data.port_b)) |
        ((CableConnection.device_b_id == data.device_a_id) & (CableConnection.port_b == data.port_a))
    ).first()
    if existing:
        raise HTTPException(409, "端口已被其他连接占用")
    cable = CableConnection(tenant_id=1, **data.model_dump(exclude_none=True))
    db.add(cable)
    db.commit()
    db.refresh(cable)
    return APIResponse.success(message="线缆连接创建成功", code=201)
