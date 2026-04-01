"""
data_provider 包
多数据源策略管理层，支持自动故障切换和熔断器保护
"""

from .base import BaseFetcher, DataFetcherManager, DataFetchError
from .akshare_fetcher import AkshareFetcher

__all__ = [
    "BaseFetcher",
    "DataFetcherManager",
    "DataFetchError",
    "AkshareFetcher",
]

# 尝试导入可选依赖
try:
    from .tushare_fetcher import TushareFetcher

    __all__.append("TushareFetcher")
except ImportError:
    pass

try:
    from .yfinance_fetcher import YfinanceFetcher

    __all__.append("YfinanceFetcher")
except ImportError:
    pass
