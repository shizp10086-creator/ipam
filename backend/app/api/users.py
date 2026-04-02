"""
User Management API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, PasswordChangeRequest
from app.services.log_service import LogService
from app.api.deps import get_current_active_user, require_admin, get_client_ip

router = APIRouter()


def search_users(db, keyword=None, role=None, is_active=None, page=1, page_size=20):
    query = db.query(User)
    if keyword:
        p = f"%{keyword}%"
        query = query.filter((User.username.like(p)) | (User.email.like(p)) | (User.full_name.like(p)))
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return users, total


@router.get("/", response_model=dict)
async def get_users(
    keyword: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    users, total = search_users(db=db, keyword=keyword, role=role, is_active=is_active, page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size
    return {"code":200,"message":"Success","data":{"items":[UserResponse.from_orm(u) for u in users],"total":total,"page":page,"page_size":page_size,"total_pages":total_pages}}


@router.post("/", response_model=dict)
async def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin), client_ip: Optional[str] = Depends(get_client_ip)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail=f"Username '{user.username}' already exists")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail=f"Email '{user.email}' already in use")
    db_user = User(username=user.username, hashed_password=get_password_hash(user.password), email=user.email, full_name=user.full_name, role=user.role, is_active=user.is_active)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    return {"code":201,"message":"User created successfully","data":UserResponse.from_orm(db_user)}


@router.get("/{user_id}", response_model=dict)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"code":200,"message":"Success","data":UserResponse.from_orm(user)}


@router.put("/{user_id}", response_model=dict)
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), client_ip: Optional[str] = Depends(get_client_ip)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No permission to modify other users")
    update_data = user_update.dict(exclude_unset=True)
    if current_user.role != "admin" and ("role" in update_data or "is_active" in update_data):
        raise HTTPException(status_code=403, detail="Only admin can modify role and active status")
    if "email" in update_data and update_data["email"] != user.email:
        if db.query(User).filter(User.email == update_data["email"], User.id != user_id).first():
            raise HTTPException(status_code=400, detail=f"Email '{update_data['email']}' already in use")
    for field, value in update_data.items():
        setattr(user, field, value)
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")
    return {"code":200,"message":"User updated successfully","data":UserResponse.from_orm(user)}


@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin), client_ip: Optional[str] = Depends(get_client_ip)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    return {"code":200,"message":"User deleted successfully","data":None}


@router.put("/{user_id}/password", response_model=dict)
async def change_password(user_id: int, password_change: PasswordChangeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password_change.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    if verify_password(password_change.new_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as old password")
    user.hashed_password = get_password_hash(password_change.new_password)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")
    return {"code":200,"message":"Password changed successfully","data":None}