"""
YFinance 数据源
美股日线数据采集
"""

from typing import Dict
from datetime import datetime, timedelta

import pandas as pd

from .base import BaseFetcher

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class YfinanceFetcher(BaseFetcher):
    """
    YFinance 数据源实现
    主要用于美股数据（支持 NYSE / NASDAQ 股票）
    """

    name = "yfinance"

    def get_daily_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        获取美股日线数据

        Args:
            code: 股票代码（如 "AAPL" / "MSFT"）
            days: 获取天数

        Returns:
            pd.DataFrame: 日线数据
        """
        import yfinance as yf

        ticker = yf.Ticker(code.upper())
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 14)

        df = ticker.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval="1d",
        )

        if df.empty:
            raise ValueError(f"YFinance 未返回数据: {code}")

        # YFinance 返回 DatetimeIndex，需要转换
        df = df.reset_index()
        df = df.rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )

        # 补充 amount 和 pct_chg
        if "amount" not in df.columns:
            df["amount"] = df["close"] * df["volume"]
        if "pct_chg" not in df.columns:
            df["pct_chg"] = df["close"].pct_change() * 100

        return df.tail(days)

    def get_realtime_quote(self, code: str) -> Dict:
        """
        获取美股实时行情

        Args:
            code: 股票代码

        Returns:
            dict: 实时行情
        """
        import yfinance as yf

        ticker = yf.Ticker(code.upper())
        info = ticker.fast_info

        try:
            price = float(info.last_price)
            prev_close = float(info.previous_close)
            change_pct = (price - prev_close) / prev_close * 100 if prev_close else 0
        except Exception:
            price = 0.0
            change_pct = 0.0

        return {
            "code": code.upper(),
            "name": getattr(info, "display_name", code),
            "price": price,
            "change_pct": change_pct,
            "market_cap": getattr(info, "market_cap", 0),
            "volume": getattr(info, "three_month_average_volume", 0),
        }
