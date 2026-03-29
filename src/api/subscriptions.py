"""
订阅管理API模块
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from .auth import get_current_user
from ..models.db import Subscription, User, get_session
from ..utils.logger import get_logger

logger = get_logger("subscriptions_api")

router = APIRouter(prefix="/api/subscriptions", tags=["订阅管理"])


class SubscriptionCreate(BaseModel):
    stock_code: str
    stock_name: str
    market: str
    rules: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    market: Optional[str] = None
    rules: Optional[str] = None
    is_active: Optional[bool] = None


class SubscriptionResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    market: str
    rules: Optional[str]
    is_active: bool
    created_at: str


@router.get("/", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    market: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: str = Depends(get_current_user),
):
    """获取订阅列表"""
    session = get_session()
    try:
        query = session.query(Subscription)

        if market:
            query = query.filter(Subscription.market == market)
        if is_active is not None:
            query = query.filter(Subscription.is_active == is_active)

        subscriptions = query.order_by(Subscription.created_at.desc()).all()

        return [
            SubscriptionResponse(
                id=s.id,
                stock_code=s.stock_code,
                stock_name=s.stock_name,
                market=s.market,
                rules=s.rules,
                is_active=s.is_active,
                created_at=s.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if s.created_at
                else "",
            )
            for s in subscriptions
        ]
    finally:
        session.close()


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int, current_user: str = Depends(get_current_user)
):
    """获取订阅详情"""
    session = get_session()
    try:
        subscription = (
            session.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        return SubscriptionResponse(
            id=subscription.id,
            stock_code=subscription.stock_code,
            stock_name=subscription.stock_name,
            market=subscription.market,
            rules=subscription.rules,
            is_active=subscription.is_active,
            created_at=subscription.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if subscription.created_at
            else "",
        )
    finally:
        session.close()


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription: SubscriptionCreate,
    current_user: str = Depends(get_current_user),
):
    """创建订阅"""
    session = get_session()
    try:
        new_subscription = Subscription(
            stock_code=subscription.stock_code,
            stock_name=subscription.stock_name,
            market=subscription.market,
            rules=subscription.rules,
            is_active=True,
        )
        session.add(new_subscription)
        session.commit()
        session.refresh(new_subscription)

        logger.info(f"管理员 {current_user} 创建订阅: {subscription.stock_name}")

        return SubscriptionResponse(
            id=new_subscription.id,
            stock_code=new_subscription.stock_code,
            stock_name=new_subscription.stock_name,
            market=new_subscription.market,
            rules=new_subscription.rules,
            is_active=new_subscription.is_active,
            created_at=new_subscription.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if new_subscription.created_at
            else "",
        )
    finally:
        session.close()


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    subscription_update: SubscriptionUpdate,
    current_user: str = Depends(get_current_user),
):
    """更新订阅"""
    session = get_session()
    try:
        subscription = (
            session.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        if subscription_update.stock_code is not None:
            subscription.stock_code = subscription_update.stock_code
        if subscription_update.stock_name is not None:
            subscription.stock_name = subscription_update.stock_name
        if subscription_update.market is not None:
            subscription.market = subscription_update.market
        if subscription_update.rules is not None:
            subscription.rules = subscription_update.rules
        if subscription_update.is_active is not None:
            subscription.is_active = subscription_update.is_active

        session.commit()
        session.refresh(subscription)

        logger.info(f"管理员 {current_user} 更新订阅: {subscription_id}")

        return SubscriptionResponse(
            id=subscription.id,
            stock_code=subscription.stock_code,
            stock_name=subscription.stock_name,
            market=subscription.market,
            rules=subscription.rules,
            is_active=subscription.is_active,
            created_at=subscription.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if subscription.created_at
            else "",
        )
    finally:
        session.close()


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: int, current_user: str = Depends(get_current_user)
):
    """删除订阅"""
    session = get_session()
    try:
        subscription = (
            session.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        session.delete(subscription)
        session.commit()

        logger.info(f"管理员 {current_user} 删除订阅: {subscription_id}")
        return {"message": "删除成功"}
    finally:
        session.close()


@router.post("/monitor/run")
async def run_monitor(current_user: str = Depends(get_current_user)):
    """手动触发监控"""
    from ..monitors.stock_monitor import StockMonitor

    try:
        monitor = StockMonitor()
        await monitor.run_monitoring()
        return {"message": "监控已执行"}
    except Exception as e:
        logger.error(f"监控执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
