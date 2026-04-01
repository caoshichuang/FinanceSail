"""
企业微信 Webhook 发送器
"""

from typing import Optional, List

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# 企业微信单条消息字节上限
_WECHAT_MAX_BYTES = 4000


class WechatSender:
    """企业微信 Webhook 通知"""

    def __init__(self, config=None):
        self._webhook_url: Optional[str] = None
        if config:
            self._webhook_url = getattr(config, "WECHAT_WEBHOOK_URL", None)
        if not self._webhook_url:
            try:
                from src.config.settings import settings

                self._webhook_url = getattr(settings, "WECHAT_WEBHOOK_URL", None)
            except Exception:
                pass

    def is_available(self) -> bool:
        """是否已配置"""
        return bool(self._webhook_url)

    # 保留旧方法名兼容
    def is_wechat_configured(self) -> bool:
        return self.is_available()

    def send(self, content: str, msg_type: str = "markdown") -> bool:
        """
        发送消息，超出 4000 字节自动分块

        Args:
            content: 消息内容（Markdown 格式）
            msg_type: 消息类型（text/markdown）

        Returns:
            bool: 至少一块发送成功则返回 True
        """
        if not self._webhook_url:
            logger.debug("企业微信 Webhook 未配置，跳过")
            return False

        chunks = self._split_content(content)
        success = False
        for chunk in chunks:
            ok = self._send_wechat(chunk, msg_type)
            if ok:
                success = True
        return success

    def _split_content(self, content: str) -> List[str]:
        """
        按字节上限分块
        """
        encoded = content.encode("utf-8")
        if len(encoded) <= _WECHAT_MAX_BYTES:
            return [content]

        chunks: List[str] = []
        while content:
            # 二分搜索安全截断点
            lo, hi = 0, len(content)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if len(content[:mid].encode("utf-8")) <= _WECHAT_MAX_BYTES:
                    lo = mid
                else:
                    hi = mid - 1
            chunks.append(content[:lo])
            content = content[lo:]
        return chunks

    def _send_wechat(self, content: str, msg_type: str = "markdown") -> bool:
        """
        发送单块消息到企业微信

        Args:
            content: 消息内容
            msg_type: 消息类型（text/markdown）

        Returns:
            bool: 是否发送成功
        """
        import httpx

        payload = {
            "msgtype": msg_type,
            msg_type: {"content": content},
        }

        try:
            resp = httpx.post(self._webhook_url, json=payload, timeout=10)
            data = resp.json()
            if data.get("errcode") == 0:
                logger.info("企业微信发送成功")
                return True
            else:
                logger.error(f"企业微信发送失败: {data}")
                return False
        except Exception as e:
            logger.error(f"企业微信发送异常: {e}")
            return False
