"""
AKShare 数据源
A股、港股日线数据采集
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


class AkshareFetcher(BaseFetcher):
    """
    AKShare 数据源实现
    支持 A股（6位数字代码）和港股（HK前缀/5位数字）
    """

    name = "akshare"

    def get_daily_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            code: 股票代码（如 "600519" / "HK00700"）
            days: 获取天数

        Returns:
            pd.DataFrame: 日线数据
        """
        import akshare as ak

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")

        code_clean = (
            code.strip().upper().lstrip("HK").lstrip("0")
            if code.upper().startswith("HK")
            else code.strip()
        )

        # 港股处理
        if code.upper().startswith("HK") or (code.isdigit() and len(code) == 5):
            hk_code = code.strip().lstrip("HK").zfill(5)
            df = ak.stock_hk_hist(
                symbol=hk_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                    "成交额": "amount",
                    "涨跌幅": "pct_chg",
                }
            )
            return df.tail(days)

        # A股处理
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        df = df.rename(
            columns={
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
                "涨跌幅": "pct_chg",
            }
        )
        return df.tail(days)

    def get_realtime_quote(self, code: str) -> Dict:
        """
        获取 A股/港股实时行情

        Args:
            code: 股票代码

        Returns:
            dict: 实时行情
        """
        import akshare as ak

        try:
            # A股
            if code.isdigit() and len(code) == 6:
                df = ak.stock_zh_a_spot_em()
                row = df[df["代码"] == code]
                if row.empty:
                    raise ValueError(f"未找到股票 {code}")
                r = row.iloc[0]
                return {
                    "code": code,
                    "name": r.get("名称", ""),
                    "price": float(r.get("最新价", 0)),
                    "change_pct": float(r.get("涨跌幅", 0)),
                    "volume": float(r.get("成交量", 0)),
                    "amount": float(r.get("成交额", 0)),
                }

            # 港股
            hk_code = code.strip().lstrip("HK").zfill(5)
            df = ak.stock_hk_spot_em()
            row = df[df["代码"] == hk_code]
            if row.empty:
                raise ValueError(f"未找到港股 {code}")
            r = row.iloc[0]
            return {
                "code": code,
                "name": r.get("名称", ""),
                "price": float(r.get("最新价", 0)),
                "change_pct": float(r.get("涨跌幅", 0)),
            }
        except Exception as e:
            logger.error(f"AKShare 实时行情获取失败 {code}: {e}")
            raise
