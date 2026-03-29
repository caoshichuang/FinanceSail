"""
应用入口模块
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .scheduler.jobs import setup_scheduler
from .api import auth_router, users_router, content_router, config_router, logs_router
from .utils.logger import get_logger
from .config.settings import settings

logger = get_logger("main")

# 创建FastAPI应用
app = FastAPI(
    title="小红书股票内容自动运营系统", description="后台管理API", version="1.0.0"
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


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "服务运行正常"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("小红书股票内容自动运营系统启动")

    # 初始化数据库
    from .models.db import init_db

    init_db()

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


# 挂载前端静态文件（如果存在）
admin_dir = settings.PROJECT_ROOT / "admin" / "dist"
if admin_dir.exists():
    app.mount("/", StaticFiles(directory=str(admin_dir), html=True), name="admin")


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=False)
