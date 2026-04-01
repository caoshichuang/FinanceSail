"""
SMTP 邮件发送器（迁移自 src/notifiers/email.py，统一接口）
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Optional, List

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class EmailSender:
    """SMTP 邮件通知"""

    def __init__(self, config=None):
        self._smtp_server: str = "smtp.qq.com"
        self._smtp_port: int = 465
        self._sender: Optional[str] = None
        self._password: Optional[str] = None
        self._receivers: List[str] = []

        # 优先从传入 config 读取
        if config:
            self._smtp_server = getattr(config, "SMTP_SERVER", self._smtp_server)
            self._smtp_port = getattr(config, "SMTP_PORT", self._smtp_port)
            self._sender = getattr(config, "EMAIL_SENDER", None) or getattr(
                config, "QQ_EMAIL", None
            )
            self._password = getattr(config, "EMAIL_PASSWORD", None) or getattr(
                config, "QQ_EMAIL_AUTH_CODE", None
            )
            receivers_raw = getattr(config, "EMAIL_RECEIVERS", None) or getattr(
                config, "RECEIVER_EMAIL", None
            )
            self._receivers = self._parse_receivers(receivers_raw)

        # fallback 从全局 settings 读取
        if not self._sender or not self._password:
            try:
                from src.config.settings import settings

                self._smtp_server = getattr(settings, "SMTP_SERVER", self._smtp_server)
                self._smtp_port = getattr(settings, "SMTP_PORT", self._smtp_port)
                self._sender = (
                    self._sender
                    or getattr(settings, "EMAIL_SENDER", None)
                    or getattr(settings, "QQ_EMAIL", None)
                )
                self._password = (
                    self._password
                    or getattr(settings, "EMAIL_PASSWORD", None)
                    or getattr(settings, "QQ_EMAIL_AUTH_CODE", None)
                )
                if not self._receivers:
                    receivers_raw = getattr(
                        settings, "EMAIL_RECEIVERS", None
                    ) or getattr(settings, "RECEIVER_EMAIL", None)
                    self._receivers = self._parse_receivers(receivers_raw)
            except Exception:
                pass

    def is_available(self) -> bool:
        """是否已配置"""
        return bool(self._sender and self._password and self._receivers)

    def send(
        self,
        content: str,
        subject: str = "FinanceSail 市场报告",
        attachments: Optional[List[Path]] = None,
    ) -> bool:
        """
        发送邮件

        Args:
            content: 正文内容（纯文本或 HTML）
            subject: 邮件主题
            attachments: 附件路径列表

        Returns:
            bool: 是否发送成功
        """
        if not self.is_available():
            logger.debug("邮件发送器未配置，跳过")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self._sender
            msg["To"] = ", ".join(self._receivers)
            msg["Subject"] = subject

            # 判断内容类型
            content_type = "html" if content.strip().startswith("<") else "plain"
            msg.attach(MIMEText(content, content_type, "utf-8"))

            # 添加图片附件
            if attachments:
                for file_path in attachments:
                    if file_path.exists() and file_path.suffix.lower() in (
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".gif",
                    ):
                        self._attach_file(msg, file_path)

            with smtplib.SMTP_SSL(self._smtp_server, self._smtp_port) as server:
                server.login(self._sender, self._password)
                server.send_message(msg)

            logger.info(f"邮件发送成功: {subject} → {self._receivers}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def send_error(self, error_message: str, task_name: str = "") -> bool:
        """发送错误通知邮件"""
        subject = f"[错误] {task_name} 任务失败"
        body = f"任务执行失败\n\n任务名称：{task_name}\n错误信息：\n{error_message}\n\n请检查日志获取更多详情。"
        return self.send(body, subject)

    def _parse_receivers(self, raw: Optional[str]) -> List[str]:
        """解析收件人（支持逗号分隔多个地址）"""
        if not raw:
            return []
        return [r.strip() for r in raw.split(",") if r.strip()]

    def _attach_file(self, msg: MIMEMultipart, file_path: Path) -> None:
        """添加附件"""
        with open(file_path, "rb") as f:
            attachment = MIMEApplication(f.read())
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=file_path.name,
            )
            msg.attach(attachment)
