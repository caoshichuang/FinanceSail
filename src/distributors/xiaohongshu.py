"""
小红书分发模块
"""

import json
from typing import Dict, List, Any
from ..utils.logger import get_logger
from ..config.settings import settings


class XiaohongshuPublisher:
    """小红书发布器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def format_content(
        self, title: str, content: str, tags: List[str]
    ) -> Dict[str, Any]:
        """
        格式化内容为小红书格式

        Args:
            title: 标题
            content: 正文内容
            tags: 标签列表

        Returns:
            Dict: 格式化后的内容
        """
        # 小红书标题限制20字
        short_title = title[:20] if len(title) > 20 else title

        # 小红书正文限制1000字
        short_content = content[:1000] if len(content) > 1000 else content

        # 格式化标签（小红书用#标签）
        formatted_tags = []
        for tag in tags[:10]:  # 最多10个标签
            formatted_tags.append(f"#{tag}")

        return {
            "title": short_title,
            "content": short_content,
            "tags": formatted_tags,
            "full_content": f"{short_content}\n\n{' '.join(formatted_tags)}",
        }

    def generate_publish_instructions(
        self, formatted_content: Dict[str, Any], image_urls: List[str]
    ) -> str:
        """
        生成发布指引

        Args:
            formatted_content: 格式化后的内容
            image_urls: 图片URL列表

        Returns:
            str: 发布指引文本
        """
        instructions = f"""
📱 小红书发布指引

1️⃣ 打开小红书App
2️⃣ 点击底部"+"按钮
3️⃣ 选择"图文"发布

📋 复制以下内容：

【标题】
{formatted_content["title"]}

【正文】
{formatted_content["full_content"]}

🖼️ 图片顺序（共{len(image_urls)}张）：
- 第1张：封面图
- 第2张起：内容卡片

⚠️ 注意事项：
- 标题最多20字
- 正文最多1000字
- 图片最多9张
- 标签前加#号
"""
        return instructions

    def get_image_download_urls(self, base_url: str, content_id: int) -> List[str]:
        """
        获取图片下载URL

        Args:
            base_url: 基础URL
            content_id: 内容ID

        Returns:
            List[str]: 图片URL列表
        """
        # 这里需要根据实际的图片路径来生成URL
        # 暂时返回空列表，需要在实际使用时填充
        return []

    def validate_content(self, formatted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证内容是否符合小红书规范

        Args:
            formatted_content: 格式化后的内容

        Returns:
            Dict: 验证结果
        """
        errors = []
        warnings = []

        # 检查标题长度
        if len(formatted_content["title"]) > 20:
            errors.append("标题超过20字限制")

        # 检查正文长度
        if len(formatted_content["content"]) > 1000:
            warnings.append("正文超过1000字，已截断")

        # 检查标签数量
        if len(formatted_content["tags"]) > 10:
            warnings.append("标签超过10个，已截断")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
