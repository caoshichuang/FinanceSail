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

logger = get_logger("scheduler")


async def us_stock_job():
    """美股总结任务"""
    job_name = "美股总结"

    # 判断美股是否开盘
    if not should_send_us_stock_email():
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

        # 4. 发送邮件
        notifier = EmailNotifier()
        notifier.send(
            market=MarketType.US_STOCK,
            titles=content["titles"],
            content=content["content"],
            tags=content["tags"],
            attachments=[zip_path],
            date=data.get("date", ""),
        )

        # 5. 保存记录
        save_content_record(
            market=MarketType.US_STOCK,
            content_type=ContentType.SUMMARY,
            title=content["titles"][0],
            content=content["content"],
            tags=content["tags"],
            status=ContentStatus.SENT,
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
    a_open = should_send_a_stock_email()
    hk_open = should_send_hk_stock_email()

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

        # 6. 发送邮件
        notifier = EmailNotifier()
        notifier.send(
            market=MarketType.A_SHARE,
            titles=a_share_content["titles"],
            content=a_share_content["content"],
            tags=a_share_content["tags"],
            attachments=[zip_path],
            date=a_share_data.get("date", ""),
        )

        # 7. 保存记录
        save_content_record(
            market=MarketType.A_SHARE,
            content_type=ContentType.SUMMARY,
            title=a_share_content["titles"][0],
            content=a_share_content["content"],
            tags=a_share_content["tags"],
            status=ContentStatus.SENT,
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
):
    """保存内容记录"""
    try:
        session = get_session()
        record = Content(
            market=market,
            content_type=content_type,
            title=title,
            content=content,
            tags=tags,
            status=status,
        )
        session.add(record)
        session.commit()
        session.close()
        logger.info(f"内容记录保存成功: {title}")
    except Exception as e:
        logger.error(f"内容记录保存失败: {e}")


async def hot_stock_job():
    """热点个股分析任务"""
    job_name = "热点个股"

    # 判断A股是否开盘
    if not should_send_a_stock_email():
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

            # 发送邮件
            notifier = EmailNotifier()
            notifier.send(
                market="热点",
                titles=content["titles"],
                content=content["content"],
                tags=content["tags"],
                attachments=[zip_path],
                date=datetime.now().strftime("%Y-%m-%d"),
            )

            # 保存记录
            save_content_record(
                market="A股",
                content_type=ContentType.HOT_STOCK,
                title=content["titles"][0],
                content=content["content"],
                tags=content["tags"],
                status=ContentStatus.SENT,
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
    if not should_send_a_stock_email():
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

            # 发送邮件
            notifier = EmailNotifier()
            notifier.send(
                market="IPO",
                titles=content["titles"],
                content=content["content"],
                tags=content["tags"],
                attachments=[zip_path],
                date=ipo.get("subscription_date", ""),
            )

            # 保存记录
            save_content_record(
                market="A股",
                content_type=ContentType.IPO,
                title=content["titles"][0],
                content=content["content"],
                tags=content["tags"],
                status=ContentStatus.SENT,
            )

        logger.info(f"{job_name}任务完成")

    except Exception as e:
        logger.error(f"{job_name}任务失败: {e}")
        notifier = EmailNotifier()
        notifier.send_error(str(e), job_name)


def setup_scheduler() -> AsyncIOScheduler:
    """设置定时任务"""
    # 初始化数据库
    init_db()

    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    # 美股总结：每日09:00
    scheduler.add_job(
        us_stock_job,
        CronTrigger(hour=9, minute=0),
        id="us_stock_summary",
        name="美股总结",
    )

    # A股+港股总结：每日17:00
    scheduler.add_job(
        a_share_job,
        CronTrigger(hour=17, minute=0),
        id="a_share_summary",
        name="A股港股总结",
    )

    # 热点个股：每日17:30（A股收盘后）
    scheduler.add_job(
        hot_stock_job,
        CronTrigger(hour=17, minute=30),
        id="hot_stock",
        name="热点个股",
    )

    # IPO分析：每日20:00（晚间发布明日IPO）
    scheduler.add_job(
        ipo_job,
        CronTrigger(hour=20, minute=0),
        id="ipo_analysis",
        name="IPO分析",
    )

    return scheduler
