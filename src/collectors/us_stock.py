"""
美股数据采集模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseCollector
from ..config.settings import settings
from ..config.constants import MarketType, USIndex


class USStockCollector(BaseCollector):
    """美股数据采集器"""

    def _get_market_type(self) -> str:
        return MarketType.US_STOCK

    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        采集美股数据

        Returns:
            Dict[str, Any]: 美股数据
        """
        self.logger.info("开始采集美股数据")

        # 获取三大指数
        indices = self._get_indices()

        # 获取热门中概股
        chinese_stocks = self._get_chinese_stocks()

        # 获取美股明星股
        star_stocks = self._get_star_stocks()

        return {
            "market": MarketType.US_STOCK,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "indices": indices,
            "chinese_stocks": chinese_stocks,
            "star_stocks": star_stocks,
        }

    def _get_indices(self) -> Dict[str, Any]:
        """获取美股三大指数"""
        try:
            # 纳斯达克指数
            nasdaq = ak.index_us_stock_sina(symbol=".IXIC")
            nasdaq_latest = nasdaq.iloc[-1]

            # 标普500
            sp500 = ak.index_us_stock_sina(symbol=".INX")
            sp500_latest = sp500.iloc[-1]

            # 道琼斯
            dow = ak.index_us_stock_sina(symbol=".DJI")
            dow_latest = dow.iloc[-1]

            return {
                "纳斯达克指数": {
                    "close": float(nasdaq_latest["close"]),
                    "change_pct": float(nasdaq_latest.get("change_pct", 0)),
                },
                "标普500": {
                    "close": float(sp500_latest["close"]),
                    "change_pct": float(sp500_latest.get("change_pct", 0)),
                },
                "道琼斯指数": {
                    "close": float(dow_latest["close"]),
                    "change_pct": float(dow_latest.get("change_pct", 0)),
                },
            }
        except Exception as e:
            self.logger.error(f"获取美股指数失败: {e}")
            return {}

    def _get_chinese_stocks(self) -> List[Dict[str, Any]]:
        """获取热门中概股"""
        try:
            # 热门中概股列表
            chinese_stock_list = [
                {"code": "PDD", "name": "拼多多"},
                {"code": "BABA", "name": "阿里巴巴"},
                {"code": "JD", "name": "京东"},
                {"code": "NIO", "name": "蔚来"},
                {"code": "LI", "name": "理想汽车"},
                {"code": "BIDU", "name": "百度"},
            ]

            stocks = []
            for stock in chinese_stock_list:
                try:
                    df = ak.stock_us_daily(symbol=stock["code"], adjust="qfq")
                    if not df.empty:
                        latest = df.iloc[-1]
                        prev = df.iloc[-2] if len(df) > 1 else latest
                        change_pct = (
                            (float(latest["close"]) - float(prev["close"]))
                            / float(prev["close"])
                            * 100
                        )

                        stocks.append(
                            {
                                "code": stock["code"],
                                "name": stock["name"],
                                "close": float(latest["close"]),
                                "change_pct": round(change_pct, 2),
                            }
                        )
                except Exception as e:
                    self.logger.warning(f"获取{stock['name']}数据失败: {e}")
                    continue

            return stocks
        except Exception as e:
            self.logger.error(f"获取中概股失败: {e}")
            return []

    def _get_star_stocks(self) -> List[Dict[str, Any]]:
        """获取美股明星股"""
        try:
            stocks = []
            for stock in settings.US_STAR_STOCKS:
                try:
                    df = ak.stock_us_daily(symbol=stock["code"], adjust="qfq")
                    if not df.empty:
                        latest = df.iloc[-1]
                        prev = df.iloc[-2] if len(df) > 1 else latest
                        change_pct = (
                            (float(latest["close"]) - float(prev["close"]))
                            / float(prev["close"])
                            * 100
                        )

                        stocks.append(
                            {
                                "code": stock["code"],
                                "name": stock["name"],
                                "close": float(latest["close"]),
                                "change_pct": round(change_pct, 2),
                            }
                        )
                except Exception as e:
                    self.logger.warning(f"获取{stock['name']}数据失败: {e}")
                    continue

            return stocks
        except Exception as e:
            self.logger.error(f"获取明星股失败: {e}")
            return []
