"""
应用入口模块 - FinanceSail
"""

import asyncio
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .scheduler.jobs import setup_scheduler
from .api import auth_router, users_router, content_router, config_router, logs_router
from .api.content import preview_router
from .api.distribution import router as distribution_router
from .api.subscriptions import router as subscriptions_router
from .utils.logger import get_logger
from .config.settings import settings
from .config.project import (
    PROJECT_NAME,
    PROJECT_NAME_EN,
    PROJECT_VERSION,
    PROJECT_DESCRIPTION,
)

logger = get_logger("main")

# 创建FastAPI应用
app = FastAPI(
    title=f"{PROJECT_NAME} {PROJECT_NAME_EN}",
    description=PROJECT_DESCRIPTION,
    version=PROJECT_VERSION,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(content_router)
app.include_router(config_router)
app.include_router(logs_router)
app.include_router(preview_router)
app.include_router(distribution_router)
app.include_router(subscriptions_router)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "服务运行正常"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    from .config.project import PROJECT_LOGO

    logger.info(
        f"{PROJECT_LOGO} {PROJECT_NAME} {PROJECT_NAME_EN} v{PROJECT_VERSION} 启动"
    )

    # 初始化数据库
    from .models.db import init_db

    init_db()

    # ── 新架构模块预热 ────────────────────────────────────
    # 初始化交易日历（exchange-calendars 首次加载较慢，提前预热）
    try:
        from .core.trading_calendar import get_open_markets_today

        open_markets = get_open_markets_today()
        logger.info(f"今日开盘市场: {open_markets or '无（休市）'}")
    except Exception as e:
        logger.warning(f"交易日历预热失败（不影响主流程）: {e}")

    # 初始化通知服务（检测已配置渠道）
    try:
        from .notifiers.notification_service import NotificationService

        ns = NotificationService()
        if not ns.is_available():
            logger.warning("未配置任何通知渠道，请检查 .env 配置")
    except Exception as e:
        logger.warning(f"通知服务初始化失败（不影响主流程）: {e}")

    # ─────────────────────────────────────────────────────

    # 设置定时任务
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("定时任务调度器启动成功")

    # 打印任务列表
    jobs = scheduler.get_jobs()
    logger.info(f"已注册任务: {len(jobs)}个")
    for job in jobs:
        logger.info(f"  - {job.name}: {job.trigger}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("系统正在关闭...")


# 挂载图片静态文件
images_dir = settings.IMAGE_DIR
if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

# 挂载前端静态文件（如果存在）
admin_dir = settings.PROJECT_ROOT / "admin" / "dist"
if admin_dir.exists():
    # 挂载静态资源
    app.mount(
        "/assets", StaticFiles(directory=str(admin_dir / "assets")), name="assets"
    )

    # 处理 SPA 路由
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """处理 SPA 路由，返回 index.html"""
        # 检查是否是静态文件
        file_path = admin_dir / path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # 否则返回 index.html
        return FileResponse(str(admin_dir / "index.html"))


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=False)
