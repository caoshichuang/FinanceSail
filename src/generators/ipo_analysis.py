"""
IPO分析生成器模块
"""

import json
from typing import Dict, Any, List
from .base import BaseGenerator
from .prompts.ipo_analysis import (
    IPO_ANALYSIS_SYSTEM_PROMPT,
    IPO_ANALYSIS_PROMPT_TEMPLATE,
)
from ..config.constants import ContentType
from ..exceptions.errors import ContentGenerationError


class IPOAnalysisGenerator(BaseGenerator):
    """IPO分析生成器"""

    async def _generate_titles(self, data: Dict[str, Any]) -> List[str]:
        """
        生成标题

        Args:
            data: IPO数据

        Returns:
            List[str]: 标题列表
        """
        try:
            prompt = self._build_prompt(data)
            response = self._call_ai(prompt, IPO_ANALYSIS_SYSTEM_PROMPT)

            # 解析JSON响应
            result = json.loads(response)
            return result.get("titles", [])
        except Exception as e:
            self.logger.error(f"IPO标题生成失败: {e}")
            return self._generate_default_titles(data)

    async def _generate_cards(self, data: Dict[str, Any]) -> List[str]:
        """
        生成字卡内容

        Args:
            data: IPO数据

        Returns:
            List[str]: 字卡内容列表
        """
        try:
            prompt = self._build_prompt(data)
            response = self._call_ai(prompt, IPO_ANALYSIS_SYSTEM_PROMPT)

            # 解析JSON响应
            result = json.loads(response)
            return result.get("cards", [])
        except Exception as e:
            self.logger.error(f"IPO字卡生成失败: {e}")
            return self._generate_default_cards(data)

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """构建提示"""
        stock_info = data.get("stock_info", {})
        issue_info = data.get("issue_info", {})
        financial_data = data.get("financial_data", {})

        return IPO_ANALYSIS_PROMPT_TEMPLATE.format(
            stock_info=json.dumps(stock_info, ensure_ascii=False, indent=2),
            issue_info=json.dumps(issue_info, ensure_ascii=False, indent=2),
            financial_data=json.dumps(financial_data, ensure_ascii=False, indent=2),
        )

    def _generate_default_titles(self, data: Dict[str, Any]) -> List[str]:
        """生成默认标题"""
        stock_name = data.get("stock_info", {}).get("name", "新股")
        return [
            f"明日申购｜{stock_name}值得打吗？",
            f"新股速览｜{stock_name}申购指南",
            f"打新提醒｜{stock_name}明日可申购",
        ]

    def _generate_default_cards(self, data: Dict[str, Any]) -> List[str]:
        """生成默认字卡"""
        stock_info = data.get("stock_info", {})
        issue_info = data.get("issue_info", {})

        cards = []

        # 字卡1：公司简介
        cards.append(f"""## 公司简介

- 公司名称：{stock_info.get("name", "-")}
- 股票代码：{stock_info.get("code", "-")}
- 所属行业：{stock_info.get("industry", "-")}
- 主营业务：{stock_info.get("business", "-")}
""")

        # 字卡2：发行信息
        cards.append(f"""## 发行信息

- 发行价格：{issue_info.get("price", "-")}元
- 发行市盈率：{issue_info.get("pe_ratio", "-")}倍
- 发行数量：{issue_info.get("total_shares", "-")}万股
- 申购上限：{issue_info.get("subscription_limit", "-")}股
- 申购日期：{issue_info.get("subscription_date", "-")}
""")

        # 字卡3-6：其他信息
        cards.append("## 财务数据\n\n待补充")
        cards.append("## 行业对比\n\n待补充")
        cards.append("## 亮点分析\n\n待补充")
        cards.append("## 风险提示\n\n待补充")

        return cards
