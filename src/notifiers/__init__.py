"""
通知模块

多渠道通知服务，支持企业微信/飞书/Telegram/邮件/PushPlus 并发推送。
"""

from .notification_service import NotificationService

__all__ = [
    "NotificationService",
]
