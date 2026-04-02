"""
ScanHistory Model - 扫描历史表
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ScanHistory(Base):
    """
    扫描历史模型
    记录 IP 扫描的历史记录和结果
    """
    __tablename__ = "scan_history"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 外键
    segment_id = Column(Integer, ForeignKey("network_segments.id"), nullable=False, comment="网段 ID")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="发起人 ID")
    
    # 扫描信息
    scan_type = Column(String(20), nullable=False, comment="扫描类型: ping/arp")
    total_ips = Column(Integer, nullable=False, comment="扫描 IP 总数")
    online_ips = Column(Integer, nullable=False, comment="在线 IP 数量")
    duration = Column(Float, nullable=False, comment="扫描耗时（秒）")
    
    # 扫描结果
    results = Column(Text, nullable=True, comment="扫描结果（JSON 格式）")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="扫描时间")
    
    # 关系定义
    # 关联网段
    segment = relationship("NetworkSegment", back_populates="scan_histories")
    
    # 发起人
    creator = relationship("User", back_populates="scan_histories")
    
    def __repr__(self):
        return f"<ScanHistory(id={self.id}, segment_id={self.segment_id}, type='{self.scan_type}', online={self.online_ips}/{self.total_ips})>"
