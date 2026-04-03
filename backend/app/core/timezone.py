"""
统一时间工具 — 所有时间统一使用北京时间。
"""
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))


def now():
    """返回当前北京时间（带时区信息）"""
    return datetime.now(CST)


def now_naive():
    """返回当前北京时间（无时区信息，用于数据库存储）"""
    return datetime.now(CST).replace(tzinfo=None)
