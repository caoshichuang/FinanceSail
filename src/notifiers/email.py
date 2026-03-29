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
        content_id: int = None,
        cover_image: Path = None,
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
            content_id: 内容ID（用于预览链接）
            cover_image: 封面图片路径
        """
        try:
            # 构建邮件主题
            subject = self._build_subject(market, titles[0] if titles else "", date)

            # 构建邮件
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = self.receiver
            msg["Subject"] = subject

            # 邮件正文（HTML格式）
            body = self._build_html_body(titles, content, tags, content_id, cover_image)
            msg.attach(MIMEText(body, "html", "utf-8"))

            # 添加附件（仅保留图片附件，移除zip）
            if attachments:
                for file_path in attachments:
                    if file_path.exists() and file_path.suffix.lower() in [
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".gif",
                    ]:
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
        """构建邮件正文（纯文本，兼容旧版本）"""
        body = "⛵ FinanceSail - Daily Market Summary\n\n"

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

        body += "\n\n" + "-" * 40
        body += "\n⛵ FinanceSail - Automated Financial Content Distribution"
        body += "\n📊 Data Source: AKShare, East Money"

        return body

    def _build_html_body(
        self,
        titles: List[str],
        content: str,
        tags: List[str],
        content_id: int = None,
        cover_image: Path = None,
    ) -> str:
        """构建HTML邮件正文"""
        # 生成预览链接
        preview_url = ""
        copy_url = ""
        if content_id:
            base_url = getattr(settings, "BASE_URL", "http://139.224.40.205:8080")
            preview_url = f"{base_url}/preview/{content_id}"
            copy_url = f"{base_url}/preview/{content_id}?copy=true"

        # 生成封面图片HTML
        cover_html = ""
        if cover_image and cover_image.exists():
            # 使用base64编码图片（内嵌）
            import base64

            with open(cover_image, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            cover_html = f"""
            <div style="margin-bottom: 20px;">
                <img src="data:image/png;base64,{image_data}" 
                     alt="Cover" 
                     style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            </div>"""

        # 生成标题选项HTML
        titles_html = ""
        for i, title in enumerate(titles, 1):
            titles_html += f'<div style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>{i}.</strong> {title}</div>'

        # 生成标签HTML
        tags_html = ""
        if tags:
            tags_list = " ".join(tags)
            tags_html = f"""
            <div style="margin-top: 20px;">
                <h3 style="color: #303133; margin-bottom: 10px;">🏷️ Tags</h3>
                <div style="background: #ecf5ff; color: #409eff; padding: 12px; border-radius: 8px; font-size: 14px;">
                    {tags_list}
                </div>
            </div>"""

        # 生成操作按钮HTML
        actions_html = ""
        if preview_url:
            actions_html = f'''
            <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #eee; text-align: center;">
                <a href="{preview_url}" 
                   style="display: inline-block; background: #409eff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 0 8px; font-weight: 500;">
                    📱 View Preview
                </a>
                <a href="{copy_url}" 
                   style="display: inline-block; background: #67c23a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 0 8px; font-weight: 500;">
                    📋 Copy Content
                </a>
            </div>'''

        # 组装HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #303133; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #409eff 0%, #67c23a 100%); color: white; padding: 20px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">⛵ FinanceSail</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">Daily Market Summary</p>
            </div>
            
            <div style="background: #fff; padding: 24px; border: 1px solid #ebeef5; border-radius: 0 0 12px 12px;">
                {cover_html}
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #303133; margin-bottom: 10px;">📊 Title Options</h3>
                    {titles_html}
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #303133; margin-bottom: 10px;">📝 Content</h3>
                    <div style="background: #f5f7fa; padding: 16px; border-radius: 8px; white-space: pre-wrap; font-family: 'SF Mono', Monaco, monospace; font-size: 14px;">
                        {content}
                    </div>
                </div>
                
                {tags_html}
                {actions_html}
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #909399; font-size: 12px;">
                    <p>⛵ FinanceSail - Automated Financial Content Distribution</p>
                    <p>📊 Data Source: AKShare, East Money</p>
                </div>
            </div>
        </body>
        </html>"""

        return html

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
