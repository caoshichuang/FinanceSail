"""
股票事件监控模块
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import akshare as ak

from ..utils.logger import get_logger
from ..models.db import StockEvent, get_session, User, Subscription
from ..config.settings import settings


class EventType(Enum):
    """事件类型"""

    PRICE_CHANGE = "change"  # 涨跌幅
    ANNOUNCEMENT = "announce"  # 公告
    EARNING = "earning"  # 财报
    DIVIDEND = "dividend"  # 分红派息


@dataclass
class StockAlert:
    """股票预警"""

    stock_code: str
    stock_name: str
    market: str
    event_type: str
    event_data: Dict[str, Any]
    change_pct: float = 0.0


class StockMonitor:
    """股票监控器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    async def check_price_changes(
        self, stocks: List[Dict[str, str]]
    ) -> List[StockAlert]:
        """
        检查涨跌幅

        Args:
            stocks: 股票列表 [{"code": "600519", "name": "贵州茅台", "market": "A股"}]

        Returns:
            List[StockAlert]: 预警列表
        """
        alerts = []
        threshold = settings.LIMIT_UP_DOWN_THRESHOLD

        for stock in stocks:
            try:
                code = stock["code"]
                name = stock["name"]
                market = stock["market"]

                if market == "A股":
                    alert = await self._check_a_share_price(code, name, threshold)
                    if alert:
                        alerts.append(alert)
                elif market == "港股":
                    alert = await self._check_hk_stock_price(code, name, threshold)
                    if alert:
                        alerts.append(alert)
                elif market == "美股":
                    alert = await self._check_us_stock_price(code, name, threshold)
                    if alert:
                        alerts.append(alert)

            except Exception as e:
                self.logger.error(f"检查股票 {stock.get('code')} 涨跌幅失败: {e}")

        return alerts

    async def _check_a_share_price(
        self, code: str, name: str, threshold: float
    ) -> Optional[StockAlert]:
        """检查A股涨跌幅"""
        try:
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df["代码"] == code]

            if stock_data.empty:
                return None

            change_pct = float(stock_data.iloc[0]["涨跌幅"])

            # 检查是否超过阈值
            if abs(change_pct) >= threshold:
                return StockAlert(
                    stock_code=code,
                    stock_name=name,
                    market="A股",
                    event_type=EventType.PRICE_CHANGE.value,
                    event_data={
                        "price": float(stock_data.iloc[0]["最新价"]),
                        "change_pct": change_pct,
                        "change": float(stock_data.iloc[0]["涨跌"]),
                        "volume": float(stock_data.iloc[0]["成交量"]),
                        "amount": float(stock_data.iloc[0]["成交额"]),
                    },
                    change_pct=change_pct,
                )
        except Exception as e:
            self.logger.error(f"检查A股 {code} 涨跌幅失败: {e}")

        return None

    async def _check_hk_stock_price(
        self, code: str, name: str, threshold: float
    ) -> Optional[StockAlert]:
        """检查港股涨跌幅"""
        try:
            # 港股代码格式转换
            hk_code = code.zfill(5)

            # 获取实时行情
            df = ak.stock_hk_spot_em()
            stock_data = df[df["代码"] == hk_code]

            if stock_data.empty:
                return None

            change_pct = float(stock_data.iloc[0]["涨跌幅"])

            # 检查是否超过阈值
            if abs(change_pct) >= threshold:
                return StockAlert(
                    stock_code=code,
                    stock_name=name,
                    market="港股",
                    event_type=EventType.PRICE_CHANGE.value,
                    event_data={
                        "price": float(stock_data.iloc[0]["最新价"]),
                        "change_pct": change_pct,
                        "change": float(stock_data.iloc[0]["涨跌"]),
                    },
                    change_pct=change_pct,
                )
        except Exception as e:
            self.logger.error(f"检查港股 {code} 涨跌幅失败: {e}")

        return None

    async def _check_us_stock_price(
        self, code: str, name: str, threshold: float
    ) -> Optional[StockAlert]:
        """检查美股涨跌幅"""
        try:
            # 获取实时行情
            df = ak.stock_us_spot_em()
            stock_data = df[df["代码"] == code]

            if stock_data.empty:
                return None

            change_pct = float(stock_data.iloc[0]["涨跌幅"])

            # 检查是否超过阈值
            if abs(change_pct) >= threshold:
                return StockAlert(
                    stock_code=code,
                    stock_name=name,
                    market="美股",
                    event_type=EventType.PRICE_CHANGE.value,
                    event_data={
                        "price": float(stock_data.iloc[0]["最新价"]),
                        "change_pct": change_pct,
                        "change": float(stock_data.iloc[0]["涨跌"]),
                    },
                    change_pct=change_pct,
                )
        except Exception as e:
            self.logger.error(f"检查美股 {code} 涨跌幅失败: {e}")

        return None

    async def check_announcements(
        self, stocks: List[Dict[str, str]]
    ) -> List[StockAlert]:
        """
        检查公告

        Args:
            stocks: 股票列表

        Returns:
            List[StockAlert]: 预警列表
        """
        alerts = []
        keywords = ["业绩", "利润", "亏损", "重组", "收购", "分红", "增持", "减持"]

        for stock in stocks:
            try:
                code = stock["code"]
                name = stock["name"]
                market = stock["market"]

                if market != "A股":
                    continue

                # 获取公告
                df = ak.stock_notice_report(symbol=code)

                if df.empty:
                    continue

                # 检查最近公告
                for _, row in df.head(5).iterrows():
                    title = row.get("公告标题", "")

                    # 检查关键词
                    matched_keywords = [kw for kw in keywords if kw in title]
                    if matched_keywords:
                        alerts.append(
                            StockAlert(
                                stock_code=code,
                                stock_name=name,
                                market=market,
                                event_type=EventType.ANNOUNCEMENT.value,
                                event_data={
                                    "title": title,
                                    "url": row.get("公告链接", ""),
                                    "date": row.get("公告日期", ""),
                                    "keywords": matched_keywords,
                                },
                            )
                        )

            except Exception as e:
                self.logger.error(f"检查股票 {stock.get('code')} 公告失败: {e}")

        return alerts

    async def check_earnings_dates(
        self, stocks: List[Dict[str, str]]
    ) -> List[StockAlert]:
        """
        检查财报日期

        Args:
            stocks: 股票列表

        Returns:
            List[StockAlert]: 预警列表
        """
        alerts = []

        for stock in stocks:
            try:
                code = stock["code"]
                name = stock["name"]
                market = stock["market"]

                if market != "A股":
                    continue

                # 获取财报日期
                df = ak.stock_financial_report_date(symbol=code)

                if df.empty:
                    continue

                # 检查未来7天内的财报日期
                today = datetime.now().date()
                week_later = today + timedelta(days=7)

                for _, row in df.iterrows():
                    report_date = row.get("财报日期")
                    if report_date:
                        try:
                            report_date = datetime.strptime(
                                report_date, "%Y-%m-%d"
                            ).date()
                            if today <= report_date <= week_later:
                                alerts.append(
                                    StockAlert(
                                        stock_code=code,
                                        stock_name=name,
                                        market=market,
                                        event_type=EventType.EARNING.value,
                                        event_data={
                                            "report_date": report_date.strftime(
                                                "%Y-%m-%d"
                                            ),
                                            "report_type": row.get("财报类型", ""),
                                        },
                                    )
                                )
                        except ValueError:
                            pass

            except Exception as e:
                self.logger.error(f"检查股票 {stock.get('code')} 财报日期失败: {e}")

        return alerts

    async def check_dividends(self, stocks: List[Dict[str, str]]) -> List[StockAlert]:
        """
        检查分红派息

        Args:
            stocks: 股票列表

        Returns:
            List[StockAlert]: 预警列表
        """
        alerts = []

        for stock in stocks:
            try:
                code = stock["code"]
                name = stock["name"]
                market = stock["market"]

                if market != "A股":
                    continue

                # 获取分红信息
                df = ak.stock_dividents_cninfo(symbol=code)

                if df.empty:
                    continue

                # 检查最近分红
                for _, row in df.head(3).iterrows():
                    alerts.append(
                        StockAlert(
                            stock_code=code,
                            stock_name=name,
                            market=market,
                            event_type=EventType.DIVIDEND.value,
                            event_data={
                                "dividend_plan": row.get("分红方案", ""),
                                "ex_dividend_date": row.get("除权除息日", ""),
                                "record_date": row.get("股权登记日", ""),
                            },
                        )
                    )

            except Exception as e:
                self.logger.error(f"检查股票 {stock.get('code')} 分红失败: {e}")

        return alerts

    def save_alert(self, alert: StockAlert):
        """保存预警记录"""
        try:
            session = get_session()
            event = StockEvent(
                stock_code=alert.stock_code,
                stock_name=alert.stock_name,
                market=alert.market,
                event_type=alert.event_type,
                event_data=str(alert.event_data),
                change_pct=alert.change_pct,
            )
            session.add(event)
            session.commit()
            session.close()
            self.logger.info(f"保存预警记录: {alert.stock_name} - {alert.event_type}")
        except Exception as e:
            self.logger.error(f"保存预警记录失败: {e}")

    def get_subscribed_stocks(self) -> List[Dict[str, str]]:
        """获取所有订阅的股票"""
        try:
            session = get_session()
            subscriptions = (
                session.query(Subscription).filter(Subscription.is_active == True).all()
            )

            stocks = []
            for sub in subscriptions:
                stocks.append(
                    {
                        "code": sub.stock_code,
                        "name": sub.stock_name,
                        "market": sub.market,
                    }
                )

            session.close()
            return stocks
        except Exception as e:
            self.logger.error(f"获取订阅股票失败: {e}")
            return []

    async def run_monitoring(self):
        """运行监控"""
        self.logger.info("开始运行股票监控...")

        try:
            # 获取订阅的股票
            stocks = self.get_subscribed_stocks()

            if not stocks:
                self.logger.info("没有订阅的股票，跳过监控")
                return

            self.logger.info(f"监控 {len(stocks)} 只股票")

            # 检查涨跌幅
            price_alerts = await self.check_price_changes(stocks)
            for alert in price_alerts:
                self.save_alert(alert)

            # 检查公告
            announcement_alerts = await self.check_announcements(stocks)
            for alert in announcement_alerts:
                self.save_alert(alert)

            # 检查财报日期
            earning_alerts = await self.check_earnings_dates(stocks)
            for alert in earning_alerts:
                self.save_alert(alert)

            # 检查分红
            dividend_alerts = await self.check_dividends(stocks)
            for alert in dividend_alerts:
                self.save_alert(alert)

            total_alerts = (
                len(price_alerts)
                + len(announcement_alerts)
                + len(earning_alerts)
                + len(dividend_alerts)
            )
            self.logger.info(f"监控完成，共 {total_alerts} 条预警")

        except Exception as e:
            self.logger.error(f"监控运行失败: {e}")
