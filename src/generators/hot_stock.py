"""
热点个股分析生成器模块
"""

import json
from typing import Dict, Any, List
from .base import BaseGenerator
from .prompts.hot_stock import HOT_STOCK_SYSTEM_PROMPT, HOT_STOCK_PROMPT_TEMPLATE
from ..config.constants import ContentType
from ..exceptions.errors import ContentGenerationError


class HotStockGenerator(BaseGenerator):
    """热点个股分析生成器"""

    async def _generate_titles(self, data: Dict[str, Any]) -> List[str]:
        """
        生成标题

        Args:
            data: 股票数据

        Returns:
            List[str]: 标题列表
        """
        try:
            prompt = self._build_prompt(data)
            response = self._call_ai(prompt, HOT_STOCK_SYSTEM_PROMPT)

            # 解析JSON响应
            result = json.loads(response)
            return result.get("titles", [])
        except Exception as e:
            self.logger.error(f"热点个股标题生成失败: {e}")
            return self._generate_default_titles(data)

    async def _generate_cards(self, data: Dict[str, Any]) -> List[str]:
        """
        生成字卡内容

        Args:
            data: 股票数据

        Returns:
            List[str]: 字卡内容列表
        """
        try:
            prompt = self._build_prompt(data)
            response = self._call_ai(prompt, HOT_STOCK_SYSTEM_PROMPT)

            # 解析JSON响应
            result = json.loads(response)
            return result.get("cards", [])
        except Exception as e:
            self.logger.error(f"热点个股字卡生成失败: {e}")
            return self._generate_default_cards(data)

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """构建提示"""
        stock_info = data.get("stock_info", {})
        today_performance = data.get("today_performance", {})
        reason = data.get("reason", "")

        return HOT_STOCK_PROMPT_TEMPLATE.format(
            stock_info=json.dumps(stock_info, ensure_ascii=False, indent=2),
            today_performance=json.dumps(
                today_performance, ensure_ascii=False, indent=2
            ),
            reason=reason,
        )

    def _generate_default_titles(self, data: Dict[str, Any]) -> List[str]:
        """生成默认标题"""
        stock_info = data.get("stock_info", {})
        stock_name = stock_info.get("name", "股票")
        change_pct = data.get("today_performance", {}).get("change_pct", 0)

        if change_pct > 0:
            return [
                f"{stock_name}涨{change_pct:.2f}%｜发生了什么？",
                f"热点追踪｜{stock_name}今日大涨",
                f"复盘｜{stock_name}为何领涨？",
            ]
        else:
            return [
                f"{stock_name}跌{abs(change_pct):.2f}%｜原因分析",
                f"热点追踪｜{stock_name}今日大跌",
                f"复盘｜{stock_name}为何领跌？",
            ]

    def _generate_default_cards(self, data: Dict[str, Any]) -> List[str]:
        """生成默认字卡"""
        stock_info = data.get("stock_info", {})
        performance = data.get("today_performance", {})

        cards = []

        # 字卡1：今日表现
        cards.append(f"""## 今日表现

- 股票名称：{stock_info.get("name", "-")}（{stock_info.get("code", "-")}）
- 今日涨跌：{performance.get("change_pct", 0):+.2f}%
- 收盘价：{performance.get("close", "-")}元
- 成交额：{performance.get("volume", "-")}亿
""")

        # 字卡2-5：其他信息
        cards.append("## 近期走势\n\n待补充")
        cards.append("## 原因分析\n\n待补充")
        cards.append("## 市场关注点\n\n待补充")
        cards.append("## 同类对比\n\n待补充")

        return cards
