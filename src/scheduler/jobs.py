"""
定时任务模块
"""

import asyncio
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..collectors.a_share import AShareCollector
from ..collectors.us_stock import USStockCollector
from ..collectors.hk_stock import HKStockCollector
from ..collectors.ipo import IPOCollector
from ..generators.market_summary import MarketSummaryGenerator
from ..generators.ipo_analysis import IPOAnalysisGenerator
from ..generators.hot_stock import HotStockGenerator
from ..renderers.cover import CoverRenderer
from ..renderers.cards import CardsRenderer
from ..renderers.packer import ImagePacker
from ..notifiers.email import EmailNotifier
from ..models.db import init_db, Content, get_session
from ..config.settings import settings
from ..config.constants import MarketType, ContentStatus, ContentType
from ..utils.logger import get_logger
from ..utils.workday import (
    should_send_us_stock_email,
    should_send_a_stock_email,
    should_send_hk_stock_email,
)
from .smart_scheduler import SmartScheduler

# 新版：TradingCalendar 集成（优先使用，降级到旧版 workday）
try:
    from ..core.trading_calendar import is_market_open as _calendar_is_open

    def _is_trading_day(market: str) -> bool:
        """
        工作日判断（集成 TradingCalendar）

        Args:
            market: "cn" / "hk" / "us"
        """
        return _calendar_is_open(market)

except ImportError:
    # trading_calendar 未就绪时降级到旧版
    def _is_trading_day(market: str) -> bool:
        if market == "us":
            return should_send_us_stock_email()
        elif market == "hk":
            return should_send_hk_stock_email()
        return should_send_a_stock_email()


logger = get_logger("scheduler")


async def us_stock_job():
    """美股总结任务"""
    job_name = "美股总结"

    # 判断美股是否开盘
    if not _is_trading_day("us"):
        return

    logger.info(f"开始执行{job_name}任务")

    try:
        # 1. 采集数据
        collector = USStockCollector()
        data = await collector.collect()

        # 2. 生成内容
        generator = MarketSummaryGenerator(market=MarketType.US_STOCK)
        content = await generator.generate(data)

        # 3. 渲染图片
        date_str = datetime.now().strftime("%Y%m%d")
        image_dir = settings.IMAGE_DIR / f"us_{date_str}"
        image_dir.mkdir(parents=True, exist_ok=True)

        # 渲染封面
        cover_renderer = CoverRenderer()
        cover_path = await cover_renderer.render(
            {
                "title": content["titles"][0],
                "subtitle": data.get("date", ""),
                "date": data.get("date", ""),
            },
            image_dir / "cover.png",
        )

        # 渲染字卡
        cards_renderer = CardsRenderer()
        cards_paths = await cards_renderer.render(content["cards"], image_dir)

        # 打包图片
        packer = ImagePacker()
        all_images = [cover_path] + cards_paths
        zip_path = image_dir / f"us_{date_str}.zip"
        packer.pack(all_images, zip_path)

        # 4. 保存记录
        content_id = save_content_record(
            market=MarketType.US_STOCK,
            content_type=ContentType.SUMMARY,
            title=content["titles"][0],
            content=content["content"],
            tags=content["tags"],
            status=ContentStatus.SENT,
            image_paths=[str(p.relative_to(settings.PROJECT_ROOT)) for p in all_images],
        )

        # 5. 发送邮件
        notifier = EmailNotifier()
        notifier.send(
            market=MarketType.US_STOCK,
            titles=content["titles"],
            content=content["content"],
            tags=content["tags"],
            attachments=[cover_path],  # 只发送封面图片，不发送zip
            date=data.get("date", ""),
            content_id=content_id,
            cover_image=cover_path,
        )

        logger.info(f"{job_name}任务完成")

    except Exception as e:
        logger.error(f"{job_name}任务失败: {e}")
        notifier = EmailNotifier()
        notifier.send_error(str(e), job_name)


