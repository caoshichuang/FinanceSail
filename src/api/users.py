"""
用户管理API模块
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .auth import get_current_user
from ..utils.subscribers import (
    load_config,
    save_config,
    add_user,
    remove_user,
    renew_user,
    add_subscription,
    remove_subscription,
    get_user_subscriptions,
    get_all_active_users,
    is_user_expired,
    cleanup_expired_users,
)
from ..utils.logger import get_logger

logger = get_logger("users_api")

router = APIRouter(prefix="/api/users", tags=["用户管理"])


class UserCreate(BaseModel):
    email: str
    name: str = ""
    expire_days: int = 30


class UserUpdate(BaseModel):
    name: Optional[str] = None
    expire_days: Optional[int] = None


class SubscriptionAdd(BaseModel):
    stock_code_or_name: str


class UserResponse(BaseModel):
    email: str
    name: str
    expire_date: str
    is_expired: bool
    stocks: list


@router.get("/", response_model=List[UserResponse])
async def list_users(
    include_expired: bool = False, current_user: str = Depends(get_current_user)
):
    """获取用户列表"""
    config = load_config()
    users = []

    for user in config.get("users", []):
        expired = is_user_expired(user["email"])
        if not include_expired and expired:
            continue

        users.append(
            UserResponse(
                email=user["email"],
                name=user.get("name", ""),
                expire_date=user.get("expire_date", ""),
                is_expired=expired,
                stocks=user.get("stocks", []),
            )
        )

    return users


@router.post("/")
async def create_user(
    user_data: UserCreate, current_user: str = Depends(get_current_user)
):
    """添加用户"""
    result = add_user(
        email=user_data.email, name=user_data.name, expire_days=user_data.expire_days
    )

    if not result:
        raise HTTPException(status_code=400, detail="用户已存在")

    logger.info(f"管理员 {current_user} 添加用户: {user_data.email}")
    return {"message": "添加成功", "email": user_data.email}


@router.delete("/{email}")
async def delete_user(email: str, current_user: str = Depends(get_current_user)):
    """删除用户"""
    result = remove_user(email)

    if not result:
        raise HTTPException(status_code=404, detail="用户不存在")

    logger.info(f"管理员 {current_user} 删除用户: {email}")
    return {"message": "删除成功", "email": email}


@router.post("/{email}/renew")
async def renew_user_subscription(
    email: str, days: int = 30, current_user: str = Depends(get_current_user)
):
    """续费用户"""
    result = renew_user(email, days)

    if not result:
        raise HTTPException(status_code=404, detail="用户不存在")

    logger.info(f"管理员 {current_user} 续费用户: {email}, {days}天")
    return {"message": "续费成功", "email": email, "days": days}


@router.get("/{email}/subscriptions")
async def get_user_subs(email: str, current_user: str = Depends(get_current_user)):
    """获取用户订阅列表"""
    stocks = get_user_subscriptions(email)
    return {"email": email, "stocks": stocks}


@router.post("/{email}/subscriptions")
async def add_user_subscription(
    email: str, sub_data: SubscriptionAdd, current_user: str = Depends(get_current_user)
):
    """添加用户订阅"""
    result = add_subscription(email, sub_data.stock_code_or_name)

    if not result:
        raise HTTPException(
            status_code=400, detail="添加失败（用户不存在/已过期/已订阅）"
        )

    logger.info(
        f"管理员 {current_user} 添加订阅: {email} -> {sub_data.stock_code_or_name}"
    )
    return {"message": "添加成功"}


@router.delete("/{email}/subscriptions/{stock_code_or_name}")
async def delete_user_subscription(
    email: str, stock_code_or_name: str, current_user: str = Depends(get_current_user)
):
    """删除用户订阅"""
    result = remove_subscription(email, stock_code_or_name)

    if not result:
        raise HTTPException(status_code=404, detail="订阅不存在")

    logger.info(f"管理员 {current_user} 删除订阅: {email} -> {stock_code_or_name}")
    return {"message": "删除成功"}


@router.post("/cleanup")
async def cleanup_expired(current_user: str = Depends(get_current_user)):
    """清理过期用户"""
    count = cleanup_expired_users()
    logger.info(f"管理员 {current_user} 清理过期用户: {count}个")
    return {"message": f"已清理 {count} 个过期用户"}
