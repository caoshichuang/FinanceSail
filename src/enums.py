"""
枚举类型定义模块
统一管理系统中使用的枚举值
"""

from enum import Enum


class ReportType(str, Enum):
    """报告类型"""

    STOCK_ANALYSIS = "stock_analysis"  # 个股分析
    MARKET_SUMMARY = "market_summary"  # 市场总结
    IPO_ANALYSIS = "ipo_analysis"  # IPO分析
    HOT_STOCK = "hot_stock"  # 热点个股


class MarketType(str, Enum):
    """市场类型"""

    CN = "cn"  # A股
    HK = "hk"  # 港股
    US = "us"  # 美股


class SignalType(str, Enum):
    """交易信号类型"""

    BUY = "🟢买入"
    WATCH = "🟡观望"
    SELL = "🔴卖出"
    HOLD = "🔵持有"


class CircuitBreakerState(str, Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 正常
    OPEN = "open"  # 熔断
    HALF_OPEN = "half_open"  # 半开


class NotificationChannel(str, Enum):
    """通知渠道"""

    EMAIL = "email"
    WECHAT = "wechat"
    FEISHU = "feishu"
    TELEGRAM = "telegram"
    PUSHPLUS = "pushplus"
    WXPUSHER = "wxpusher"


class TrendDirection(str, Enum):
    """趋势方向"""

    UPTREND = "uptrend"  # 上升趋势
    DOWNTREND = "downtrend"  # 下降趋势
    SIDEWAYS = "sideways"  # 横盘
