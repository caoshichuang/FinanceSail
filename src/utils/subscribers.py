"""
用户订阅管理工具模块
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger("subscribers")

# 订阅配置文件路径
SUBSCRIBERS_FILE = settings.PROJECT_ROOT / "config" / "subscribers.json"


def load_config() -> Dict[str, Any]:
    """
    加载订阅配置

    Returns:
        Dict[str, Any]: 配置数据
    """
    if not SUBSCRIBERS_FILE.exists():
        return {"users": []}

    try:
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载订阅配置失败: {e}")
        return {"users": []}


def save_config(config: Dict[str, Any]):
    """
    保存订阅配置

    Args:
        config: 配置数据
    """
    try:
        SUBSCRIBERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info("订阅配置保存成功")
    except Exception as e:
        logger.error(f"保存订阅配置失败: {e}")
        raise


def add_user(email: str, name: str = "", expire_days: int = 30) -> bool:
    """
    添加用户

    Args:
        email: 用户邮箱
        name: 用户昵称（可选）
        expire_days: 订阅天数（默认30天）

    Returns:
        bool: 是否添加成功
    """
    config = load_config()

    # 检查用户是否已存在
    for user in config["users"]:
        if user["email"] == email:
            logger.warning(f"用户已存在: {email}")
            return False

    # 计算到期日期
    expire_date = (date.today() + timedelta(days=expire_days)).strftime("%Y-%m-%d")

    # 添加用户
    config["users"].append(
        {"email": email, "name": name, "expire_date": expire_date, "stocks": []}
    )

    save_config(config)
    logger.info(f"添加用户成功: {email}, 到期日期: {expire_date}")
    return True


def remove_user(email: str) -> bool:
    """
    删除用户（全部退订）

    Args:
        email: 用户邮箱

    Returns:
        bool: 是否删除成功
    """
    config = load_config()

    for i, user in enumerate(config["users"]):
        if user["email"] == email:
            del config["users"][i]
            save_config(config)
            logger.info(f"删除用户成功: {email}")
            return True

    logger.warning(f"用户不存在: {email}")
    return False


def renew_user(email: str, days: int = 30) -> bool:
    """
    续费用户（延长到期时间）

    Args:
        email: 用户邮箱
        days: 续费天数（默认30天）

    Returns:
        bool: 是否续费成功
    """
    config = load_config()

    for user in config["users"]:
        if user["email"] == email:
            # 从当前到期日期或今天开始计算（取较晚的）
            current_expire = datetime.strptime(user["expire_date"], "%Y-%m-%d").date()
            today = date.today()
            start_date = max(current_expire, today)
            new_expire = (start_date + timedelta(days=days)).strftime("%Y-%m-%d")

            user["expire_date"] = new_expire
            save_config(config)
            logger.info(f"续费成功: {email}, 新到期日期: {new_expire}")
            return True

    logger.warning(f"用户不存在: {email}")
    return False


def is_user_expired(email: str) -> bool:
    """
    检查用户是否过期

    Args:
        email: 用户邮箱

    Returns:
        bool: 是否过期
    """
    config = load_config()

    for user in config["users"]:
        if user["email"] == email:
            expire_date = datetime.strptime(user["expire_date"], "%Y-%m-%d").date()
            return date.today() > expire_date

    # 用户不存在视为过期
    return True


def add_subscription(email: str, stock_code_or_name: str) -> bool:
    """
    添加用户订阅股票

    Args:
        email: 用户邮箱
        stock_code_or_name: 股票代码或股票名称

    Returns:
        bool: 是否添加成功
    """
    config = load_config()

    # 检查用户是否存在且未过期
    user = None
    for u in config["users"]:
        if u["email"] == email:
            user = u
            break

    if not user:
        logger.warning(f"用户不存在: {email}")
        return False

    # 检查是否过期
    if is_user_expired(email):
        logger.warning(f"用户已过期: {email}")
        return False

    # 判断是代码还是名称
    if stock_code_or_name.isdigit() or (
        len(stock_code_or_name) <= 6 and any(c.isdigit() for c in stock_code_or_name)
    ):
        # 股票代码
        code = stock_code_or_name
        name = ""
    else:
        # 股票名称
        code = ""
        name = stock_code_or_name

    # 检查是否已订阅
    for stock in user["stocks"]:
        if (code and stock.get("code") == code) or (name and stock.get("name") == name):
            logger.warning(f"股票已订阅: {stock_code_or_name}")
            return False

    # 添加订阅
    user["stocks"].append({"code": code, "name": name})
    save_config(config)
    logger.info(f"添加订阅成功: {email} -> {stock_code_or_name}")
    return True


def remove_subscription(email: str, stock_code_or_name: str) -> bool:
    """
    删除用户订阅股票

    Args:
        email: 用户邮箱
        stock_code_or_name: 股票代码或股票名称

    Returns:
        bool: 是否删除成功
    """
    config = load_config()

    for user in config["users"]:
        if user["email"] == email:
            for i, stock in enumerate(user["stocks"]):
                if (
                    stock.get("code") == stock_code_or_name
                    or stock.get("name") == stock_code_or_name
                ):
                    del user["stocks"][i]
                    save_config(config)
                    logger.info(f"删除订阅成功: {email} -> {stock_code_or_name}")
                    return True

            logger.warning(f"股票未订阅: {stock_code_or_name}")
            return False

    logger.warning(f"用户不存在: {email}")
    return False


def get_user_subscriptions(email: str) -> List[Dict[str, str]]:
    """
    查询用户订阅列表（自动过滤过期）

    Args:
        email: 用户邮箱

    Returns:
        List[Dict[str, str]]: 订阅的股票列表
    """
    # 检查是否过期
    if is_user_expired(email):
        logger.info(f"用户已过期: {email}")
        return []

    config = load_config()

    for user in config["users"]:
        if user["email"] == email:
            return user.get("stocks", [])

    return []


def get_stock_subscribers(stock_code_or_name: str) -> List[str]:
    """
    按股票查询订阅用户（自动过滤过期）

    Args:
        stock_code_or_name: 股票代码或股票名称

    Returns:
        List[str]: 订阅用户的邮箱列表
    """
    config = load_config()
    subscribers = []

    for user in config["users"]:
        # 跳过过期用户
        if is_user_expired(user["email"]):
            continue

        for stock in user.get("stocks", []):
            if (
                stock.get("code") == stock_code_or_name
                or stock.get("name") == stock_code_or_name
            ):
                subscribers.append(user["email"])
                break

    return subscribers


def cleanup_expired_users() -> int:
    """
    清理过期用户

    Returns:
        int: 清理的用户数量
    """
    config = load_config()
    today = date.today()

    original_count = len(config["users"])
    config["users"] = [
        user
        for user in config["users"]
        if datetime.strptime(user["expire_date"], "%Y-%m-%d").date() >= today
    ]
    cleaned_count = original_count - len(config["users"])

    if cleaned_count > 0:
        save_config(config)
        logger.info(f"清理过期用户: {cleaned_count}个")

    return cleaned_count


def get_all_active_users() -> List[Dict[str, Any]]:
    """
    获取所有有效用户（未过期）

    Returns:
        List[Dict[str, Any]]: 有效用户列表
    """
    config = load_config()
    active_users = []

    for user in config["users"]:
        if not is_user_expired(user["email"]):
            active_users.append(user)

    return active_users
