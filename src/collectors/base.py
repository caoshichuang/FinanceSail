"""
数据采集基类模块
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..utils.logger import get_logger
from ..utils.retry import retry
from ..utils.validator import DataValidator
from ..exceptions.errors import DataCollectionError, DataSourceError


class BaseCollector(ABC):
    """数据采集基类"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.validator = DataValidator()

    async def collect(self, **kwargs) -> Dict[str, Any]:
        """
        采集数据（带重试）

        Args:
            **kwargs: 采集参数

        Returns:
            Dict[str, Any]: 采集的数据
        """
        try:
            data = await self._fetch_data(**kwargs)
            self._validate_data(data)
            return data
        except Exception as e:
            self.logger.error(f"数据采集失败: {e}")
            raise DataCollectionError(f"数据采集失败: {e}") from e

    @abstractmethod
    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        获取数据（子类实现）

        Args:
            **kwargs: 采集参数

        Returns:
            Dict[str, Any]: 采集的数据
        """
        pass

    def _validate_data(self, data: Dict[str, Any]):
        """
        校验数据

        Args:
            data: 待校验数据
        """
        if not data:
            raise DataCollectionError("数据为空")

        # 子类可以重写此方法进行更详细的校验
        self._custom_validate(data)

    def _custom_validate(self, data: Dict[str, Any]):
        """
        自定义校验（子类可重写）

        Args:
            data: 待校验数据
        """
        pass

    def _get_market_type(self) -> str:
        """
        获取市场类型

        Returns:
            str: 市场类型
        """
        return "unknown"