async def a_share_job():
    """A股+港股总结任务"""
    job_name = "A股港股总结"

    # 判断是否有市场开盘
    a_open = _is_trading_day("cn")
    hk_open = _is_trading_day("hk")

    if not a_open and not hk_open:
        logger.info("今日A股和港股均休市，跳过")
        return

    logger.info(f"开始执行{job_name}任务")

    try:
        # 1. 采集A股数据
        a_share_collector = AShareCollector()
        a_share_data = await a_share_collector.collect()

        # 2. 采集港股数据
        hk_collector = HKStockCollector()
        hk_data = await hk_collector.collect()

        # 3. 合并数据
        combined_data = {**a_share_data, "hk_data": hk_data}

        # 4. 生成A股内容
        a_share_generator = MarketSummaryGenerator(market=MarketType.A_SHARE)
        a_share_content = await a_share_generator.generate(a_share_data)

        # 5. 渲染图片
        date_str = datetime.now().strftime("%Y%m%d")
        image_dir = settings.IMAGE_DIR / f"a_share_{date_str}"
        image_dir.mkdir(parents=True, exist_ok=True)

        # 渲染封面
        cover_renderer = CoverRenderer()
        cover_path = await cover_renderer.render(
            {
                "title": a_share_content["titles"][0],
                "subtitle": f"港股恒生指数：{hk_data.get('indices', {}).get('恒生指数', {}).get('change_pct', 0):+.2f}%",
                "date": a_share_data.get("date", ""),
            },
            image_dir / "cover.png",
        )

        # 渲染字卡
        cards_renderer = CardsRenderer()
        cards_paths = await cards_renderer.render(a_share_content["cards"], image_dir)

        # 打包图片
        packer = ImagePacker()
        all_images = [cover_path] + cards_paths
        zip_path = image_dir / f"a_share_{date_str}.zip"
        packer.pack(all_images, zip_path)

        # 6. 保存记录
        content_id = save_content_record(
            market=MarketType.A_SHARE,
            content_type=ContentType.SUMMARY,
            title=a_share_content["titles"][0],
            content=a_share_content["content"],
            tags=a_share_content["tags"],
            status=ContentStatus.SENT,
            image_paths=[str(p.relative_to(settings.PROJECT_ROOT)) for p in all_images],
        )

        # 7. 发送邮件
        notifier = EmailNotifier()
        notifier.send(
            market=MarketType.A_SHARE,
            titles=a_share_content["titles"],
            content=a_share_content["content"],
            tags=a_share_content["tags"],
            attachments=[cover_path],  # 只发送封面图片，不发送zip
            date=a_share_data.get("date", ""),
            content_id=content_id,
            cover_image=cover_path,
        )

        logger.info(f"{job_name}任务完成")

    except Exception as e:
        logger.error(f"{job_name}任务失败: {e}")
        notifier = EmailNotifier()
        notifier.send_error(str(e), job_name)


def save_content_record(
    market: str,
    content_type: str,
    title: str,
    content: str,
    tags: str,
    status: str,
    image_paths: list = None,
) -> int:
    """保存内容记录"""
    try:
        import json

        session = get_session()
        record = Content(
            market=market,
            content_type=content_type,
            title=title,
            content=content,
            tags=tags,
            status=status,
            image_paths=json.dumps(image_paths) if image_paths else None,
        )
        session.add(record)
        session.commit()
        content_id = record.id
        session.close()
        logger.info(f"内容记录保存成功: {title} (ID: {content_id})")
        return content_id
    except Exception as e:
        logger.error(f"内容记录保存失败: {e}")
        return None


async def hot_stock_job():
    """热点个股分析任务"""
    job_name = "热点个股"

    # 判断A股是否开盘
    if not _is_trading_day("cn"):
        logger.info("今日A股休市，跳过热点个股")
        return

    logger.info(f"开始执行{job_name}任务")

    try:
        smart_scheduler = SmartScheduler()

        # 检测热点股票
        hot_stocks = await smart_scheduler.check_hot_stocks()

        if not hot_stocks:
            logger.info("今日无热点个股，跳过")
            return

        # 只处理涨跌停的股票
        for stock in hot_stocks:
            if stock.get("reason") not in ["涨停", "跌停"]:
                continue

            # 生成内容
            generator = HotStockGenerator()
            content = await generator.generate(
                {
                    "stock_info": stock,
                    "today_performance": stock,
                    "reason": stock.get("reason", ""),
                }
            )

            # 渲染图片
            date_str = datetime.now().strftime("%Y%m%d")
            image_dir = settings.IMAGE_DIR / f"hot_{stock['code']}_{date_str}"
            image_dir.mkdir(parents=True, exist_ok=True)

            # 渲染封面
            cover_renderer = CoverRenderer()
            cover_path = await cover_renderer.render(
                {
                    "title": content["titles"][0],
                    "subtitle": stock.get("name", ""),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                },
                image_dir / "cover.png",
            )

            # 渲染字卡
            cards_renderer = CardsRenderer()
            cards_paths = await cards_renderer.render(content["cards"], image_dir)

            # 打包图片
            packer = ImagePacker()
            all_images = [cover_path] + cards_paths
            zip_path = image_dir / f"hot_{stock['code']}_{date_str}.zip"
            packer.pack(all_images, zip_path)

            # 保存记录
            content_id = save_content_record(
                market="A股",
                content_type=ContentType.HOT_STOCK,
                title=content["titles"][0],
                content=content["content"],
                tags=content["tags"],
                status=ContentStatus.SENT,
                image_paths=[
                    str(p.relative_to(settings.PROJECT_ROOT)) for p in all_images
                ],
            )

            # 发送邮件
            notifier = EmailNotifier()
            notifier.send(
                market="热点",
                titles=content["titles"],
                content=content["content"],
                tags=content["tags"],
                attachments=[cover_path],  # 只发送封面图片，不发送zip
                date=datetime.now().strftime("%Y-%m-%d"),
                content_id=content_id,
                cover_image=cover_path,
            )

        logger.info(f"{job_name}任务完成")

    except Exception as e:
        logger.error(f"{job_name}任务失败: {e}")
        notifier = EmailNotifier()
        notifier.send_error(str(e), job_name)


