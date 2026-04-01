"""
数据源基类和管理器
实现策略模式多数据源管理，含熔断器保护
"""

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import date

import pandas as pd

from src.enums import CircuitBreakerState, MarketType

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


# 标准数据列（所有数据源输出统一格式）
STANDARD_COLUMNS = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "pct_chg",
]

# 错误类


class DataFetchError(Exception):
    """数据获取失败异常"""

    pass


# ──────────────────────────────────────────────
# 熔断器
# ──────────────────────────────────────────────


@dataclass
class CircuitBreaker:
    """
    熔断器实现
    - CLOSED：正常调用
    - OPEN：熔断，拒绝调用，等待冷却
    - HALF_OPEN：冷却后放行一次探针请求
    """

    failure_threshold: int = 3  # 连续失败次数触发熔断
    cooldown_seconds: int = 300  # 熔断冷却时间（秒）

    _state: CircuitBreakerState = field(default=CircuitBreakerState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)

    @property
    def state(self) -> CircuitBreakerState:
        if self._state == CircuitBreakerState.OPEN:
            if time.time() - self._last_failure_time >= self.cooldown_seconds:
                self._state = CircuitBreakerState.HALF_OPEN
        return self._state

    def is_allowed(self) -> bool:
        """是否允许当前请求通过"""
        s = self.state
        return s in (CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN)

    def record_success(self):
        """记录成功"""
        self._failure_count = 0
        self._state = CircuitBreakerState.CLOSED

    def record_failure(self):
        """记录失败"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitBreakerState.OPEN
            logger.warning(
                f"熔断器触发：连续失败 {self._failure_count} 次，冷却 {self.cooldown_seconds}s"
            )


# ──────────────────────────────────────────────
# 基类
# ──────────────────────────────────────────────


class BaseFetcher(ABC):
    """数据源抽象基类"""

    name: str = "base"  # 子类必须重写

    @abstractmethod
    def get_daily_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            code: 股票代码
            days: 获取天数

        Returns:
            pd.DataFrame: 标准格式日线数据（STANDARD_COLUMNS）
        """
        raise NotImplementedError

    @abstractmethod
    def get_realtime_quote(self, code: str) -> Dict:
        """
        获取实时行情

        Args:
            code: 股票代码

        Returns:
            dict: 实时行情数据
        """
        raise NotImplementedError

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据标准化：确保输出包含 STANDARD_COLUMNS

        Args:
            df: 原始 DataFrame

        Returns:
            pd.DataFrame: 标准化后的 DataFrame
        """
        # 列名统一小写
        df.columns = [c.lower() for c in df.columns]

        # 重命名常见别名
        rename_map = {
            "trade_date": "date",
            "vol": "volume",
            "change_rate": "pct_chg",
            "pct_change": "pct_chg",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # 补充缺失列
        for col in STANDARD_COLUMNS:
            if col not in df.columns:
                if col == "pct_chg" and "close" in df.columns:
                    df["pct_chg"] = df["close"].pct_change() * 100
                elif (
                    col == "amount" and "close" in df.columns and "volume" in df.columns
                ):
                    df["amount"] = df["close"] * df["volume"]
                else:
                    df[col] = None

        # 确保 date 列为字符串
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        return df[STANDARD_COLUMNS].copy()


# ──────────────────────────────────────────────
# 市场检测
# ──────────────────────────────────────────────


def detect_market(code: str) -> str:
    """
    根据股票代码自动检测市场类型

    Args:
        code: 股票代码

    Returns:
        str: "cn" / "hk" / "us"
    """
    code = code.strip().upper()

    # 港股：HK前缀 或 5位数字
    if code.startswith("HK") or re.fullmatch(r"\d{5}", code):
        return MarketType.HK.value

    # A股：6位数字
    if re.fullmatch(r"\d{6}", code):
        return MarketType.CN.value

    # 美股：纯字母或字母+数字
    if re.fullmatch(r"[A-Z]{1,5}(?:\.[A-Z]{1,2})?", code):
        return MarketType.US.value

    # 默认 A股
    logger.warning(f"无法识别股票代码 {code} 的市场类型，默认为 A股")
    return MarketType.CN.value


# ──────────────────────────────────────────────
# 数据源管理器
# ──────────────────────────────────────────────


class DataFetcherManager:
    """
    多数据源策略管理器
    - 按市场类型分配优先级数据源
    - 自动故障切换
    - 熔断器保护
    """

    def __init__(self):
        self._fetchers: Dict[str, List[BaseFetcher]] = {
            MarketType.CN.value: [],
            MarketType.HK.value: [],
            MarketType.US.value: [],
        }
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._init_fetchers()

    def _init_fetchers(self):
        """初始化各市场数据源，按优先级排序"""
        # A股数据源
        try:
            from .akshare_fetcher import AkshareFetcher

            self._fetchers[MarketType.CN.value].append(AkshareFetcher())
        except Exception as e:
            logger.warning(f"AkshareFetcher 初始化失败: {e}")

        try:
            from .tushare_fetcher import TushareFetcher

            fetcher = TushareFetcher()
            if fetcher.is_available():
                self._fetchers[MarketType.CN.value].append(fetcher)
                self._fetchers[MarketType.HK.value].append(fetcher)
        except Exception as e:
            logger.warning(f"TushareFetcher 初始化失败: {e}")

        # 港股：AKShare 也支持
        try:
            from .akshare_fetcher import AkshareFetcher

            self._fetchers[MarketType.HK.value].append(AkshareFetcher())
        except Exception:
            pass

        # 美股数据源
        try:
            from .yfinance_fetcher import YfinanceFetcher

            self._fetchers[MarketType.US.value].append(YfinanceFetcher())
        except Exception as e:
            logger.warning(f"YfinanceFetcher 初始化失败: {e}")

        # 为每个 fetcher 创建熔断器
        all_fetchers = []
        for fetchers in self._fetchers.values():
            all_fetchers.extend(fetchers)
        for fetcher in all_fetchers:
            if fetcher.name not in self._circuit_breakers:
                self._circuit_breakers[fetcher.name] = CircuitBreaker()

        logger.info(
            f"DataFetcherManager 初始化完成：cn={len(self._fetchers['cn'])} "
            f"hk={len(self._fetchers['hk'])} us={len(self._fetchers['us'])}"
        )

    def _is_circuit_open(self, fetcher_name: str) -> bool:
        """检查熔断器是否已熔断"""
        cb = self._circuit_breakers.get(fetcher_name)
        if cb is None:
            return False
        return not cb.is_allowed()

    def _record_success(self, fetcher_name: str):
        cb = self._circuit_breakers.get(fetcher_name)
        if cb:
            cb.record_success()

    def _record_failure(self, fetcher_name: str):
        cb = self._circuit_breakers.get(fetcher_name)
        if cb:
            cb.record_failure()

    def get_daily_data(self, code: str, days: int = 60) -> Tuple[pd.DataFrame, str]:
        """
        获取日线数据，自动选择最优数据源

        Args:
            code: 股票代码
            days: 获取天数

        Returns:
            Tuple[pd.DataFrame, str]: (标准化数据, 数据源名称)

        Raises:
            DataFetchError: 所有数据源均失败
        """
        market = detect_market(code)
        fetchers = self._fetchers.get(market, [])

        if not fetchers:
            raise DataFetchError(f"市场 {market} 无可用数据源")

        last_error: Optional[Exception] = None
        for fetcher in fetchers:
            if self._is_circuit_open(fetcher.name):
                logger.debug(f"{fetcher.name} 熔断中，跳过")
                continue
            try:
                df = fetcher.get_daily_data(code, days)
                df = fetcher.normalize(df)
                self._record_success(fetcher.name)
                logger.info(f"[{code}] 从 {fetcher.name} 获取数据成功，共 {len(df)} 行")
                return df, fetcher.name
            except Exception as e:
                last_error = e
                self._record_failure(fetcher.name)
                logger.warning(f"{fetcher.name} 获取 {code} 失败: {e}")

        raise DataFetchError(f"所有数据源均失败（{code}），最后错误: {last_error}")

    def get_realtime_quote(self, code: str) -> Tuple[Dict, str]:
        """
        获取实时行情，自动选择数据源

        Returns:
            Tuple[dict, str]: (行情数据, 数据源名称)
        """
        market = detect_market(code)
        fetchers = self._fetchers.get(market, [])

        last_error: Optional[Exception] = None
        for fetcher in fetchers:
            if self._is_circuit_open(fetcher.name):
                continue
            try:
                quote = fetcher.get_realtime_quote(code)
                self._record_success(fetcher.name)
                return quote, fetcher.name
            except Exception as e:
                last_error = e
                self._record_failure(fetcher.name)
                logger.warning(f"{fetcher.name} 实时行情 {code} 失败: {e}")

        raise DataFetchError(
            f"所有数据源均失败（实时行情 {code}），最后错误: {last_error}"
        )

    def circuit_breaker_status(self) -> Dict[str, str]:
        """返回所有熔断器状态（用于监控）"""
        return {name: cb.state.value for name, cb in self._circuit_breakers.items()}
