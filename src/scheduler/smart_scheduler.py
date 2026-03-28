"""
智能调度模块
实现内容优先级判断和智能调度逻辑
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ..collectors.a_share import AShareCollector
from ..collectors.ipo import IPOCollector
from ..config.constants import ContentType, MarketType
from ..utils.logger import get_logger


class SmartScheduler:
    """智能调度器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    async def check_hot_stocks(self) -> List[Dict[str, Any]]:
        """
        检测热点股票

        Returns:
            List[Dict[str, Any]]: 热点股票列表
        """
        try:
            collector = AShareCollector()
            data = await collector.collect()

            hot_stocks = data.get("hot_stocks", [])
            limit_up = data.get("limit_up", [])
            limit_down = data.get("limit_down", [])

            # 合并热点股票
            all_hot = []

            # 涨跌停股票优先
            for stock in limit_up[:3]:
                stock["reason"] = "涨停"
                all_hot.append(stock)

            for stock in limit_down[:3]:
                stock["reason"] = "跌停"
                all_hot.append(stock)

            # 其他热点股票
            for stock in hot_stocks:
                if stock not in all_hot:
                    all_hot.append(stock)

            return all_hot[:5]  # 最多返回5只

        except Exception as e:
            self.logger.error(f"热点股票检测失败: {e}")
            return []

    async def check_ipo_today(self) -> List[Dict[str, Any]]:
        """
        检查今日是否有IPO申购

        Returns:
            List[Dict[str, Any]]: 今日可申购新股列表
        """
        try:
            collector = IPOCollector()
            data = await collector.collect()

            return data.get("new_subscriptions", [])

        except Exception as e:
            self.logger.error(f"IPO检查失败: {e}")
            return []

    async def check_ipo_tomorrow(self) -> List[Dict[str, Any]]:
        """
        检查明日是否有IPO申购

        Returns:
            List[Dict[str, Any]]: 明日可申购新股列表
        """
        try:
            collector = IPOCollector()
            data = await collector.collect()

            tomorrow = (datetime.now()).strftime("%Y-%m-%d")
            subscriptions = data.get("new_subscriptions", [])

            # 筛选明日申购
            tomorrow_subs = [
                sub for sub in subscriptions if sub.get("subscription_date") == tomorrow
            ]

            return tomorrow_subs

        except Exception as e:
            self.logger.error(f"明日IPO检查失败: {e}")
            return []

    async def get_content_priority(self) -> Dict[str, Any]:
        """
        获取内容优先级

        Returns:
            Dict[str, Any]: 内容优先级信息
        """
        priority = {
            "ipo_today": [],
            "ipo_tomorrow": [],
            "hot_stocks": [],
            "priority_order": [],
        }

        # 检查今日IPO
        ipo_today = await self.check_ipo_today()
        if ipo_today:
            priority["ipo_today"] = ipo_today
            priority["priority_order"].append(ContentType.IPO)

        # 检查明日IPO
        ipo_tomorrow = await self.check_ipo_tomorrow()
        if ipo_tomorrow:
            priority["ipo_tomorrow"] = ipo_tomorrow
            priority["priority_order"].append(ContentType.IPO)

        # 检查热点股票
        hot_stocks = await self.check_hot_stocks()
        if hot_stocks:
            priority["hot_stocks"] = hot_stocks
            priority["priority_order"].append(ContentType.HOT_STOCK)

        # 默认：市场总结
        priority["priority_order"].append(ContentType.SUMMARY)

        return priority

    def should_generate_ipo(self, priority: Dict[str, Any]) -> bool:
        """判断是否应该生成IPO内容"""
        return bool(priority.get("ipo_today") or priority.get("ipo_tomorrow"))

    def should_generate_hot_stock(self, priority: Dict[str, Any]) -> bool:
        """判断是否应该生成热点个股内容"""
        hot_stocks = priority.get("hot_stocks", [])
        # 只有涨跌停才单独生成
        for stock in hot_stocks:
            if stock.get("reason") in ["涨停", "跌停"]:
                return True
        return False
