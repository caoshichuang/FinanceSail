"""
应用入口模块
"""

import asyncio
from .scheduler.jobs import setup_scheduler
from .utils.logger import get_logger

logger = get_logger("main")


async def main():
    """主函数"""
    logger.info("小红书股票内容自动运营系统启动")

    # 设置定时任务
    scheduler = setup_scheduler()

    # 启动调度器
    scheduler.start()
    logger.info("定时任务调度器启动成功")

    # 打印任务列表
    jobs = scheduler.get_jobs()
    logger.info(f"已注册任务: {len(jobs)}个")
    for job in jobs:
        logger.info(f"  - {job.name}: {job.trigger}")

    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("收到退出信号，正在关闭...")
        scheduler.shutdown()
        logger.info("系统已关闭")


if __name__ == "__main__":
    asyncio.run(main())
