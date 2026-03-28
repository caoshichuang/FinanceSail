"""
数据校验模块
"""

from typing import Dict, Any, List, Optional
from ..utils.logger import get_logger

logger = get_logger("validator")


class DataValidator:
    """数据校验器"""

    @staticmethod
    def validate_market_data(data: Dict[str, Any], market: str) -> bool:
        """
        校验市场数据

        Args:
            data: 市场数据
            market: 市场类型（A股/港股/美股）

        Returns:
            bool: 校验是否通过
        """
        if not data:
            logger.error("数据为空")
            return False

        # 检查必要字段
        required_fields = ["indices", "star_stocks"]
        for field in required_fields:
            if field not in data:
                logger.error(f"缺少必要字段: {field}")
                return False

        # 检查指数数据
        if not data.get("indices"):
            logger.error("指数数据为空")
            return False

        # 检查明星股数据
        if not data.get("star_stocks"):
            logger.warning("明星股数据为空，但继续处理")

        return True

    @staticmethod
    def validate_content(content: Dict[str, Any]) -> bool:
        """
        校验生成的内容

        Args:
            content: 生成的内容

        Returns:
            bool: 校验是否通过
        """
        if not content:
            logger.error("内容为空")
            return False

        # 检查标题
        titles = content.get("titles", [])
        if not titles or len(titles) == 0:
            logger.error("标题为空")
            return False

        # 检查字卡内容
        cards = content.get("cards", [])
        if not cards or len(cards) == 0:
            logger.error("字卡内容为空")
            return False

        return True

    @staticmethod
    def validate_indices(indices: Dict[str, Any]) -> bool:
        """
        校验指数数据

        Args:
            indices: 指数数据

        Returns:
            bool: 校验是否通过
        """
        if not indices:
            logger.error("指数数据为空")
            return False

        # 检查是否有涨跌幅数据
        for name, data in indices.items():
            if "change_pct" not in data:
                logger.warning(f"指数 {name} 缺少涨跌幅数据")

        return True

    @staticmethod
    def validate_stock_list(stocks: List[Dict[str, Any]]) -> bool:
        """
        校验股票列表

        Args:
            stocks: 股票列表

        Returns:
            bool: 校验是否通过
        """
        if not stocks:
            logger.warning("股票列表为空")
            return False

        for stock in stocks:
            if "code" not in stock or "name" not in stock:
                logger.warning(f"股票数据不完整: {stock}")
                return False

        return True
