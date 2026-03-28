"""
内容生成基类模块
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import openai
from ..config.settings import settings
from ..config.constants import DISCLAIMER
from ..utils.logger import get_logger
from ..utils.retry import retry
from ..utils.sanitizer import sanitizer
from ..exceptions.errors import AIModelError, ContentValidationError


class BaseGenerator(ABC):
    """内容生成基类"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.client = openai.OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )

    async def generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成内容

        Args:
            data: 输入数据

        Returns:
            Dict[str, Any]: 生成的内容（titles, content, tags）
        """
        try:
            # 生成标题
            titles = await self._generate_titles(data)

            # 生成正文
            cards = await self._generate_cards(data)

            # 生成标签
            tags = self._generate_tags(data)

            # 组装完整内容
            content = self._assemble_content(cards)

            # 校验内容
            self._validate_content({"titles": titles, "content": content, "tags": tags})

            return {
                "titles": titles,
                "cards": cards,
                "content": content,
                "tags": tags,
            }
        except Exception as e:
            self.logger.error(f"内容生成失败: {e}")
            raise

    @abstractmethod
    async def _generate_titles(self, data: Dict[str, Any]) -> List[str]:
        """
        生成标题（子类实现）

        Args:
            data: 输入数据

        Returns:
            List[str]: 标题列表
        """
        pass

    @abstractmethod
    async def _generate_cards(self, data: Dict[str, Any]) -> List[str]:
        """
        生成字卡内容（子类实现）

        Args:
            data: 输入数据

        Returns:
            List[str]: 字卡内容列表
        """
        pass

    def _generate_tags(self, data: Dict[str, Any]) -> List[str]:
        """
        生成标签

        Args:
            data: 输入数据

        Returns:
            List[str]: 标签列表
        """
        market = data.get("market", "")
        tags = ["#股票", "#投资理财"]

        if market == "A股":
            tags.extend(["#A股", "#股市分析"])
        elif market == "美股":
            tags.extend(["#美股", "#纳斯达克"])
        elif market == "港股":
            tags.extend(["#港股", "#恒生指数"])

        return tags

    def _assemble_content(self, cards: List[str]) -> str:
        """
        组装完整内容

        Args:
            cards: 字卡内容列表

        Returns:
            str: 完整内容
        """
        content = "\n\n".join(cards)
        content += "\n\n" + DISCLAIMER
        return content

    def _validate_content(self, content: Dict[str, Any]):
        """
        校验内容

        Args:
            content: 生成的内容
        """
        # 检查敏感词
        text = " ".join(content.get("titles", [])) + " " + content.get("content", "")
        if not sanitizer.validate(text):
            self.logger.warning("内容包含敏感词，但继续处理")

    def _call_ai(self, prompt: str, system_prompt: str = None) -> str:
        """
        调用AI模型

        Args:
            prompt: 用户提示
            system_prompt: 系统提示

        Returns:
            str: AI响应
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )

            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"AI调用失败: {e}")
            raise AIModelError(f"AI调用失败: {e}") from e
