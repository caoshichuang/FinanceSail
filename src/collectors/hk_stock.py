"""
港股数据采集模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseCollector
from ..config.settings import settings
from ..config.constants import MarketType, HKIndex


class HKStockCollector(BaseCollector):
    """港股数据采集器"""

    def _get_market_type(self) -> str:
        return MarketType.HK_STOCK

    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        采集港股数据

        Returns:
            Dict[str, Any]: 港股数据
        """
        self.logger.info("开始采集港股数据")

        # 获取恒生指数
        indices = self._get_indices()

        # 获取港股明星股
        star_stocks = self._get_star_stocks()

        # 获取南向资金
        capital_flow = self._get_capital_flow()

        return {
            "market": MarketType.HK_STOCK,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "indices": indices,
            "star_stocks": star_stocks,
            "capital_flow": capital_flow,
        }

    def _get_indices(self) -> Dict[str, Any]:
        """获取恒生指数、恒生科技指数"""
        try:
            # 恒生指数
            hs_index = ak.stock_hk_index_daily_sina(symbol="HSI")
            hs_latest = hs_index.iloc[-1]

            # 恒生科技指数
            hstech_index = ak.stock_hk_index_daily_sina(symbol="HSTECH")
            hstech_latest = hstech_index.iloc[-1]

            return {
                "恒生指数": {
                    "close": float(hs_latest["close"]),
                    "change_pct": float(
                        (hs_latest["close"] - hs_latest["pre_close"])
                        / hs_latest["pre_close"]
                        * 100
                    )
                    if "pre_close" in hs_latest
                    else 0,
                },
                "恒生科技指数": {
                    "close": float(hstech_latest["close"]),
                    "change_pct": float(
                        (hstech_latest["close"] - hstech_latest["pre_close"])
                        / hstech_latest["pre_close"]
                        * 100
                    )
                    if "pre_close" in hstech_latest
                    else 0,
                },
            }
        except Exception as e:
            self.logger.error(f"获取港股指数失败: {e}")
            return {}

    def _get_star_stocks(self) -> List[Dict[str, Any]]:
        """获取港股明星股"""
        try:
            # 获取所有港股实时行情
            df = ak.stock_hk_spot_em()

            star_stocks = []
            for stock in settings.HK_STAR_STOCKS:
                stock_data = df[df["代码"] == stock["code"]]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    star_stocks.append(
                        {
                            "code": stock["code"],
                            "name": stock["name"],
                            "close": float(row["最新价"]),
                            "change_pct": float(row["涨跌幅"]),
                            "volume": float(row["成交额"]),
                        }
                    )

            return star_stocks
        except Exception as e:
            self.logger.error(f"获取港股明星股失败: {e}")
            return []

    def _get_capital_flow(self) -> Dict[str, Any]:
        """获取南向资金"""
        try:
            # 获取南向资金
            df = ak.stock_hsgt_south_net_flow_in_em(symbol="南向")

            if not df.empty:
                latest = df.iloc[-1]
                return {
                    "south_net_flow": float(latest["净流入"]),
                    "south_date": str(latest["日期"]),
                }

            return {}
        except Exception as e:
            self.logger.error(f"获取南向资金失败: {e}")
            return {}
