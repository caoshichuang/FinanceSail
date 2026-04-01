"""
配置管理器（单例模式）
统一管理运行时配置，支持动态热加载
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.logger import get_logger

logger = get_logger("config_manager")


class ConfigManager:
    """
    单例配置管理器
    负责加载和合并 settings.py 静态配置 + dynamic_config.json 动态配置
    """

    _instance: Optional["ConfigManager"] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config: Dict[str, Any] = {}
        self._dynamic_config_path: Optional[Path] = None
        self._reload()

    def _reload(self):
        """重新加载所有配置"""
        try:
            from ..config.settings import settings

            # 基础配置从 settings 获取
            self._settings = settings
            self._dynamic_config_path = (
                settings.PROJECT_ROOT / "config" / "dynamic_config.json"
            )
            self._config = self._merge_config()
        except Exception as e:
            logger.error(f"配置加载失败: {e}")

    def _merge_config(self) -> Dict[str, Any]:
        """合并静态配置和动态配置"""
        merged: Dict[str, Any] = {}

        # 静态配置
        try:
            merged.update(self._settings.model_dump())
        except Exception:
            pass

        # 动态配置（优先级更高）
        if self._dynamic_config_path and self._dynamic_config_path.exists():
            try:
                with open(self._dynamic_config_path, "r", encoding="utf-8") as f:
                    dynamic = json.load(f)
                self._deep_update(merged, dynamic)
            except Exception as e:
                logger.warning(f"动态配置加载失败: {e}")

        return merged

    def _deep_update(self, base: dict, updates: dict):
        """递归深度合并字典"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键（支持点分隔：如 "llm.primary_model"）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def reload(self):
        """热重载配置"""
        self._reload()
        logger.info("配置已热重载")

    @property
    def settings(self):
        """直接访问 Settings 对象"""
        return self._settings

    @property
    def all(self) -> Dict[str, Any]:
        """返回全部配置"""
        return self._config.copy()


# 全局配置管理器实例
config_manager = ConfigManager()
