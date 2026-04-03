"""
Statistics Service - 统计数据计算服务

This service provides statistical calculations for the dashboard,
including IP usage, device counts, and network segment statistics.

Requirements: 7.1, 7.2, 7.3, 7.4
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.ip_address import IPAddress
from app.models.device import Device
from app.models.network_segment import NetworkSegment
from app.models.operation_log import OperationLog
import logging

logger = logging.getLogger(__name__)


class StatisticsService:
    """统计数据计算服务"""

    def __init__(self, db: Session):
        """
        Initialize statistics service

        Args:
            db: Database session
        """
        self.db = db

    def get_overview_stats(self) -> Dict[str, Any]:
        """
        计算总览统计数据（关键指标）

        Returns:
            Dict containing:
                - total_ips: 总 IP 数
                - used_ips: 已用 IP 数
                - available_ips: 空闲 IP 数
                - reserved_ips: 保留 IP 数
                - total_devices: 设备总数
                - total_segments: 网段总数
                - overall_usage_rate: 总体使用率

        Validates: Requirements 7.4
        """
        try:
            # 计算总 IP 数
            total_ips = self.db.query(func.count(IPAddress.id)).scalar() or 0

            # 计算各状态 IP 数量
            used_ips = self.db.query(func.count(IPAddress.id)).filter(
                IPAddress.status == "used"
            ).scalar() or 0

            available_ips = self.db.query(func.count(IPAddress.id)).filter(
                IPAddress.status == "available"
            ).scalar() or 0

            reserved_ips = self.db.query(func.count(IPAddress.id)).filter(
                IPAddress.status == "reserved"
            ).scalar() or 0

            # 计算在线 IP 数量
            online_ips = self.db.query(func.count(IPAddress.id)).filter(
                IPAddress.is_online == True
            ).scalar() or 0

            # 计算设备总数
            total_devices = self.db.query(func.count(Device.id)).scalar() or 0

            # 计算网段总数
            total_segments = self.db.query(func.count(NetworkSegment.id)).scalar() or 0

            # 计算总体使用率 = (已用 IP + 保留 IP + 在线 IP) / 总 IP × 100%
            overall_usage_rate = 0.0
            if total_ips > 0:
                overall_usage_rate = round((used_ips + reserved_ips + online_ips) / total_ips * 100, 2)

            return {
                "total_ips": total_ips,
                "used_ips": used_ips,
                "available_ips": available_ips,
                "reserved_ips": reserved_ips,
                "online_ips": online_ips,
                "total_devices": total_devices,
                "total_segments": total_segments,
                "overall_usage_rate": overall_usage_rate
            }
        except Exception as e:
            logger.error(f"Error calculating overview stats: {e}")
            raise

    def get_segment_usage_distribution(self) -> List[Dict[str, Any]]:
        """
        计算网段使用率分布

        Returns:
            List of dicts containing:
                - segment_id: 网段 ID
                - segment_name: 网段名称
                - network: 网络地址
                - prefix_length: 前缀长度
                - total_ips: 总 IP 数
                - used_ips: 已用 IP 数
                - available_ips: 空闲 IP 数
                - reserved_ips: 保留 IP 数
                - usage_rate: 使用率（百分比）
                - usage_threshold: 告警阈值

        Validates: Requirements 7.1
        """
        try:
            segments = self.db.query(NetworkSegment).all()
            result = []

            for segment in segments:
                # 计算该网段的总 IP 数（排除网络地址和广播地址）
                total_ips = 2 ** (32 - segment.prefix_length) - 2

                # 查询该网段各状态的 IP 数量
                used_ips = self.db.query(func.count(IPAddress.id)).filter(
                    and_(
                        IPAddress.segment_id == segment.id,
                        IPAddress.status == "used"
                    )
                ).scalar() or 0

                available_ips = self.db.query(func.count(IPAddress.id)).filter(
                    and_(
                        IPAddress.segment_id == segment.id,
                        IPAddress.status == "available"
                    )
                ).scalar() or 0

                reserved_ips = self.db.query(func.count(IPAddress.id)).filter(
                    and_(
                        IPAddress.segment_id == segment.id,
                        IPAddress.status == "reserved"
                    )
                ).scalar() or 0

                # 计算使用率
                usage_rate = 0.0
                if total_ips > 0:
                    usage_rate = round((used_ips + reserved_ips) / total_ips * 100, 2)

                result.append({
                    "segment_id": segment.id,
                    "name": segment.name,  # 前端期望的字段名
                    "segment_name": segment.name,  # 保留兼容性
                    "network": segment.network,
                    "prefix_length": segment.prefix_length,
                    "total_ips": total_ips,
                    "used_ips": used_ips,
                    "available_ips": available_ips,
                    "reserved_ips": reserved_ips,
                    "usage_rate": usage_rate,
                    "usage_threshold": segment.usage_threshold
                })

            return result
        except Exception as e:
            logger.error(f"Error calculating segment usage distribution: {e}")
            raise

    def get_ip_status_distribution(self) -> Dict[str, Any]:
        """
        计算 IP 状态分布（空闲/已用/保留）

        Returns:
            Dict containing:
                - available: 空闲 IP 数量
                - used: 已用 IP 数量
                - reserved: 保留 IP 数量
                - total: 总 IP 数量
                - distribution: 各状态百分比

        Validates: Requirements 7.2
        """
        try:
            # 查询各状态的 IP 数量
            available_count = self.db.query(func.count(IPAddress.id)).filter(
                IPAddress.status == "available"
            ).scalar() or 0

            used_count = self.db.query(func.count(IPAddress.id)).filter(
                IPAddress.status == "used"
            ).scalar() or 0

            reserved_count = self.db.query(func.count(IPAddress.id)).filter(
                IPAddress.status == "reserved"
            ).scalar() or 0

            total_count = available_count + used_count + reserved_count

            # 计算百分比
            distribution = {
                "available": 0.0,
                "used": 0.0,
                "reserved": 0.0
            }

            if total_count > 0:
                distribution["available"] = round(available_count / total_count * 100, 2)
                distribution["used"] = round(used_count / total_count * 100, 2)
                distribution["reserved"] = round(reserved_count / total_count * 100, 2)

            return {
                "available": available_count,
                "used": used_count,
                "reserved": reserved_count,
                "total": total_count,
                "distribution": distribution
            }
        except Exception as e:
            logger.error(f"Error calculating IP status distribution: {e}")
            raise

    def get_device_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        计算设备数量统计和增长趋势

        Args:
            days: 统计的天数（默认 30 天）

        Returns:
            Dict containing:
                - total_devices: 设备总数
                - device_types: 按设备类型分组的统计
                - growth_trend: 增长趋势数据（按天）

        Validates: Requirements 7.3
        """
        try:
            # 计算设备总数
            total_devices = self.db.query(func.count(Device.id)).scalar() or 0

            # 按设备类型分组统计
            device_type_stats = self.db.query(
                Device.device_type,
                func.count(Device.id).label("count")
            ).group_by(Device.device_type).all()

            device_types = {}
            for device_type, count in device_type_stats:
                type_name = device_type if device_type else "未分类"
                device_types[type_name] = count

            # 计算增长趋势（按天统计）
            start_date = datetime.now() - timedelta(days=days)

            # 查询每天创建的设备数量
            daily_growth = self.db.query(
                func.date(Device.created_at).label("date"),
                func.count(Device.id).label("count")
            ).filter(
                Device.created_at >= start_date
            ).group_by(
                func.date(Device.created_at)
            ).order_by(
                func.date(Device.created_at)
            ).all()

            # 构建增长趋势数据
            growth_trend = []
            cumulative_count = self.db.query(func.count(Device.id)).filter(
                Device.created_at < start_date
            ).scalar() or 0

            # 创建日期到数量的映射
            daily_map = {str(date): count for date, count in daily_growth}

            # 填充每一天的数据
            current_date = start_date.date()
            end_date = datetime.now().date()

            dates = []  # 日期数组
            counts = []  # 累计数量数组

            while current_date <= end_date:
                date_str = str(current_date)
                daily_count = daily_map.get(date_str, 0)
                cumulative_count += daily_count

                dates.append(date_str)
                counts.append(cumulative_count)

                growth_trend.append({
                    "date": date_str,
                    "daily_count": daily_count,
                    "cumulative_count": cumulative_count
                })

                current_date += timedelta(days=1)

            return {
                "total_devices": total_devices,
                "device_types": device_types,
                "growth_trend": growth_trend,
                "dates": dates,  # 前端期望的格式
                "counts": counts  # 前端期望的格式
            }
        except Exception as e:
            logger.error(f"Error calculating device statistics: {e}")
            raise

    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的操作活动

        Args:
            limit: 返回的记录数量

        Returns:
            List of recent operation logs
        """
        try:
            logs = self.db.query(OperationLog).order_by(
                OperationLog.created_at.desc()
            ).limit(limit).all()

            result = []
            for log in logs:
                result.append({
                    "id": log.id,
                    "username": log.username,
                    "operation_type": log.operation_type,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })

            return result
        except Exception as e:
            logger.error(f"Error fetching recent activities: {e}")
            raise

    def get_time_range_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取指定时间范围内的统计数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict containing time-filtered statistics

        Validates: Requirements 7.6
        """
        try:
            # 如果没有指定时间范围，使用最近 30 天
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # 统计时间范围内创建的设备数量
            devices_created = self.db.query(func.count(Device.id)).filter(
                and_(
                    Device.created_at >= start_date,
                    Device.created_at <= end_date
                )
            ).scalar() or 0

            # 统计时间范围内分配的 IP 数量
            ips_allocated = self.db.query(func.count(IPAddress.id)).filter(
                and_(
                    IPAddress.allocated_at >= start_date,
                    IPAddress.allocated_at <= end_date,
                    IPAddress.status == "used"
                )
            ).scalar() or 0

            # 统计时间范围内的操作数量
            operations_count = self.db.query(func.count(OperationLog.id)).filter(
                and_(
                    OperationLog.created_at >= start_date,
                    OperationLog.created_at <= end_date
                )
            ).scalar() or 0

            # 按操作类型分组统计
            operation_types = self.db.query(
                OperationLog.operation_type,
                func.count(OperationLog.id).label("count")
            ).filter(
                and_(
                    OperationLog.created_at >= start_date,
                    OperationLog.created_at <= end_date
                )
            ).group_by(OperationLog.operation_type).all()

            operation_type_stats = {op_type: count for op_type, count in operation_types}

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "devices_created": devices_created,
                "ips_allocated": ips_allocated,
                "operations_count": operations_count,
                "operation_types": operation_type_stats
            }
        except Exception as e:
            logger.error(f"Error calculating time range stats: {e}")
            raise


def get_statistics_service(db: Session) -> StatisticsService:
    """
    Factory function to create StatisticsService instance

    Args:
        db: Database session

    Returns:
        StatisticsService instance
    """
    return StatisticsService(db)
