"""
OperationLog Model - 操作日志表
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class OperationLog(Base):
    """
    操作日志模型
    记录系统中所有关键操作的审计记录
    """
    __tablename__ = "operation_logs"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 操作人信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="操作人 ID")
    username = Column(String(50), nullable=False, comment="操作人用户名（冗余字段）")
    
    # 操作信息
    operation_type = Column(
        String(20), 
        nullable=False, 
        index=True,
        comment="操作类型: create/update/delete/allocate/release"
    )
    resource_type = Column(
        String(20), 
        nullable=False, 
        index=True,
        comment="资源类型: ip/device/segment/user"
    )
    resource_id = Column(Integer, nullable=True, comment="资源 ID")
    
    # 操作详情
    details = Column(Text, nullable=True, comment="操作详情（JSON 格式）")
    
    # 客户端信息
    ip_address = Column(String(45), nullable=True, comment="客户端 IP")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True, comment="操作时间")
    
    # 关系定义
    # 操作人
    user = relationship("User", back_populates="operation_logs")
    
    def __repr__(self):
        return f"<OperationLog(id={self.id}, user='{self.username}', type='{self.operation_type}', resource='{self.resource_type}')>"
