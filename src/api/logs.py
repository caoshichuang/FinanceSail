"""
日志查询API模块
"""

import os
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from .auth import get_current_user
from ..config.settings import settings
from ..utils.logger import get_logger
from ..scheduler.jobs import setup_scheduler

logger = get_logger("logs_api")

router = APIRouter(prefix="/api/logs", tags=["日志管理"])

LOG_DIR = settings.LOG_DIR


class LogResponse(BaseModel):
    lines: List[str]
    total_lines: int


class JobStatus(BaseModel):
    id: str
    name: str
    next_run: Optional[str]
    trigger: str


@router.get("/app", response_model=LogResponse)
async def get_app_log(
    lines: int = Query(default=100, le=1000),
    current_user: str = Depends(get_current_user),
):
    """获取应用日志"""
    log_file = LOG_DIR / "app.log"
    return await _read_log_file(log_file, lines)


@router.get("/error", response_model=LogResponse)
async def get_error_log(
    lines: int = Query(default=100, le=1000),
    current_user: str = Depends(get_current_user),
):
    """获取错误日志"""
    log_file = LOG_DIR / "error.log"
    return await _read_log_file(log_file, lines)


@router.get("/system")
async def get_system_status(current_user: str = Depends(get_current_user)):
    """获取系统状态"""
    import psutil
    import sys

    # CPU使用率
    cpu_percent = psutil.cpu_percent(interval=1)

    # 内存使用
    memory = psutil.virtual_memory()

    # 磁盘使用
    disk = psutil.disk_usage("/")

    # Python进程
    current_process = psutil.Process()

    return {
        "cpu_percent": cpu_percent,
        "memory": {
            "total": memory.total,
            "used": memory.used,
            "percent": memory.percent,
        },
        "disk": {"total": disk.total, "used": disk.used, "percent": disk.percent},
        "process": {
            "pid": current_process.pid,
            "memory_mb": current_process.memory_info().rss / 1024 / 1024,
            "cpu_percent": current_process.cpu_percent(),
        },
        "python_version": sys.version,
    }


@router.get("/jobs", response_model=List[JobStatus])
async def get_scheduled_jobs(current_user: str = Depends(get_current_user)):
    """获取定时任务状态"""
    try:
        scheduler = setup_scheduler()
        jobs = scheduler.get_jobs()

        result = []
        for job in jobs:
            result.append(
                JobStatus(
                    id=job.id,
                    name=job.name,
                    next_run=job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                    if job.next_run_time
                    else None,
                    trigger=str(job.trigger),
                )
            )

        return result
    except Exception as e:
        logger.error(f"获取定时任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _read_log_file(log_file: Path, lines: int) -> LogResponse:
    """读取日志文件"""
    try:
        if not log_file.exists():
            return LogResponse(lines=[], total_lines=0)

        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()

        # 返回最后N行
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return LogResponse(
            lines=[line.rstrip() for line in recent_lines], total_lines=len(all_lines)
        )
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
