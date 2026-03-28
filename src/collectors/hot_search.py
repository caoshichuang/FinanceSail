"""
热搜股票采集模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseCollector
from ..config.constants import ContentType


class HotSearchCollector(BaseCollector):
    """热搜股票采集器"""

    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        采集热搜股票

        Returns:
            Dict[str, Any]: 热搜股票数据
        """
        self.logger.info("开始采集热搜股票")

        # 获取热搜股票
        hot_search_list = self._get_hot_search_stocks()

        return {
            "content_type": "hot_search",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "hot_search": hot_search_list,
        }

    def _get_hot_search_stocks(self) -> List[Dict[str, Any]]:
        """获取热搜股票"""
        try:
            # 使用AKShare获取东方财富人气榜
            df = ak.stock_hot_rank_em()

            hot_list = []
            for _, row in df.head(10).iterrows():
                hot_list.append(
                    {
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("股票名称", "")),
                        "rank": int(row.get("当前排名", 0)),
                        "price": float(row.get("最新价", 0)),
                        "change_pct": float(row.get("涨跌幅", 0)),
                    }
                )

            return hot_list
        except Exception as e:
            self.logger.error(f"获取热搜股票失败: {e}")
            return []
