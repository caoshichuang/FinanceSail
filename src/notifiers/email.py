"""
邮件通知模块
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Dict, Any
from ..config.settings import settings
from ..config.constants import EMAIL_SUBJECT_TEMPLATE
from ..utils.logger import get_logger
from ..utils.retry import sync_retry
from ..exceptions.errors import EmailError


class EmailNotifier:
    """QQ邮件通知器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.sender = settings.QQ_EMAIL
        self.password = settings.QQ_EMAIL_AUTH_CODE
        self.receiver = settings.RECEIVER_EMAIL

    @sync_retry(max_retries=3, delay=2)
    def send(
        self,
        market: str,
        titles: List[str],
        content: str,
        tags: List[str],
        attachments: List[Path] = None,
        date: str = None,
    ):
        """
        发送邮件

        Args:
            market: 市场类型
            titles: 标题列表
            content: 正文内容
            tags: 标签列表
            attachments: 附件列表
            date: 日期
        """
        try:
            # 构建邮件主题
            subject = self._build_subject(market, titles[0] if titles else "", date)

            # 构建邮件
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = self.receiver
            msg["Subject"] = subject

            # 邮件正文
            body = self._build_body(titles, content, tags)
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # 添加附件
            if attachments:
                for file_path in attachments:
                    if file_path.exists():
                        self._attach_file(msg, file_path)

            # 发送
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)

            self.logger.info(f"邮件发送成功: {subject}")

        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
            raise EmailError(f"邮件发送失败: {e}") from e

    def send_error(self, error_message: str, task_name: str = ""):
        """
        发送错误通知邮件

        Args:
            error_message: 错误信息
            task_name: 任务名称
        """
        try:
            subject = f"[错误] {task_name} 任务失败"
            body = f"""
任务执行失败

任务名称：{task_name}
错误信息：
{error_message}

请检查日志获取更多详情。
"""

            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = self.receiver
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)

            self.logger.info(f"错误通知邮件发送成功: {subject}")

        except Exception as e:
            self.logger.error(f"错误通知邮件发送失败: {e}")

    def _build_subject(self, market: str, title: str, date: str = None) -> str:
        """构建邮件主题"""
        template = EMAIL_SUBJECT_TEMPLATE.get(market, "[市场] {date}｜{title}")
        date = date or ""
        return template.format(date=date, title=title[:30])

    def _build_body(self, titles: List[str], content: str, tags: List[str]) -> str:
        """构建邮件正文"""
        body = "📊 今日市场总结\n\n"

        # 标题选项
        body += "【标题选项】\n"
        for i, title in enumerate(titles, 1):
            body += f"{i}. {title}\n"

        body += "\n【完整文案】\n"
        body += "-" * 40 + "\n"
        body += content
        body += "\n" + "-" * 40 + "\n"

        # 标签
        body += "\n【标签】\n"
        body += " ".join(tags)

        body += "\n\n📎 附件：图片zip包"

        return body

    def _attach_file(self, msg: MIMEMultipart, file_path: Path):
        """添加附件"""
        with open(file_path, "rb") as f:
            attachment = MIMEApplication(f.read())
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=file_path.name,
            )
            msg.attach(attachment)
