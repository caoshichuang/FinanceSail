"""
Tushare 数据源
A股、港股日线数据采集（需要 Token）
"""

from typing import Dict, Optional
from datetime import datetime, timedelta

import pandas as pd

from .base import BaseFetcher

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class TushareFetcher(BaseFetcher):
    """
    Tushare 数据源实现
    作为 AKShare 的备用数据源
    """

    name = "tushare"

    def __init__(self):
        self._pro = None
        self._token: Optional[str] = None
        self._init()

    def _init(self):
        """初始化 Tushare 连接"""
        try:
            from src.config.settings import settings

            self._token = settings.TUSHARE_TOKEN
            if self._token:
                import tushare as ts

                ts.set_token(self._token)
                self._pro = ts.pro_api()
                logger.info("Tushare 初始化成功")
        except Exception as e:
            logger.warning(f"Tushare 初始化失败: {e}")

    def is_available(self) -> bool:
        """检查 Tushare 是否可用"""
        return self._pro is not None

    def get_daily_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        获取日线数据（Tushare 格式：xxxxxx.SH / xxxxxx.SZ）

        Args:
            code: 股票代码（支持 "600519" 自动补后缀）
            days: 获取天数

        Returns:
            pd.DataFrame: 日线数据
        """
        if not self.is_available():
            raise RuntimeError("Tushare 未初始化")

        ts_code = self._to_ts_code(code)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")

        df = self._pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            raise ValueError(f"Tushare 未返回数据: {ts_code}")

        df = df.sort_values("trade_date").tail(days)
        df = df.rename(
            columns={
                "trade_date": "date",
                "vol": "volume",
                "pct_chg": "pct_chg",
                "amount": "amount",
            }
        )
        return df

    def get_realtime_quote(self, code: str) -> Dict:
        """
        获取实时行情（Tushare 实时数据）
        """
        if not self.is_available():
            raise RuntimeError("Tushare 未初始化")

        ts_code = self._to_ts_code(code)
        df = self._pro.realtime_quote(ts_code=ts_code)
        if df is None or df.empty:
            raise ValueError(f"Tushare 未返回实时行情: {ts_code}")

        r = df.iloc[0]
        return {
            "code": code,
            "name": r.get("name", ""),
            "price": float(r.get("price", 0)),
            "change_pct": float(r.get("pct_change", 0)),
        }

    def _to_ts_code(self, code: str) -> str:
        """
        将通用代码转换为 Tushare 格式
        600519 → 600519.SH
        000001 → 000001.SZ
        300001 → 300001.SZ
        """
        code = code.strip()
        if "." in code:
            return code.upper()
        if code.startswith(("6", "5", "9")):
            return f"{code}.SH"
        return f"{code}.SZ"