async def ipo_job():
    """IPO分析任务"""
    job_name = "IPO分析"

    # 判断A股是否开盘
    if not _is_trading_day("cn"):
        logger.info("今日A股休市，跳过IPO分析")
        return

    logger.info(f"开始执行{job_name}任务")

    try:
        smart_scheduler = SmartScheduler()

        # 检查今日和明日IPO
        ipo_today = await smart_scheduler.check_ipo_today()
        ipo_tomorrow = await smart_scheduler.check_ipo_tomorrow()

        all_ipo = ipo_today + ipo_tomorrow

        if not all_ipo:
            logger.info("今日无新股申购，跳过")
            return

        # 为每只新股生成内容
        for ipo in all_ipo[:3]:  # 最多处理3只
            # 生成内容
            generator = IPOAnalysisGenerator()
            content = await generator.generate(
                {
                    "stock_info": ipo,
                    "issue_info": ipo,
                    "financial_data": {},
                }
            )

            # 渲染图片
            date_str = datetime.now().strftime("%Y%m%d")
            image_dir = settings.IMAGE_DIR / f"ipo_{ipo['code']}_{date_str}"
            image_dir.mkdir(parents=True, exist_ok=True)

            # 渲染封面
            cover_renderer = CoverRenderer()
            cover_path = await cover_renderer.render(
                {
                    "title": content["titles"][0],
                    "subtitle": f"发行价{ipo.get('price', '-')}元",
                    "date": ipo.get("subscription_date", ""),
                },
                image_dir / "cover.png",
            )

            # 渲染字卡
            cards_renderer = CardsRenderer()
            cards_paths = await cards_renderer.render(content["cards"], image_dir)

            # 打包图片
            packer = ImagePacker()
            all_images = [cover_path] + cards_paths
            zip_path = image_dir / f"ipo_{ipo['code']}_{date_str}.zip"
            packer.pack(all_images, zip_path)

            # 保存记录
            content_id = save_content_record(
                market="A股",
                content_type=ContentType.IPO,
                title=content["titles"][0],
                content=content["content"],
                tags=content["tags"],
                status=ContentStatus.SENT,
                image_paths=[
                    str(p.relative_to(settings.PROJECT_ROOT)) for p in all_images
                ],
            )

            # 发送邮件
            notifier = EmailNotifier()
            notifier.send(
                market="IPO",
                titles=content["titles"],
                content=content["content"],
                tags=content["tags"],
                attachments=[cover_path],  # 只发送封面图片，不发送zip
                date=ipo.get("subscription_date", ""),
                content_id=content_id,
                cover_image=cover_path,
            )

        logger.info(f"{job_name}任务完成")

    except Exception as e:
        logger.error(f"{job_name}任务失败: {e}")
        notifier = EmailNotifier()
        notifier.send_error(str(e), job_name)


def setup_scheduler() -> AsyncIOScheduler:
    """设置定时任务（使用动态配置，按市场时区调度）"""
    # 初始化数据库
    init_db()

    # 重新加载动态配置
    settings.load_dynamic_config()

    # A股/港股用 Asia/Shanghai 时区；美股用 America/New_York 时区
    scheduler_cn = AsyncIOScheduler(timezone="Asia/Shanghai")
    scheduler_us = AsyncIOScheduler(timezone="America/New_York")

    # 复用同一个 AsyncIOScheduler，但通过 timezone 参数控制各 job 触发时区
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    # 解析动态配置的时间
    def parse_time(time_str: str) -> tuple:
        """解析时间字符串，返回 (hour, minute)"""
        try:
            parts = time_str.split(":")
            return int(parts[0]), int(parts[1])
        except Exception:
            return 9, 0

    # 美股总结（按美东时间调度，09:00 ET ≈ 美股前市）
    us_hour, us_minute = parse_time(settings.US_STOCK_TIME)
    scheduler.add_job(
        us_stock_job,
        CronTrigger(hour=us_hour, minute=us_minute, timezone="America/New_York"),
        id="us_stock_summary",
        name="美股总结",
    )

    # A股+港股总结（北京时间）
    a_hour, a_minute = parse_time(settings.A_SHARE_TIME)
    scheduler.add_job(
        a_share_job,
        CronTrigger(hour=a_hour, minute=a_minute, timezone="Asia/Shanghai"),
        id="a_share_summary",
        name="A股港股总结",
    )

    # 热点个股（北京时间）
    hot_hour, hot_minute = parse_time(settings.HOT_STOCK_TIME)
    scheduler.add_job(
        hot_stock_job,
        CronTrigger(hour=hot_hour, minute=hot_minute, timezone="Asia/Shanghai"),
        id="hot_stock",
        name="热点个股",
    )

    # IPO分析（北京时间）
    ipo_hour, ipo_minute = parse_time(settings.IPO_TIME)
    scheduler.add_job(
        ipo_job,
        CronTrigger(hour=ipo_hour, minute=ipo_minute, timezone="Asia/Shanghai"),
        id="ipo_analysis",
        name="IPO分析",
    )

    return scheduler
