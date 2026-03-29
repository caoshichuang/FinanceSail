"""
配置管理API模块
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .auth import get_current_user
from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger("config_api")

router = APIRouter(prefix="/api/config", tags=["配置管理"])

# 配置文件路径
CONFIG_DIR = settings.PROJECT_ROOT / "config"
HOLIDAYS_FILE = settings.DATA_DIR / "holidays.json"
ENV_FILE = settings.PROJECT_ROOT / ".env"


class HolidayUpdate(BaseModel):
    year: int
    dates: list


class EnvConfig(BaseModel):
    DEEPSEEK_API_KEY: Optional[str] = None
    TUSHARE_TOKEN: Optional[str] = None
    QQ_EMAIL: Optional[str] = None
    QQ_EMAIL_AUTH_CODE: Optional[str] = None
    RECEIVER_EMAIL: Optional[str] = None


@router.get("/env")
async def get_env_config(current_user: str = Depends(get_current_user)):
    """获取环境变量配置（脱敏）"""
    return {
        "DEEPSEEK_API_KEY": _mask_value(settings.DEEPSEEK_API_KEY),
        "TUSHARE_TOKEN": _mask_value(settings.TUSHARE_TOKEN),
        "QQ_EMAIL": settings.QQ_EMAIL,
        "QQ_EMAIL_AUTH_CODE": _mask_value(settings.QQ_EMAIL_AUTH_CODE),
        "RECEIVER_EMAIL": settings.RECEIVER_EMAIL,
    }


@router.put("/env")
async def update_env_config(
    config: EnvConfig, current_user: str = Depends(get_current_user)
):
    """更新环境变量配置"""
    try:
        # 读取现有配置
        env_content = ""
        if ENV_FILE.exists():
            env_content = ENV_FILE.read_text(encoding="utf-8")

        # 更新配置
        updates = config.dict(exclude_unset=True)
        for key, value in updates.items():
            if value is None:
                continue

            # 查找并替换
            pattern = f"{key}="
            if pattern in env_content:
                lines = env_content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith(pattern):
                        lines[i] = f"{key}={value}"
                        break
                env_content = "\n".join(lines)
            else:
                env_content += f"\n{key}={value}"

        # 保存
        ENV_FILE.write_text(env_content, encoding="utf-8")

        logger.info(f"管理员 {current_user} 更新环境配置")
        return {"message": "配置已保存，请重启服务生效"}
    except Exception as e:
        logger.error(f"更新环境配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holidays")
async def get_holidays(current_user: str = Depends(get_current_user)):
    """获取节假日配置"""
    try:
        if HOLIDAYS_FILE.exists():
            with open(HOLIDAYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"读取节假日配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/holidays")
async def update_holidays(
    data: HolidayUpdate, current_user: str = Depends(get_current_user)
):
    """更新节假日配置"""
    try:
        holidays = {}
        if HOLIDAYS_FILE.exists():
            with open(HOLIDAYS_FILE, "r", encoding="utf-8") as f:
                holidays = json.load(f)

        holidays[str(data.year)] = data.dates

        with open(HOLIDAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(holidays, f, ensure_ascii=False, indent=2)

        logger.info(f"管理员 {current_user} 更新{data.year}年节假日")
        return {"message": "节假日配置已更新"}
    except Exception as e:
        logger.error(f"更新节假日配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/star-stocks")
async def get_star_stocks(current_user: str = Depends(get_current_user)):
    """获取明星股配置"""
    return {
        "A股": settings.A_SHARE_STAR_STOCKS,
        "港股": settings.HK_STAR_STOCKS,
        "美股": settings.US_STAR_STOCKS,
    }


@router.get("/scheduler")
async def get_scheduler_config(current_user: str = Depends(get_current_user)):
    """获取定时任务配置"""
    return {
        "us_stock_time": "09:00",
        "a_share_time": "17:00",
        "hot_stock_time": "17:30",
        "ipo_time": "20:00",
    }


def _mask_value(value: str) -> str:
    """脱敏显示"""
    if not value or len(value) < 8:
        return "****"
    return value[:4] + "****" + value[-4:]
