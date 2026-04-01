"""
PushPlus 发送器（国内推送服务）
"""

from typing import Optional

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

_PUSHPLUS_API = "http://www.pushplus.plus/send"


class PushPlusSender:
    """PushPlus 推送通知"""

    def __init__(self, config=None):
        self._token: Optional[str] = None
        self._topic: Optional[str] = None  # 群组推送主题（可选）

        if config:
            self._token = getattr(config, "PUSHPLUS_TOKEN", None)
            self._topic = getattr(config, "PUSHPLUS_TOPIC", None)

        if not self._token:
            try:
                from src.config.settings import settings

                self._token = getattr(settings, "PUSHPLUS_TOKEN", None)
                self._topic = self._topic or getattr(settings, "PUSHPLUS_TOPIC", None)
            except Exception:
                pass

    def is_available(self) -> bool:
        """是否已配置"""
        return bool(self._token)

    def send(self, content: str, title: str = "FinanceSail 市场报告") -> bool:
        """
        发送 PushPlus 推送

        Args:
            content: 消息内容（支持 HTML/Markdown）
            title: 消息标题

        Returns:
            bool: 是否发送成功
        """
        if not self.is_available():
            logger.debug("PushPlus 未配置，跳过")
            return False

        import httpx

        payload = {
            "token": self._token,
            "title": title,
            "content": content,
            "template": "markdown",
        }

        # 群组推送
        if self._topic:
            payload["topic"] = self._topic

        try:
            resp = httpx.post(_PUSHPLUS_API, json=payload, timeout=15)
            data = resp.json()
            if data.get("code") == 200:
                logger.info("PushPlus 发送成功")
                return True
            else:
                logger.error(f"PushPlus 发送失败: {data}")
                return False
        except Exception as e:
            logger.error(f"PushPlus 发送异常: {e}")
            return False
