"""
全局异常处理模块
"""

import sys
import traceback
from typing import Callable
from ..utils.logger import get_logger
from .errors import RedbookAutoError

logger = get_logger("exception_handler")


def setup_exception_handler():
    """设置全局异常处理器"""

    def handle_exception(exc_type, exc_value, exc_traceback):
        """全局异常处理"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 键盘中断，使用默认处理
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error(
            "未捕获的异常",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_exception


async def handle_async_exception(coro: Callable, *args, **kwargs):
    """
    处理异步函数的异常

    Args:
        coro: 异步函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数执行结果或None（如果发生异常）
    """
    try:
        return await coro(*args, **kwargs)
    except RedbookAutoError as e:
        logger.error(f"业务异常: {e}")
        return None
    except Exception as e:
        logger.error(f"未预期的异常: {e}")
        logger.error(traceback.format_exc())
        return None


def format_error(e: Exception) -> str:
    """
    格式化异常信息

    Args:
        e: 异常对象

    Returns:
        str: 格式化后的错误信息
    """
    return f"{type(e).__name__}: {str(e)}"
