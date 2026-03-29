"""
微信公众号分发模块
"""

import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..utils.logger import get_logger
from ..config.settings import settings


class WeChatPublisher:
    """微信公众号发布器"""

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.logger = get_logger(self.__class__.__name__)
        self.app_id = app_id or getattr(settings, "WECHAT_APP_ID", "")
        self.app_secret = app_secret or getattr(settings, "WECHAT_APP_SECRET", "")
        self.access_token = None
        self.token_expires_at = None

    def get_access_token(self) -> Optional[str]:
        """
        获取access_token

        Returns:
            str: access_token，失败返回None
        """
        # 检查token是否过期
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token

        # 获取新token
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if "access_token" in data:
                self.access_token = data["access_token"]
                # token有效期7200秒，提前5分钟刷新
                self.token_expires_at = datetime.now() + timedelta(
                    seconds=data["expires_in"] - 300
                )
                self.logger.info("获取access_token成功")
                return self.access_token
            else:
                self.logger.error(f"获取access_token失败: {data}")
                return None
        except Exception as e:
            self.logger.error(f"获取access_token异常: {e}")
            return None

    def upload_image(self, image_url: str) -> Optional[str]:
        """
        上传图片到微信服务器

        Args:
            image_url: 图片URL

        Returns:
            str: 媒体ID，失败返回None
        """
        token = self.get_access_token()
        if not token:
            return None

        url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={token}&type=image"

        try:
            # 下载图片
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()

            # 上传到微信
            files = {"media": ("image.jpg", img_response.content, "image/jpeg")}
            response = requests.post(url, files=files, timeout=30)
            data = response.json()

            if "media_id" in data:
                self.logger.info(f"上传图片成功: {data['media_id']}")
                return data["media_id"]
            else:
                self.logger.error(f"上传图片失败: {data}")
                return None
        except Exception as e:
            self.logger.error(f"上传图片异常: {e}")
            return None

    def create_draft(
        self,
        title: str,
        content: str,
        thumb_media_id: str,
        author: str = "FinanceSail",
        digest: str = "",
        content_source_url: str = "",
    ) -> Optional[str]:
        """
        创建草稿

        Args:
            title: 标题
            content: 正文（HTML格式）
            thumb_media_id: 封面图媒体ID
            author: 作者
            digest: 摘要
            content_source_url: 原文链接

        Returns:
            str: 媒体文章ID，失败返回None
        """
        token = self.get_access_token()
        if not token:
            return None

        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

        # 处理摘要（限制54字）
        if not digest:
            digest = content[:54] if len(content) > 54 else content
        digest = digest[:54]

        # 处理标题（限制64字）
        title = title[:64] if len(title) > 64 else title

        articles = [
            {
                "title": title,
                "author": author,
                "digest": digest,
                "content": content,
                "content_source_url": content_source_url,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]

        try:
            response = requests.post(url, json={"articles": articles}, timeout=30)
            data = response.json()

            if "media_id" in data:
                self.logger.info(f"创建草稿成功: {data['media_id']}")
                return data["media_id"]
            else:
                self.logger.error(f"创建草稿失败: {data}")
                return None
        except Exception as e:
            self.logger.error(f"创建草稿异常: {e}")
            return None

    def publish_article(self, media_id: str) -> Optional[str]:
        """
        发布文章

        Args:
            media_id: 媒体文章ID

        Returns:
            str: 发布任务ID，失败返回None
        """
        token = self.get_access_token()
        if not token:
            return None

        url = (
            f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
        )

        try:
            response = requests.post(url, json={"media_id": media_id}, timeout=30)
            data = response.json()

            if "publish_id" in data:
                self.logger.info(f"发布文章成功: {data['publish_id']}")
                return data["publish_id"]
            else:
                self.logger.error(f"发布文章失败: {data}")
                return None
        except Exception as e:
            self.logger.error(f"发布文章异常: {e}")
            return None

    def check_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """
        检查发布状态

        Args:
            publish_id: 发布任务ID

        Returns:
            Dict: 发布状态
        """
        token = self.get_access_token()
        if not token:
            return {"status": "error", "message": "获取token失败"}

        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token={token}"

        try:
            response = requests.post(url, json={"publish_id": publish_id}, timeout=30)
            data = response.json()

            # publish_status: 0=成功, 1=发布中, 2=原创失败, 3=常规失败, 4=审核失败
            status_map = {
                0: "success",
                1: "publishing",
                2: "failed",
                3: "failed",
                4: "failed",
            }

            return {
                "status": status_map.get(data.get("publish_status", -1), "unknown"),
                "data": data,
            }
        except Exception as e:
            self.logger.error(f"检查发布状态异常: {e}")
            return {"status": "error", "message": str(e)}

    def format_content_for_wechat(
        self, title: str, content: str, tags: List[str]
    ) -> str:
        """
        格式化内容为微信公众号格式

        Args:
            title: 标题
            content: 正文内容
            tags: 标签列表

        Returns:
            str: HTML格式的内容
        """
        # 将换行符转换为<br>
        content_html = content.replace("\n", "<br>")

        # 添加标签
        tags_html = ""
        if tags:
            tags_list = " ".join([f"#{tag}" for tag in tags[:5]])
            tags_html = f'<p style="color: #888; font-size: 14px;">{tags_list}</p>'

        # 组装HTML
        html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.8; color: #333;">
    <p>{content_html}</p>
    {tags_html}
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #888; font-size: 12px;">数据来源：AKShare、东方财富</p>
</div>
"""
        return html
