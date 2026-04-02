"""
Alert Service
处理告警相关的业务逻辑，包括使用率监控、告警触发和解除
"""
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.alert import Alert
from app.models.network_segment import NetworkSegment
from app.models.ip_address import IPAddress


class AlertService:
    """告警服务类"""
    
    @staticmethod
    def calculate_segment_usage(db: Session, segment_id: int) -> Optional[Dict]:
        """
        计算网段使用率
        
        Args:
            db: 数据库会话
            segment_id: 网段 ID
            
        Returns:
            {
                'total_ips': int,      # 总 IP 数量
                'used_ips': int,       # 已用 IP 数量
                'available_ips': int,  # 可用 IP 数量
                'reserved_ips': int,   # 保留 IP 数量
                'usage_rate': float    # 使用率（百分比）
            }
            如果网段不存在返回 None
        """
        # 查询网段
        segment = db.query(NetworkSegment).filter(
            NetworkSegment.id == segment_id
        ).first()
        
        if not segment:
            return None
        
        # 计算总 IP 数量（排除网络地址和广播地址）
        total_ips = 2 ** (32 - segment.prefix_length) - 2
        
        # 查询各状态 IP 数量
        used_ips = db.query(IPAddress).filter(
            IPAddress.segment_id == segment_id,
            IPAddress.status == 'used'
        ).count()
        
        reserved_ips = db.query(IPAddress).filter(
            IPAddress.segment_id == segment_id,
            IPAddress.status == 'reserved'
        ).count()
        
        available_ips = total_ips - used_ips - reserved_ips
        
        # 计算使用率
        usage_rate = (used_ips + reserved_ips) / total_ips * 100 if total_ips > 0 else 0
        
        return {
            'segment_id': segment_id,
            'segment_name': segment.name,
            'total_ips': total_ips,
            'used_ips': used_ips,
            'available_ips': available_ips,
            'reserved_ips': reserved_ips,
            'usage_rate': round(usage_rate, 2),
            'threshold': segment.usage_threshold
        }
    
    @staticmethod
    def check_and_create_alert(
        db: Session,
        segment_id: int
    ) -> Tuple[bool, Optional[str], Optional[Alert]]:
        """
        检查网段使用率并在达到阈值时创建告警
        
        Args:
            db: 数据库会话
            segment_id: 网段 ID
            
        Returns:
            (alert_created, message, alert): 是否创建了告警、消息、告警对象
        """
        # 1. 计算网段使用率
        usage_stats = AlertService.calculate_segment_usage(db, segment_id)
        if not usage_stats:
            return False, "Network segment not found", None
        
        # 2. 检查是否达到阈值
        current_usage = usage_stats['usage_rate']
        threshold = usage_stats['threshold']
        
        if current_usage < threshold:
            return False, "Usage rate below threshold", None
        
        # 3. 检查是否已存在未解决的告警
        existing_alert = db.query(Alert).filter(
            Alert.segment_id == segment_id,
            Alert.is_resolved == False,
            Alert.alert_type == 'usage_threshold'
        ).first()
        
        if existing_alert:
            # 更新现有告警的使用率
            existing_alert.current_usage = current_usage
            db.commit()
            db.refresh(existing_alert)
            return False, "Alert already exists and was updated", existing_alert
        
        # 4. 创建新告警
        # 确定严重程度
        if current_usage >= 90:
            severity = 'critical'
        else:
            severity = 'warning'
        
        message = (
            f"Network segment '{usage_stats['segment_name']}' usage rate "
            f"has reached {current_usage:.2f}% (threshold: {threshold}%)"
        )
        
        alert = Alert(
            segment_id=segment_id,
            alert_type='usage_threshold',
            severity=severity,
            message=message,
            current_usage=current_usage,
            threshold=threshold,
            is_resolved=False
        )
        
        try:
            db.add(alert)
            db.commit()
            db.refresh(alert)
            return True, "Alert created successfully", alert
        except Exception as e:
            db.rollback()
            return False, f"Database error: {str(e)}", None
    
    @staticmethod
    def check_and_resolve_alert(
        db: Session,
        segment_id: int
    ) -> Tuple[bool, Optional[str], Optional[Alert]]:
        """
        检查网段使用率并在低于阈值时自动解除告警
        
        Args:
            db: 数据库会话
            segment_id: 网段 ID
            
        Returns:
            (alert_resolved, message, alert): 是否解除了告警、消息、告警对象
        """
        # 1. 计算网段使用率
        usage_stats = AlertService.calculate_segment_usage(db, segment_id)
        if not usage_stats:
            return False, "Network segment not found", None
        
        # 2. 检查是否存在未解决的告警
        alert = db.query(Alert).filter(
            Alert.segment_id == segment_id,
            Alert.is_resolved == False,
            Alert.alert_type == 'usage_threshold'
        ).first()
        
        if not alert:
            return False, "No active alert found", None
        
        # 3. 检查使用率是否低于阈值
        current_usage = usage_stats['usage_rate']
        threshold = usage_stats['threshold']
        
        if current_usage >= threshold:
            # 使用率仍然高于阈值，更新告警
            alert.current_usage = current_usage
            db.commit()
            db.refresh(alert)
            return False, "Usage rate still above threshold", alert
        
        # 4. 自动解除告警
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.current_usage = current_usage
        
        try:
            db.commit()
            db.refresh(alert)
            return True, "Alert resolved automatically", alert
        except Exception as e:
            db.rollback()
            return False, f"Database error: {str(e)}", None
    
    @staticmethod
    def monitor_all_segments(db: Session) -> Dict:
        """
        监控所有网段的使用率并触发/解除告警
        
        Args:
            db: 数据库会话
            
        Returns:
            {
                'total_segments': int,
                'alerts_created': int,
                'alerts_resolved': int,
                'segments_checked': List[dict]
            }
        """
        # 查询所有网段
        segments = db.query(NetworkSegment).all()
        
        result = {
            'total_segments': len(segments),
            'alerts_created': 0,
            'alerts_resolved': 0,
            'segments_checked': []
        }
        
        for segment in segments:
            # 计算使用率
            usage_stats = AlertService.calculate_segment_usage(db, segment.id)
            if not usage_stats:
                continue
            
            segment_result = {
                'segment_id': segment.id,
                'segment_name': segment.name,
                'usage_rate': usage_stats['usage_rate'],
                'threshold': usage_stats['threshold'],
                'action': None
            }
            
            # 检查是否需要创建告警
            if usage_stats['usage_rate'] >= usage_stats['threshold']:
                created, msg, alert = AlertService.check_and_create_alert(db, segment.id)
                if created:
                    result['alerts_created'] += 1
                    segment_result['action'] = 'alert_created'
                else:
                    segment_result['action'] = 'alert_exists'
            else:
                # 检查是否需要解除告警
                resolved, msg, alert = AlertService.check_and_resolve_alert(db, segment.id)
                if resolved:
                    result['alerts_resolved'] += 1
                    segment_result['action'] = 'alert_resolved'
                else:
                    segment_result['action'] = 'no_action'
            
            result['segments_checked'].append(segment_result)
        
        return result
    
    @staticmethod
    def resolve_alert_manually(
        db: Session,
        alert_id: int
    ) -> Tuple[bool, str, Optional[Alert]]:
        """
        手动解决告警
        
        Args:
            db: 数据库会话
            alert_id: 告警 ID
            
        Returns:
            (success, message, alert): 操作结果、消息、告警对象
        """
        # 查询告警
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return False, "Alert not found", None
        
        if alert.is_resolved:
            return False, "Alert is already resolved", None
        
        # 更新告警状态
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        
        # 更新当前使用率
        usage_stats = AlertService.calculate_segment_usage(db, alert.segment_id)
        if usage_stats:
            alert.current_usage = usage_stats['usage_rate']
        
        try:
            db.commit()
            db.refresh(alert)
            return True, "Alert resolved successfully", alert
        except Exception as e:
            db.rollback()
            return False, f"Database error: {str(e)}", None
    
    @staticmethod
    def get_alerts(
        db: Session,
        segment_id: Optional[int] = None,
        is_resolved: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Alert], int]:
        """
        获取告警列表
        
        Args:
            db: 数据库会话
            segment_id: 网段 ID（可选）
            is_resolved: 是否已解决（可选）
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            (alerts, total): 告警列表和总数
        """
        query = db.query(Alert)
        
        # 应用筛选条件
        if segment_id is not None:
            query = query.filter(Alert.segment_id == segment_id)
        
        if is_resolved is not None:
            query = query.filter(Alert.is_resolved == is_resolved)
        
        # 获取总数
        total = query.count()
        
        # 应用分页和排序
        alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
        
        return alerts, total
    
    @staticmethod
    def get_alert_by_id(db: Session, alert_id: int) -> Optional[Alert]:
        """
        根据 ID 获取告警详情
        
        Args:
            db: 数据库会话
            alert_id: 告警 ID
            
        Returns:
            告警对象或 None
        """
        return db.query(Alert).filter(Alert.id == alert_id).first()
