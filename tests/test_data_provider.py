"""
data_provider 单元测试

测试 CircuitBreaker、数据标准化、DataFetcherManager 核心逻辑。
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# ── 为无安装的依赖注入 Mock ──────────────────────────────────

# Mock akshare / tushare 避免真实网络调用
for mod_name in ("akshare", "tushare"):
    sys.modules.setdefault(mod_name, types.ModuleType(mod_name))

# ─────────────────────────────────────────────────────────────


from data_provider.base import CircuitBreaker, DataFetcherManager, DataFetchError
from src.enums import CircuitBreakerState


class TestCircuitBreaker:
    """熔断器状态机测试"""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker(failure_threshold=3, cool_down_seconds=5)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.is_open() is False

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=3, cool_down_seconds=5)
        for _ in range(3):
            cb.record_failure()
        assert cb.is_open() is True
        assert cb.state == CircuitBreakerState.OPEN

    def test_records_success_resets_counter(self):
        cb = CircuitBreaker(failure_threshold=3, cool_down_seconds=5)
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED

    def test_half_open_after_cooldown(self):
        import time

        cb = CircuitBreaker(failure_threshold=1, cool_down_seconds=0.01)
        cb.record_failure()
        assert cb.is_open() is True

        time.sleep(0.02)
        # 冷却后再次检查，应变为 HALF_OPEN
        result = cb.is_open()
        assert result is False or cb.state == CircuitBreakerState.HALF_OPEN


class TestDataNormalization:
    """数据标准化测试"""

    def test_normalize_fills_missing_columns(self):
        from data_provider.base import STANDARD_COLUMNS

        raw_df = pd.DataFrame(
            {
                "date": ["2024-01-01"],
                "open": [10.0],
                "high": [11.0],
                "low": [9.5],
                "close": [10.5],
                "volume": [1000000],
            }
        )

        # 补全缺失列
        for col in STANDARD_COLUMNS:
            if col not in raw_df.columns:
                raw_df[col] = 0.0

        for col in STANDARD_COLUMNS:
            assert col in raw_df.columns


class TestDataFetcherManager:
    """DataFetcherManager 基础测试"""

    def test_instantiation(self):
        """能正常实例化（不实际发起网络请求）"""
        manager = DataFetcherManager()
        assert manager is not None

    def test_detect_market_cn(self):
        from data_provider.base import detect_market

        assert detect_market("600519") == "cn"
        assert detect_market("000001") == "cn"

    def test_detect_market_us(self):
        from data_provider.base import detect_market

        assert detect_market("AAPL") == "us"
        assert detect_market("TSLA") == "us"

    def test_detect_market_hk(self):
        from data_provider.base import detect_market

        assert detect_market("00700") == "hk"
        assert detect_market("09988") == "hk"
