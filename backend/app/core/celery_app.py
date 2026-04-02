"""
Celery 任务队列配置。

支持：
- 异步任务处理（扫描、导入导出、报表生成等）
- 定时任务调度（定时扫描、自动回收、数据清洗等）
- 优先级队列（紧急/高/中/低）
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "ipam",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery 配置
celery_app.conf.update(
    # 序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务执行
    task_acks_late=True,  # 任务完成后才确认（防止 Worker 崩溃丢任务）
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # 每次只取一个任务（配合 acks_late）

    # 结果过期
    result_expires=3600,  # 结果保留 1 小时

    # 优先级队列
    task_queue_max_priority=10,
    task_default_priority=5,

    # 任务路由
    task_routes={
        "app.tasks.scan.*": {"queue": "scan"},
        "app.tasks.alert.*": {"queue": "alert", "priority": 8},
        "app.tasks.report.*": {"queue": "report", "priority": 3},
        "app.tasks.cleanup.*": {"queue": "cleanup", "priority": 2},
    },

    # 定时任务（Celery Beat）
    beat_schedule={
        # 临时 IP 自动过期回收 - 每 5 分钟检查一次
        "check-temporary-ip-expiry": {
            "task": "app.tasks.cleanup.check_temporary_ip_expiry",
            "schedule": 300.0,  # 5 分钟
            "options": {"priority": 5},
        },
        # 保留 IP 过期检查 - 每小时
        "check-reserved-ip-expiry": {
            "task": "app.tasks.cleanup.check_reserved_ip_expiry",
            "schedule": 3600.0,  # 1 小时
            "options": {"priority": 3},
        },
        # 网段使用率告警检查 - 每 10 分钟
        "check-segment-usage-alerts": {
            "task": "app.tasks.alert.check_segment_usage_alerts",
            "schedule": 600.0,  # 10 分钟
            "options": {"priority": 7},
        },
    },
)

# 自动发现任务模块
celery_app.autodiscover_tasks(["app.tasks"])
