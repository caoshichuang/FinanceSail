"""
Telegram Bot 发送器
"""

from typing import Optional

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Telegram 单条消息字符上限
_TG_MAX_CHARS = 4096


class TelegramSender:
    """Telegram Bot 通知"""

    def __init__(self, config=None):
        self._bot_token: Optional[str] = None
        self._chat_id: Optional[str] = None

        if config:
            self._bot_token = getattr(config, "TELEGRAM_BOT_TOKEN", None)
            self._chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)

        if not self._bot_token or not self._chat_id:
            try:
                from src.config.settings import settings

                self._bot_token = self._bot_token or getattr(
                    settings, "TELEGRAM_BOT_TOKEN", None
                )
                self._chat_id = self._chat_id or getattr(
                    settings, "TELEGRAM_CHAT_ID", None
                )
            except Exception:
                pass

    def is_available(self) -> bool:
        """是否已配置"""
        return bool(self._bot_token and self._chat_id)

    def send(self, content: str) -> bool:
        """
        发送消息，超出 4096 字符自动分块

        Args:
            content: 消息内容（支持 Markdown）

        Returns:
            bool: 至少一块发送成功则返回 True
        """
        if not self.is_available():
            logger.debug("Telegram 未配置，跳过")
            return False

        chunks = self._split_content(content)
        success = False
        for chunk in chunks:
            ok = self._send_message(chunk)
            if ok:
                success = True
        return success

    def _split_content(self, content: str) -> list:
        """按字符上限分块"""
        if len(content) <= _TG_MAX_CHARS:
            return [content]
        chunks = []
        while content:
            chunks.append(content[:_TG_MAX_CHARS])
            content = content[_TG_MAX_CHARS:]
        return chunks

    def _send_message(self, text: str) -> bool:
        """
        通过 Telegram Bot API 发送消息

        API: POST https://api.telegram.org/bot<token>/sendMessage
        """
        import httpx

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            resp = httpx.post(url, json=payload, timeout=15)
            data = resp.json()
            if data.get("ok"):
                logger.info("Telegram 发送成功")
                return True
            else:
                logger.error(f"Telegram 发送失败: {data}")
                # 如果 Markdown 解析失败，降级为纯文本重试
                if data.get("error_code") == 400:
                    payload.pop("parse_mode", None)
                    resp2 = httpx.post(url, json=payload, timeout=15)
                    data2 = resp2.json()
                    if data2.get("ok"):
                        logger.info("Telegram 降级纯文本发送成功")
                        return True
                return False
        except Exception as e:
            logger.error(f"Telegram 发送异常: {e}")
            return False
