"""
市场总结生成器模块
"""

import json
from typing import Dict, Any, List
from .base import BaseGenerator
from .prompts.us_summary import US_SUMMARY_SYSTEM_PROMPT, US_SUMMARY_PROMPT_TEMPLATE
from .prompts.a_share_summary import (
    A_SHARE_SUMMARY_SYSTEM_PROMPT,
    A_SHARE_SUMMARY_PROMPT_TEMPLATE,
)
from .prompts.hk_summary import HK_SUMMARY_SYSTEM_PROMPT, HK_SUMMARY_PROMPT_TEMPLATE
from ..config.constants import MarketType
from ..exceptions.errors import ContentGenerationError


class MarketSummaryGenerator(BaseGenerator):
    """市场总结生成器"""

    def __init__(self, market: str):
        """
        初始化

        Args:
            market: 市场类型（A股/美股/港股）
        """
        super().__init__()
        self.market = market

    async def _generate_titles(self, data: Dict[str, Any]) -> List[str]:
        """
        生成标题

        Args:
            data: 输入数据

        Returns:
            List[str]: 标题列表
        """
        try:
            prompt = self._build_titles_prompt(data)
            system_prompt = self._get_system_prompt()

            response = self._call_ai(prompt, system_prompt)

            # 清理响应，提取JSON
            json_str = self._extract_json(response)
            result = json.loads(json_str)
            return result.get("titles", [])
        except Exception as e:
            self.logger.error(f"标题生成失败: {e}")
            return self._extract_titles_from_text(response)

    async def _generate_cards(self, data: Dict[str, Any]) -> List[str]:
        """
        生成字卡内容

        Args:
            data: 输入数据

        Returns:
            List[str]: 字卡内容列表
        """
        try:
            prompt = self._build_cards_prompt(data)
            system_prompt = self._get_system_prompt()

            response = self._call_ai(prompt, system_prompt)

            # 清理响应，提取JSON
            json_str = self._extract_json(response)
            result = json.loads(json_str)
            return result.get("cards", [])
        except Exception as e:
            self.logger.error(f"字卡生成失败: {e}")
            return self._extract_cards_from_text(response)

    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON"""
        import re

        # 尝试找到 ```json ... ``` 格式
        match = re.search(r"```json\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 尝试找到 {...} 格式
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0).strip()

        # 返回原始文本
        return text

    def _get_system_prompt(self) -> str:
        """获取系统提示"""
        if self.market == MarketType.US_STOCK:
            return US_SUMMARY_SYSTEM_PROMPT
        elif self.market == MarketType.A_SHARE:
            return A_SHARE_SUMMARY_SYSTEM_PROMPT
        elif self.market == MarketType.HK_STOCK:
            return HK_SUMMARY_SYSTEM_PROMPT
        else:
            raise ContentGenerationError(f"不支持的市场类型: {self.market}")

    def _build_titles_prompt(self, data: Dict[str, Any]) -> str:
        """构建标题生成提示"""
        return self._build_prompt(data)

    def _build_cards_prompt(self, data: Dict[str, Any]) -> str:
        """构建字卡生成提示"""
        return self._build_prompt(data)

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """构建完整提示"""
        if self.market == MarketType.US_STOCK:
            return US_SUMMARY_PROMPT_TEMPLATE.format(
                indices=json.dumps(
                    data.get("indices", {}), ensure_ascii=False, indent=2
                ),
                chinese_stocks=json.dumps(
                    data.get("chinese_stocks", []), ensure_ascii=False, indent=2
                ),
                star_stocks=json.dumps(
                    data.get("star_stocks", []), ensure_ascii=False, indent=2
                ),
            )
        elif self.market == MarketType.A_SHARE:
            return A_SHARE_SUMMARY_PROMPT_TEMPLATE.format(
                indices=json.dumps(
                    data.get("indices", {}), ensure_ascii=False, indent=2
                ),
                distribution=json.dumps(
                    data.get("distribution", {}), ensure_ascii=False, indent=2
                ),
                hot_sectors=json.dumps(
                    data.get("hot_sectors", []), ensure_ascii=False, indent=2
                ),
                star_stocks=json.dumps(
                    data.get("star_stocks", []), ensure_ascii=False, indent=2
                ),
                capital_flow=json.dumps(
                    data.get("capital_flow", {}), ensure_ascii=False, indent=2
                ),
                limit_stocks=json.dumps(
                    {
                        "涨跌停": data.get("limit_up", []) + data.get("limit_down", []),
                        "热点股": data.get("hot_stocks", []),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        elif self.market == MarketType.HK_STOCK:
            return HK_SUMMARY_PROMPT_TEMPLATE.format(
                indices=json.dumps(
                    data.get("indices", {}), ensure_ascii=False, indent=2
                ),
                star_stocks=json.dumps(
                    data.get("star_stocks", []), ensure_ascii=False, indent=2
                ),
                capital_flow=json.dumps(
                    data.get("capital_flow", {}), ensure_ascii=False, indent=2
                ),
            )
        else:
            raise ContentGenerationError(f"不支持的市场类型: {self.market}")

    def _extract_titles_from_text(self, text: str) -> List[str]:
        """从文本中提取标题"""
        # 简单实现：按行分割，取前3行
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return lines[:3] if lines else ["今日市场总结"]

    def _extract_cards_from_text(self, text: str) -> List[str]:
        """从文本中提取字卡"""
        # 简单实现：按空行分割
        cards = [card.strip() for card in text.split("\n\n") if card.strip()]
        return cards if cards else [text]
