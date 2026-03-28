"""
数据源降级采集器
"""

from typing import Dict, Any, List, Type
from .base import BaseCollector
from ..utils.logger import get_logger
from ..exceptions.errors import DataSourceError


class FallbackCollector:
    """数据源降级采集器"""

    def __init__(self, collectors: List[BaseCollector]):
        """
        初始化降级采集器

        Args:
            collectors: 数据源列表（按优先级排序）
        """
        self.logger = get_logger(self.__class__.__name__)
        self.collectors = collectors

    async def collect(self, **kwargs) -> Dict[str, Any]:
        """
        尝试多个数据源采集数据

        Args:
            **kwargs: 采集参数

        Returns:
            Dict[str, Any]: 采集的数据

        Raises:
            DataSourceError: 所有数据源均失败
        """
        last_exception = None

        for collector in self.collectors:
            try:
                self.logger.info(f"尝试数据源: {collector.__class__.__name__}")
                data = await collector.collect(**kwargs)
                self.logger.info(f"数据源 {collector.__class__.__name__} 采集成功")
                return data
            except Exception as e:
                self.logger.warning(f"数据源 {collector.__class__.__name__} 失败: {e}")
                last_exception = e
                continue

        self.logger.error("所有数据源均失败")
        raise DataSourceError(f"所有数据源均失败: {last_exception}")
