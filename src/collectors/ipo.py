"""
IPO数据采集模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base import BaseCollector
from ..config.constants import ContentType


class IPOCollector(BaseCollector):
    """IPO数据采集器"""

    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        采集IPO数据

        Returns:
            Dict[str, Any]: IPO数据
        """
        self.logger.info("开始采集IPO数据")

        # 获取新股申购列表
        new_subscriptions = self._get_new_subscriptions()

        # 获取即将上市新股
        upcoming_listings = self._get_upcoming_listings()

        # 获取近期上市新股
        recent_listings = self._get_recent_listings()

        return {
            "content_type": ContentType.IPO,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "new_subscriptions": new_subscriptions,
            "upcoming_listings": upcoming_listings,
            "recent_listings": recent_listings,
            "has_ipo_today": len(new_subscriptions) > 0,
            "has_ipo_tomorrow": self._has_ipo_tomorrow(new_subscriptions),
        }

    def _get_new_subscriptions(self) -> List[Dict[str, Any]]:
        """获取今日可申购新股"""
        try:
            # 获取新股申购数据
            df = ak.stock_xgsglb_em()

            if df.empty:
                return []

            # 筛选今日申购
            today = datetime.now().strftime("%Y-%m-%d")
            today_df = df[df["申购日期"] == today]

            subscriptions = []
            for _, row in today_df.iterrows():
                subscriptions.append(
                    {
                        "code": str(row.get("股票代码", "")),
                        "name": str(row.get("股票简称", "")),
                        "subscription_code": str(row.get("申购代码", "")),
                        "price": float(row.get("发行价格", 0)),
                        "pe_ratio": float(row.get("发行市盈率", 0)),
                        "subscription_limit": str(row.get("申购上限", "")),
                        "total_shares": str(row.get("发行总量", "")),
                        "online_subscription": str(row.get("网上发行量", "")),
                        "subscription_date": str(row.get("申购日期", "")),
                        "announcement_date": str(row.get("中签号公布日", "")),
                        "payment_date": str(row.get("中签缴款日期", "")),
                    }
                )

            return subscriptions
        except Exception as e:
            self.logger.error(f"获取新股申购数据失败: {e}")
            return []

    def _get_upcoming_listings(self) -> List[Dict[str, Any]]:
        """获取即将上市新股"""
        try:
            # 获取新股上市数据
            df = ak.stock_ipo_info_em()

            if df.empty:
                return []

            # 筛选未来7天内上市的股票
            today = datetime.now()
            future_date = today + timedelta(days=7)

            upcoming = []
            for _, row in df.iterrows():
                listing_date = pd.to_datetime(row.get("上市日期", ""), errors="coerce")
                if pd.notna(listing_date) and today <= listing_date <= future_date:
                    upcoming.append(
                        {
                            "code": str(row.get("股票代码", "")),
                            "name": str(row.get("股票简称", "")),
                            "listing_date": str(row.get("上市日期", "")),
                            "issue_price": float(row.get("发行价格", 0)),
                            "industry": str(row.get("行业", "")),
                        }
                    )

            return upcoming
        except Exception as e:
            self.logger.error(f"获取即将上市新股失败: {e}")
            return []

    def _get_recent_listings(self) -> List[Dict[str, Any]]:
        """获取近期上市新股（首日表现）"""
        try:
            # 获取新股上市数据
            df = ak.stock_ipo_info_em()

            if df.empty:
                return []

            # 筛选最近7天上市的股票
            today = datetime.now()
            past_date = today - timedelta(days=7)

            recent = []
            for _, row in df.iterrows():
                listing_date = pd.to_datetime(row.get("上市日期", ""), errors="coerce")
                if pd.notna(listing_date) and past_date <= listing_date <= today:
                    recent.append(
                        {
                            "code": str(row.get("股票代码", "")),
                            "name": str(row.get("股票简称", "")),
                            "listing_date": str(row.get("上市日期", "")),
                            "issue_price": float(row.get("发行价格", 0)),
                            "first_day_close": float(row.get("首日收盘价", 0)),
                            "first_day_change_pct": float(row.get("首日涨幅", 0)),
                            "industry": str(row.get("行业", "")),
                        }
                    )

            return recent
        except Exception as e:
            self.logger.error(f"获取近期上市新股失败: {e}")
            return []

    def _has_ipo_tomorrow(self, subscriptions: List[Dict[str, Any]]) -> bool:
        """检查明日是否有新股申购"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        for sub in subscriptions:
            if sub.get("subscription_date") == tomorrow:
                return True
        return False
