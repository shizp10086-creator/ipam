"""
数据清理定时任务。
"""
import logging
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.cleanup.check_temporary_ip_expiry")
def check_temporary_ip_expiry():
    """检查并回收已过期的临时 IP 地址。"""
    logger.info("开始检查临时 IP 过期...")
    # TODO: Phase 1 任务 7.7 实现具体逻辑
    logger.info("临时 IP 过期检查完成")


@celery_app.task(name="app.tasks.cleanup.check_reserved_ip_expiry")
def check_reserved_ip_expiry():
    """检查并释放已过期的保留 IP 地址。"""
    logger.info("开始检查保留 IP 过期...")
    # TODO: Phase 1 任务 7.2 实现具体逻辑
    logger.info("保留 IP 过期检查完成")
