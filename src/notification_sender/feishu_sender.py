"""
飞书 Webhook 发送器
"""

from typing import Optional, List

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# 飞书单条消息字节上限
_FEISHU_MAX_BYTES = 20000


class FeishuSender:
    """飞书 Webhook 通知"""

    def __init__(self, config=None):
        self._webhook_url: Optional[str] = None
        if config:
            self._webhook_url = getattr(config, "FEISHU_WEBHOOK_URL", None)
        if not self._webhook_url:
            try:
                from src.config.settings import settings

                self._webhook_url = getattr(settings, "FEISHU_WEBHOOK_URL", None)
            except Exception:
                pass

    def is_available(self) -> bool:
        """是否已配置"""
        return bool(self._webhook_url)

    def send(self, content: str) -> bool:
        """
        发送消息，超出 20000 字节自动分块

        Args:
            content: 消息内容（Markdown/文本格式）

        Returns:
            bool: 至少一块发送成功则返回 True
        """
        if not self._webhook_url:
            logger.debug("飞书 Webhook 未配置，跳过")
            return False

        chunks = self._split_content(content)
        success = False
        for chunk in chunks:
            ok = self._send_feishu(chunk)
            if ok:
                success = True
        return success

    def _split_content(self, content: str) -> List[str]:
        """按字节上限分块"""
        encoded = content.encode("utf-8")
        if len(encoded) <= _FEISHU_MAX_BYTES:
            return [content]

        chunks: List[str] = []
        while content:
            lo, hi = 0, len(content)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if len(content[:mid].encode("utf-8")) <= _FEISHU_MAX_BYTES:
                    lo = mid
                else:
                    hi = mid - 1
            chunks.append(content[:lo])
            content = content[lo:]
        return chunks

    def _send_feishu(self, content: str) -> bool:
        """
        发送单块消息到飞书

        飞书 Webhook 格式：
        POST <webhook_url>
        {"msg_type": "text", "content": {"text": "<content>"}}
        """
        import httpx

        payload = {
            "msg_type": "text",
            "content": {"text": content},
        }

        try:
            resp = httpx.post(self._webhook_url, json=payload, timeout=10)
            data = resp.json()
            # 飞书成功返回 {"StatusCode": 0, ...} 或 {"code": 0, ...}
            code = data.get("StatusCode", data.get("code", -1))
            if code == 0:
                logger.info("飞书发送成功")
                return True
            else:
                logger.error(f"飞书发送失败: {data}")
                return False
        except Exception as e:
            logger.error(f"飞书发送异常: {e}")
            return False
