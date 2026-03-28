"""
新闻数据采集模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseCollector
from ..config.constants import ContentType


class NewsCollector(BaseCollector):
    """新闻数据采集器"""

    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        采集财经新闻

        Returns:
            Dict[str, Any]: 新闻数据
        """
        self.logger.info("开始采集财经新闻")

        # 获取财经新闻
        news_list = self._get_financial_news()

        return {
            "content_type": "news",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "news": news_list,
        }

    def _get_financial_news(self) -> List[Dict[str, Any]]:
        """获取财经新闻"""
        try:
            # 使用AKShare获取财经新闻
            df = ak.news_cctv(date=datetime.now().strftime("%Y%m%d"))

            news_list = []
            for _, row in df.head(5).iterrows():
                news_list.append(
                    {
                        "title": str(row.get("新闻标题", "")),
                        "content": str(row.get("新闻内容", ""))[:200],
                        "time": str(row.get("发布时间", "")),
                    }
                )

            return news_list
        except Exception as e:
            self.logger.error(f"获取财经新闻失败: {e}")
            return []
