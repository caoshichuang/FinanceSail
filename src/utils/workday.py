"""
股市开盘日判断工具模块
根据A股、港股、美股交易日历判断是否应该发送邮件
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Set, List
from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger("market_day")

# 节假日数据文件路径
HOLIDAYS_FILE = settings.DATA_DIR / "holidays.json"


def load_holidays(year: int) -> Set[str]:
    """
    加载指定年份的节假日数据

    Args:
        year: 年份

    Returns:
        Set[str]: 节假日日期集合（格式：YYYY-MM-DD）
    """
    holidays = set()

    if not HOLIDAYS_FILE.exists():
        logger.warning(f"节假日数据文件不存在: {HOLIDAYS_FILE}")
        return holidays

    try:
        with open(HOLIDAYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        year_str = str(year)
        if year_str in data:
            holidays = set(data[year_str])
            logger.info(f"加载{year}年节假日数据: {len(holidays)}天")
        else:
            logger.warning(f"未找到{year}年节假日数据")

    except Exception as e:
        logger.error(f"加载节假日数据失败: {e}")

    return holidays


def is_us_stock_open(check_date: date = None) -> bool:
    """
    判断美股是否开盘
    美股：周一至周五，排除美国节假日

    Args:
        check_date: 待检查日期

    Returns:
        bool: 美股是否开盘
    """
    if check_date is None:
        check_date = date.today()

    # 周末不开盘
    if check_date.weekday() >= 5:  # 5=周六, 6=周日
        return False

    # 美国主要节假日（简化版，覆盖主要节日）
    us_holidays = {
        # 元旦
        f"{check_date.year}-01-01",
        # 马丁·路德·金日（1月第三个周一）
        # 总统日（2月第三个周一）
        # 阵亡将士纪念日（5月最后一个周一）
        # 独立日
        f"{check_date.year}-07-04",
        # 劳动节（9月第一个周一）
        # 感恩节（11月第四个周四）
        # 圣诞节
        f"{check_date.year}-12-25",
    }

    date_str = check_date.strftime("%Y-%m-%d")
    return date_str not in us_holidays


def is_a_stock_open(check_date: date = None) -> bool:
    """
    判断A股是否开盘
    A股：周一至周五，排除中国法定节假日

    Args:
        check_date: 待检查日期

    Returns:
        bool: A股是否开盘
    """
    if check_date is None:
        check_date = date.today()

    # 周末不开盘
    if check_date.weekday() >= 5:
        return False

    # 中国法定节假日不开盘
    cn_holidays = load_holidays(check_date.year)
    date_str = check_date.strftime("%Y-%m-%d")

    return date_str not in cn_holidays


def is_hk_stock_open(check_date: date = None) -> bool:
    """
    判断港股是否开盘
    港股：周一至周五，排除香港节假日

    Args:
        check_date: 待检查日期

    Returns:
        bool: 港股是否开盘
    """
    if check_date is None:
        check_date = date.today()

    # 周末不开盘
    if check_date.weekday() >= 5:
        return False

    # 香港节假日（与大陆略有不同，但简化处理）
    hk_holidays = load_holidays(check_date.year)
    date_str = check_date.strftime("%Y-%m-%d")

    return date_str not in hk_holidays


def is_any_market_open(check_date: date = None) -> bool:
    """
    判断是否有任何市场开盘
    只要有任意一个市场开盘，就发送邮件

    Args:
        check_date: 待检查日期

    Returns:
        bool: 是否有市场开盘
    """
    if check_date is None:
        check_date = date.today()

    # 计算美股开盘时间（北京时间晚上）
    # 美股交易时间：北京时间 21:30-04:00（夏令时）/ 22:30-05:00（冬令时）
    us_open = is_us_stock_open(check_date)

    # A股开盘时间：北京时间 09:30-15:00
    a_open = is_a_stock_open(check_date)

    # 港股开盘时间：北京时间 09:30-16:00
    hk_open = is_hk_stock_open(check_date)

    return us_open or a_open or hk_open


def should_send_us_stock_email() -> bool:
    """
    判断是否应该发送美股邮件
    规则：今天是工作日（非周末非节假日）且昨天美股开盘

    Returns:
        bool: 是否应该发送
    """
    from datetime import timedelta

    today = date.today()
    yesterday = today - timedelta(days=1)

    # 今天是周末，不发送
    if today.weekday() >= 5:
        logger.info("今天是周末，不发送美股邮件")
        return False

    # 今天是节假日，不发送
    cn_holidays = load_holidays(today.year)
    if today.strftime("%Y-%m-%d") in cn_holidays:
        logger.info("今天是节假日，不发送美股邮件")
        return False

    # 昨天美股没开盘，不发送
    if not is_us_stock_open(yesterday):
        logger.info("昨日美股休市，不发送美股邮件")
        return False

    return True


def should_send_a_stock_email() -> bool:
    """
    判断是否应该发送A股邮件
    今天A股开盘则发送

    Returns:
        bool: 是否应该发送
    """
    result = is_a_stock_open()

    if not result:
        logger.info("今日A股休市，跳过A股邮件")

    return result


def should_send_hk_stock_email() -> bool:
    """
    判断是否应该发送港股邮件
    今天港股开盘则发送

    Returns:
        bool: 是否应该发送
    """
    result = is_hk_stock_open()

    if not result:
        logger.info("今日港股休市，跳过港股邮件")

    return result
