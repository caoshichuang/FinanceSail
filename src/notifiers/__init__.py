"""
通知模块

兼容旧版 EmailNotifier / WxPusherNotifier，
同时暴露新的多渠道 NotificationService。
"""

from .email import EmailNotifier
from .notification_service import NotificationService

__all__ = [
    "EmailNotifier",
    "NotificationService",
]
