"""
多渠道通知服务

负责统一管理所有通知渠道的初始化、自动检测和并发推送。
"""

import concurrent.futures
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

from .notification_sender.wechat_sender import WechatSender
from .notification_sender.feishu_sender import FeishuSender
from .notification_sender.telegram_sender import TelegramSender
from .notification_sender.email_sender import EmailSender
from .notification_sender.pushplus_sender import PushPlusSender


class NotificationService:
    """
    多渠道通知服务

    - 自动检测已配置的渠道
    - 并发向所有渠道推送消息
    - 任意一个渠道成功即返回 True
    """

    def __init__(self, config=None):
        """
        初始化所有渠道发送器并自动检测配置状态

        Args:
            config: 可选配置对象（settings 实例或任意带属性的对象）
        """
        self._senders: Dict[str, Any] = {
            "企业微信": WechatSender(config),
            "飞书": FeishuSender(config),
            "Telegram": TelegramSender(config),
            "邮件": EmailSender(config),
            "PushPlus": PushPlusSender(config),
        }

        # 检测哪些渠道已配置
        self._active_channels: List[str] = [
            name for name, sender in self._senders.items() if sender.is_available()
        ]

        if self._active_channels:
            logger.info(
                f"已配置 {len(self._active_channels)} 个通知渠道："
                + "、".join(self._active_channels)
            )
        else:
            logger.warning("未配置任何通知渠道")

    def is_available(self) -> bool:
        """是否至少有一个渠道可用"""
        return len(self._active_channels) > 0

    def send(
        self,
        content: str,
        subject: str = "FinanceSail 市场报告",
        attachments: Optional[List[Path]] = None,
    ) -> bool:
        """
        并发向所有已配置的渠道推送消息

        Args:
            content: 消息内容（Markdown 格式）
            subject: 邮件主题（邮件渠道专用）
            attachments: 附件路径列表（邮件渠道专用）

        Returns:
            bool: 至少一个渠道成功则返回 True
        """
        if not self.is_available():
            logger.warning("无可用通知渠道，跳过推送")
            return False

        results: Dict[str, bool] = {}

        def _send_to_channel(name: str, sender: Any) -> tuple:
            try:
                if name == "邮件":
                    ok = sender.send(content, subject=subject, attachments=attachments)
                elif name == "PushPlus":
                    ok = sender.send(content, title=subject)
                else:
                    ok = sender.send(content)
                return name, ok
            except Exception as e:
                logger.error(f"[{name}] 推送异常: {e}")
                return name, False

        # 只对已激活渠道并发推送
        active_senders = {name: self._senders[name] for name in self._active_channels}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(active_senders)
        ) as executor:
            futures = {
                executor.submit(_send_to_channel, name, sender): name
                for name, sender in active_senders.items()
            }
            for future in concurrent.futures.as_completed(futures):
                name, ok = future.result()
                results[name] = ok
                status = "✓" if ok else "✗"
                logger.info(f"[{name}] {status}")

        success_channels = [n for n, ok in results.items() if ok]
        fail_channels = [n for n, ok in results.items() if not ok]

        if success_channels:
            logger.info(f"推送成功渠道: {', '.join(success_channels)}")
        if fail_channels:
            logger.warning(f"推送失败渠道: {', '.join(fail_channels)}")

        return bool(success_channels)

    @property
    def active_channels(self) -> List[str]:
        """返回当前激活的渠道列表"""
        return list(self._active_channels)
