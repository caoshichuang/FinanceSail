"""
交易日历模块
基于 exchange-calendars 库动态检测各市场交易日
支持 A股(CN)、港股(HK)、美股(US)
"""

from datetime import datetime, date, timedelta
from typing import Optional, Set
from zoneinfo import ZoneInfo

from ..utils.logger import get_logger

logger = get_logger("trading_calendar")

# 市场对应的 exchange-calendars 交易所代码
MARKET_EXCHANGE_MAP = {
    "cn": "XSHG",  # 上海证券交易所
    "hk": "XHKG",  # 香港交易所
    "us": "XNYS",  # 纽约证券交易所
}

# 市场对应的时区
MARKET_TIMEZONE_MAP = {
    "cn": "Asia/Shanghai",
    "hk": "Asia/Hong_Kong",
    "us": "America/New_York",
}

# A股收盘时间（北京时间）
CN_CLOSE_HOUR = 15

# 美股收盘时间（纽约时间）
US_CLOSE_HOUR = 16


def _try_exchange_calendars(market: str, check_date: date) -> Optional[bool]:
    """
    尝试使用 exchange-calendars 检查交易日
    如果库不可用，返回 None
    """
    try:
        import exchange_calendars as xcals

        exchange = MARKET_EXCHANGE_MAP.get(market)
        if not exchange:
            return None
        cal = xcals.get_calendar(exchange)
        return cal.is_session(check_date.strftime("%Y-%m-%d"))
    except ImportError:
        logger.warning("exchange-calendars 未安装，使用备用逻辑（默认开盘）")
        return None
    except Exception as e:
        logger.warning(f"exchange-calendars 查询失败: {e}，使用备用逻辑")
        return None


def _fallback_is_open(market: str, check_date: date) -> bool:
    """
    备用判断逻辑：周末返回 False，工作日返回 True
    对 A股/港股 还会读取静态节假日文件
    """
    if check_date.weekday() >= 5:
        return False

    if market in ("cn", "hk"):
        try:
            from ..utils.workday import load_holidays

            holidays = load_holidays(check_date.year)
            date_str = check_date.strftime("%Y-%m-%d")
            return date_str not in holidays
        except Exception:
            pass

    return True


def is_market_open(market: str, check_date: date = None) -> bool:
    """
    判断指定市场在某天是否开盘

    Args:
        market: 市场代码（"cn"/"hk"/"us"）
        check_date: 待检查日期，默认今天

    Returns:
        bool: 是否开盘
    """
    if check_date is None:
        check_date = date.today()

    result = _try_exchange_calendars(market, check_date)
    if result is not None:
        return result

    return _fallback_is_open(market, check_date)


def get_market_now(market: str) -> datetime:
    """
    获取指定市场当前时间（市场本地时区）

    Args:
        market: 市场代码（"cn"/"hk"/"us"）

    Returns:
        datetime: 含时区信息的当前时间
    """
    tz_name = MARKET_TIMEZONE_MAP.get(market, "Asia/Shanghai")
    tz = ZoneInfo(tz_name)
    return datetime.now(tz)


def get_effective_trading_date(market: str = "cn") -> date:
    """
    获取最近有效交易日期
    - 非交易日：返回上一个交易日
    - 交易日且已收盘：返回今天
    - 交易日未收盘：返回前一个交易日

    Args:
        market: 市场代码

    Returns:
        date: 有效交易日期
    """
    now = get_market_now(market)
    today = now.date()

    close_hour = CN_CLOSE_HOUR if market in ("cn", "hk") else US_CLOSE_HOUR

    if is_market_open(market, today):
        if now.hour >= close_hour:
            return today
        # 今日尚未收盘，用昨天
        check = today - timedelta(days=1)
    else:
        check = today - timedelta(days=1)

    # 往前找到最近的交易日（最多找14天）
    for _ in range(14):
        if is_market_open(market, check):
            return check
        check -= timedelta(days=1)

    logger.error(f"无法找到 {market} 市场的有效交易日，返回今天")
    return today


def get_open_markets_today(check_date: date = None) -> Set[str]:
    """
    获取今日开盘的市场集合

    Args:
        check_date: 待检查日期，默认今天

    Returns:
        Set[str]: 开盘市场代码集合
    """
    if check_date is None:
        check_date = date.today()

    open_markets = set()
    for market in MARKET_EXCHANGE_MAP:
        if is_market_open(market, check_date):
            open_markets.add(market)

    return open_markets


def compute_effective_region(region: str, open_markets: Set[str]) -> str:
    """
    根据开盘市场集合确定实际有效的分析区域

    Args:
        region: 目标区域（"cn"/"us"/"hk"/"both"/"all"）
        open_markets: 今日开盘市场集合

    Returns:
        str: 实际有效区域，若无市场开盘返回空字符串
    """
    if region == "both":
        if "cn" in open_markets and "hk" in open_markets:
            return "both"
        if "cn" in open_markets:
            return "cn"
        if "hk" in open_markets:
            return "hk"
        return ""

    if region == "all":
        result = [m for m in ("cn", "hk", "us") if m in open_markets]
        return ",".join(result) if result else ""

    if region in open_markets:
        return region

    return ""
