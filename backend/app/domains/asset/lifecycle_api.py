"""
资产全生命周期 + 软件许可证 + 合同供应商管理 API。
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== 资产生命周期 ====================

@router.get("/lifecycle/stats", summary="资产生命周期统计")
def lifecycle_stats(db: Session = Depends(get_db)):
    stats = {}
    for status in ["purchasing", "in_stock", "in_use", "repair", "idle", "retired"]:
        # 使用 devices 表的现有数据模拟
        stats[status] = 0
    try:
        r = db.execute(text("SELECT COUNT(*) FROM devices WHERE deleted_at IS NULL")).scalar()
        stats["in_use"] = r or 0
        stats["total"] = r or 0
    except Exception:
        stats["total"] = 0
    return APIResponse.success(data=stats)


@router.get("/lifecycle/transfers", summary="资产流转记录")
def list_transfers(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """领用/调拨/借用/归还记录。"""
    # 从操作日志中提取资产相关操作
    try:
        r = db.execute(text("""
            SELECT id, username, operation_type, resource_type, details, created_at
            FROM operation_logs
            WHERE resource_type IN ('device', 'asset')
            ORDER BY created_at DESC LIMIT :lim OFFSET :off
        """), {"lim": limit, "off": skip})
        items = [dict(row._mapping) for row in r]
        for item in items:
            for k, v in item.items():
                if isinstance(v, datetime):
                    item[k] = v.isoformat()
    except Exception:
        items = []
    return APIResponse.success(data={"items": items, "total": len(items)})


# ==================== 软件许可证 ====================

class LicenseCreate(BaseModel):
    software_name: str = Field(..., max_length=200)
    version: Optional[str] = None
    license_type: str = "perpetual"  # perpetual/subscription/oem
    total_count: int = Field(..., ge=1)
    purchase_date: Optional[str] = None
    expire_date: Optional[str] = None
    vendor: Optional[str] = None
    license_key: Optional[str] = None
    cost: Optional[float] = None


@router.get("/licenses", summary="软件许可证列表")
def list_licenses(db: Session = Depends(get_db)):
    try:
        r = db.execute(text("SELECT * FROM software_licenses ORDER BY created_at DESC"))
        items = [dict(row._mapping) for row in r]
        for item in items:
            for k, v in item.items():
                if isinstance(v, datetime):
                    item[k] = v.isoformat()
    except Exception:
        items = []
    return APIResponse.success(data={"items": items, "total": len(items)})


@router.post("/licenses", status_code=201, summary="添加软件许可证")
def create_license(data: LicenseCreate, db: Session = Depends(get_db)):
    db.execute(text("""
        INSERT INTO software_licenses (software_name, version, license_type, total_count, used_count,
            purchase_date, expire_date, vendor, license_key, cost)
        VALUES (:name, :ver, :ltype, :total, 0, :pdate, :edate, :vendor, :lkey, :cost)
    """), {
        "name": data.software_name, "ver": data.version, "ltype": data.license_type,
        "total": data.total_count, "pdate": data.purchase_date, "edate": data.expire_date,
        "vendor": data.vendor, "lkey": data.license_key, "cost": data.cost,
    })
    db.commit()
    return APIResponse.success(message="许可证添加成功", code=201)


# ==================== 合同管理 ====================

class ContractCreate(BaseModel):
    contract_no: str = Field(..., max_length=100)
    contract_type: str = "purchase"  # purchase/maintenance/lease/subscription
    vendor: str = Field(..., max_length=200)
    amount: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


@router.get("/contracts", summary="合同列表")
def list_contracts(db: Session = Depends(get_db)):
    try:
        r = db.execute(text("SELECT * FROM contracts ORDER BY created_at DESC"))
        items = [dict(row._mapping) for row in r]
        for item in items:
            for k, v in item.items():
                if isinstance(v, datetime):
                    item[k] = v.isoformat()
    except Exception:
        items = []
    return APIResponse.success(data={"items": items, "total": len(items)})


@router.post("/contracts", status_code=201, summary="添加合同")
def create_contract(data: ContractCreate, db: Session = Depends(get_db)):
    db.execute(text("""
        INSERT INTO contracts (contract_no, contract_type, vendor, amount, start_date, end_date, description)
        VALUES (:no, :ctype, :vendor, :amount, :sdate, :edate, :desc)
    """), {
        "no": data.contract_no, "ctype": data.contract_type, "vendor": data.vendor,
        "amount": data.amount, "sdate": data.start_date, "edate": data.end_date, "desc": data.description,
    })
    db.commit()
    return APIResponse.success(message="合同添加成功", code=201)


# ==================== 供应商管理 ====================

@router.get("/vendors", summary="供应商列表")
def list_vendors(db: Session = Depends(get_db)):
    try:
        r = db.execute(text("SELECT * FROM vendors ORDER BY created_at DESC"))
        items = [dict(row._mapping) for row in r]
        for item in items:
            for k, v in item.items():
                if isinstance(v, datetime):
                    item[k] = v.isoformat()
    except Exception:
        items = []
    return APIResponse.success(data={"items": items, "total": len(items)})


@router.post("/vendors", status_code=201, summary="添加供应商")
def create_vendor(name: str, contact: str = None, phone: str = None, db: Session = Depends(get_db)):
    db.execute(text("""
        INSERT INTO vendors (name, contact_name, contact_phone)
        VALUES (:name, :contact, :phone)
    """), {"name": name, "contact": contact, "phone": phone})
    db.commit()
    return APIResponse.success(message="供应商添加成功", code=201)
