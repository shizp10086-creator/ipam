"""
Alert Model - 告警表
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Alert(Base):
    """
    告警模型
    存储系统告警信息，主要用于网段使用率告警
    """
    __tablename__ = "alerts"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 外键
    segment_id = Column(Integer, ForeignKey("network_segments.id"), nullable=False, index=True, comment="网段 ID")

    # 告警信息
    alert_type = Column(String(50), nullable=False, comment="告警类型: usage_threshold")
    severity = Column(String(20), nullable=False, comment="严重程度: warning/critical")
    message = Column(Text, nullable=False, comment="告警消息")

    # 使用率信息
    current_usage = Column(Float, nullable=False, comment="当前使用率")
    threshold = Column(Float, nullable=False, comment="阈值")

    # 解决状态
    is_resolved = Column(Boolean, default=False, nullable=False, index=True, comment="是否已解决")
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True, comment="创建时间")

    # 关系定义
    # 关联网段
    segment = relationship("NetworkSegment", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', resolved={self.is_resolved})>"
