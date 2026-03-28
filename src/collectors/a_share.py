"""
A股数据采集模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseCollector
from ..config.settings import settings
from ..config.constants import MarketType, AShareIndex


class AShareCollector(BaseCollector):
    """A股数据采集器"""

    def _get_market_type(self) -> str:
        return MarketType.A_SHARE

    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        采集A股数据

        Returns:
            Dict[str, Any]: A股数据
        """
        self.logger.info("开始采集A股数据")

        # 获取大盘指数
        indices = self._get_indices()

        # 获取涨跌分布
        distribution = self._get_distribution()

        # 获取热点板块
        hot_sectors = self._get_hot_sectors()

        # 获取明星股数据
        star_stocks = self._get_star_stocks()

        # 获取资金流向
        capital_flow = self._get_capital_flow()

        # 检测涨跌停
        limit_stocks = self._get_limit_stocks()

        # 检测热点股票
        hot_stocks = self._get_hot_stocks()

        return {
            "market": MarketType.A_SHARE,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "indices": indices,
            "distribution": distribution,
            "hot_sectors": hot_sectors,
            "star_stocks": star_stocks,
            "capital_flow": capital_flow,
            "limit_up": limit_stocks.get("limit_up", []),
            "limit_down": limit_stocks.get("limit_down", []),
            "hot_stocks": hot_stocks,
        }

    def _get_indices(self) -> Dict[str, Any]:
        """获取A股三大指数"""
        try:
            # 获取上证指数
            sh_index = ak.stock_zh_index_daily(symbol="sh000001")
            sh_latest = sh_index.iloc[-1]

            # 获取深证成指
            sz_index = ak.stock_zh_index_daily(symbol="sz399001")
            sz_latest = sz_index.iloc[-1]

            # 获取创业板指
            cy_index = ak.stock_zh_index_daily(symbol="sz399006")
            cy_latest = cy_index.iloc[-1]

            return {
                "上证指数": {
                    "close": float(sh_latest["close"]),
                    "change_pct": float(
                        (sh_latest["close"] - sh_latest["pre_close"])
                        / sh_latest["pre_close"]
                        * 100
                    )
                    if "pre_close" in sh_latest
                    else 0,
                },
                "深证成指": {
                    "close": float(sz_latest["close"]),
                    "change_pct": float(
                        (sz_latest["close"] - sz_latest["pre_close"])
                        / sz_latest["pre_close"]
                        * 100
                    )
                    if "pre_close" in sz_latest
                    else 0,
                },
                "创业板指": {
                    "close": float(cy_latest["close"]),
                    "change_pct": float(
                        (cy_latest["close"] - cy_latest["pre_close"])
                        / cy_latest["pre_close"]
                        * 100
                    )
                    if "pre_close" in cy_latest
                    else 0,
                },
            }
        except Exception as e:
            self.logger.error(f"获取指数数据失败: {e}")
            return {}

    def _get_distribution(self) -> Dict[str, int]:
        """获取涨跌分布"""
        try:
            # 获取所有A股实时行情
            df = ak.stock_zh_a_spot_em()

            up_count = len(df[df["涨跌幅"] > 0])
            down_count = len(df[df["涨跌幅"] < 0])
            flat_count = len(df[df["涨跌幅"] == 0])

            return {
                "上涨": up_count,
                "下跌": down_count,
                "平盘": flat_count,
                "总数": len(df),
            }
        except Exception as e:
            self.logger.error(f"获取涨跌分布失败: {e}")
            return {}

    def _get_hot_sectors(self) -> List[Dict[str, Any]]:
        """获取热点板块TOP3"""
        try:
            # 获取板块行情
            df = ak.stock_board_concept_name_em()

            # 按涨跌幅排序
            df = df.sort_values("涨跌幅", ascending=False).head(3)

            sectors = []
            for _, row in df.iterrows():
                sectors.append(
                    {
                        "name": row["板块名称"],
                        "change_pct": float(row["涨跌幅"]),
                        "leading_stock": row.get("领涨股票", ""),
                    }
                )

            return sectors
        except Exception as e:
            self.logger.error(f"获取热点板块失败: {e}")
            return []

    def _get_star_stocks(self) -> List[Dict[str, Any]]:
        """获取明星股数据"""
        try:
            # 获取所有A股实时行情
            df = ak.stock_zh_a_spot_em()

            star_stocks = []
            for stock in settings.A_SHARE_STAR_STOCKS:
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
            self.logger.error(f"获取明星股数据失败: {e}")
            return []

    def _get_capital_flow(self) -> Dict[str, Any]:
        """获取资金流向"""
        try:
            # 获取北向资金
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向")

            if not df.empty:
                latest = df.iloc[-1]
                return {
                    "north_net_flow": float(latest["净流入"]),
                    "north_date": str(latest["日期"]),
                }

            return {}
        except Exception as e:
            self.logger.error(f"获取资金流向失败: {e}")
            return {}

    def _get_limit_stocks(self) -> Dict[str, List[Dict[str, Any]]]:
        """检测涨跌停股票"""
        try:
            # 获取所有A股实时行情
            df = ak.stock_zh_a_spot_em()

            # 涨停股票
            limit_up_threshold = settings.LIMIT_UP_DOWN_THRESHOLD
            limit_up = df[df["涨跌幅"] >= limit_up_threshold].head(5)
            limit_up_list = []
            for _, row in limit_up.iterrows():
                limit_up_list.append(
                    {
                        "code": row["代码"],
                        "name": row["名称"],
                        "close": float(row["最新价"]),
                        "change_pct": float(row["涨跌幅"]),
                    }
                )

            # 跌停股票
            limit_down = df[df["涨跌幅"] <= -limit_up_threshold].head(5)
            limit_down_list = []
            for _, row in limit_down.iterrows():
                limit_down_list.append(
                    {
                        "code": row["代码"],
                        "name": row["名称"],
                        "close": float(row["最新价"]),
                        "change_pct": float(row["涨跌幅"]),
                    }
                )

            return {
                "limit_up": limit_up_list,
                "limit_down": limit_down_list,
            }
        except Exception as e:
            self.logger.error(f"检测涨跌停失败: {e}")
            return {"limit_up": [], "limit_down": []}

    def _get_hot_stocks(self) -> List[Dict[str, Any]]:
        """检测热点股票（涨跌超阈值）"""
        try:
            # 获取所有A股实时行情
            df = ak.stock_zh_a_spot_em()

            threshold = settings.HOT_STOCK_THRESHOLD

            # 涨幅超阈值
            hot_up = df[df["涨跌幅"] >= threshold].head(5)

            # 跌幅超阈值
            hot_down = df[df["涨跌幅"] <= -threshold].head(5)

            # 合并
            hot_stocks = []
            for _, row in pd.concat([hot_up, hot_down]).iterrows():
                hot_stocks.append(
                    {
                        "code": row["代码"],
                        "name": row["名称"],
                        "close": float(row["最新价"]),
                        "change_pct": float(row["涨跌幅"]),
                        "volume": float(row["成交额"]),
                    }
                )

            return hot_stocks
        except Exception as e:
            self.logger.error(f"检测热点股票失败: {e}")
            return []
