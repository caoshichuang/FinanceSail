"""
日志模块
使用Loguru实现结构化日志
"""

import sys
from pathlib import Path
from loguru import logger
from ..config.settings import settings


def setup_logger():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # 文件输出 - 所有日志
    log_file = settings.LOG_DIR / "app.log"
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        encoding="utf-8",
    )

    # 文件输出 - 错误日志
    error_log_file = settings.LOG_DIR / "error.log"
    logger.add(
        str(error_log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        encoding="utf-8",
    )

    return logger


def get_logger(name: str):
    """获取指定名称的logger"""
    return logger.bind(name=name)


# 初始化日志系统
setup_logger()
