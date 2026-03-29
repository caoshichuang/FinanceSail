"""
今日头条分发模块
"""

import json
import requests
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from ..config.settings import settings


class ToutiaoPublisher:
    """今日头条发布器"""

    def __init__(self, access_token: str = None):
        self.logger = get_logger(self.__class__.__name__)
        self.access_token = access_token or getattr(
            settings, "TOUTIAO_ACCESS_TOKEN", ""
        )
        self.base_url = "https://open.toutiao.com"

    def create_article(
        self,
        title: str,
        content: str,
        cover_images: List[str] = None,
        abstract: str = "",
        article_type: int = 0,
    ) -> Optional[str]:
        """
        创建文章

        Args:
            title: 标题
            content: 正文内容（HTML格式）
            cover_images: 封面图URL列表
            abstract: 摘要
            article_type: 文章类型（0=文章，1=图集）

        Returns:
            str: 文章ID，失败返回None
        """
        url = f"{self.base_url}/api/apps/article/publish/v2"

        # 处理摘要（限制120字）
        if not abstract:
            abstract = content[:120] if len(content) > 120 else content
        abstract = abstract[:120]

        # 处理标题（限制30字）
        title = title[:30] if len(title) > 30 else title

        payload = {
            "access_token": self.access_token,
            "title": title,
            "content": content,
            "abstract": abstract,
            "article_type": article_type,
        }

        # 添加封面图
        if cover_images:
            payload["cover_images"] = cover_images[:3]  # 最多3张

        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()

            if data.get("success"):
                article_id = data.get("data", {}).get("article_id")
                self.logger.info(f"创建文章成功: {article_id}")
                return article_id
            else:
                self.logger.error(f"创建文章失败: {data}")
                return None
        except Exception as e:
            self.logger.error(f"创建文章异常: {e}")
            return None

    def publish_article(self, article_id: str) -> bool:
        """
        发布文章

        Args:
            article_id: 文章ID

        Returns:
            bool: 是否成功
        """
        url = f"{self.base_url}/api/apps/article/publish"

        payload = {
            "access_token": self.access_token,
            "article_id": article_id,
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()

            if data.get("success"):
                self.logger.info(f"发布文章成功: {article_id}")
                return True
            else:
                self.logger.error(f"发布文章失败: {data}")
                return False
        except Exception as e:
            self.logger.error(f"发布文章异常: {e}")
            return False

    def get_article_status(self, article_id: str) -> Dict[str, Any]:
        """
        获取文章状态

        Args:
            article_id: 文章ID

        Returns:
            Dict: 文章状态
        """
        url = f"{self.base_url}/api/apps/article/detail"

        params = {
            "access_token": self.access_token,
            "article_id": article_id,
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if data.get("success"):
                article_data = data.get("data", {})
                return {
                    "status": "published"
                    if article_data.get("status") == 1
                    else "draft",
                    "data": article_data,
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("message", "Unknown error"),
                }
        except Exception as e:
            self.logger.error(f"获取文章状态异常: {e}")
            return {"status": "error", "message": str(e)}

    def format_content_for_toutiao(
        self, title: str, content: str, tags: List[str]
    ) -> str:
        """
        格式化内容为今日头条格式

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
