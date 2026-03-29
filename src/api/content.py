"""
内容管理API模块
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from .auth import get_current_user
from ..models.db import Content, get_session
from ..utils.logger import get_logger
from ..scheduler.jobs import us_stock_job, a_share_job, ipo_job, hot_stock_job
import asyncio

logger = get_logger("content_api")

router = APIRouter(prefix="/api/content", tags=["内容管理"])


class ContentResponse(BaseModel):
    id: int
    market: str
    content_type: str
    title: str
    content: str
    tags: str
    status: str
    created_at: str


@router.get("/", response_model=List[ContentResponse])
async def list_content(
    market: Optional[str] = None,
    content_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: str = Depends(get_current_user),
):
    """获取内容列表"""
    session = get_session()
    try:
        query = session.query(Content)

        if market:
            query = query.filter(Content.market == market)
        if content_type:
            query = query.filter(Content.content_type == content_type)
        if date_from:
            query = query.filter(Content.created_at >= date_from)
        if date_to:
            query = query.filter(Content.created_at <= date_to)

        contents = query.order_by(Content.created_at.desc()).limit(limit).all()

        return [
            ContentResponse(
                id=c.id,
                market=c.market,
                content_type=c.content_type,
                title=c.title,
                content=c.content,
                tags=c.tags or "",
                status=c.status,
                created_at=c.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if c.created_at
                else "",
            )
            for c in contents
        ]
    finally:
        session.close()


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, current_user: str = Depends(get_current_user)):
    """获取内容详情"""
    session = get_session()
    try:
        content = session.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="内容不存在")

        return ContentResponse(
            id=content.id,
            market=content.market,
            content_type=content.content_type,
            title=content.title,
            content=content.content,
            tags=content.tags or "",
            status=content.status,
            created_at=content.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if content.created_at
            else "",
        )
    finally:
        session.close()


@router.delete("/{content_id}")
async def delete_content(
    content_id: int, current_user: str = Depends(get_current_user)
):
    """删除内容"""
    session = get_session()
    try:
        content = session.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="内容不存在")

        session.delete(content)
        session.commit()

        logger.info(f"管理员 {current_user} 删除内容: {content_id}")
        return {"message": "删除成功"}
    finally:
        session.close()


@router.post("/trigger/us")
async def trigger_us_stock(current_user: str = Depends(get_current_user)):
    """手动触发美股总结"""
    logger.info(f"管理员 {current_user} 手动触发美股总结")
    try:
        await us_stock_job()
        return {"message": "美股总结任务已执行"}
    except Exception as e:
        logger.error(f"美股总结任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/a-share")
async def trigger_a_share(current_user: str = Depends(get_current_user)):
    """手动触发A股港股总结"""
    logger.info(f"管理员 {current_user} 手动触发A股港股总结")
    try:
        await a_share_job()
        return {"message": "A股港股总结任务已执行"}
    except Exception as e:
        logger.error(f"A股港股总结任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/ipo")
async def trigger_ipo(current_user: str = Depends(get_current_user)):
    """手动触发IPO分析"""
    logger.info(f"管理员 {current_user} 手动触发IPO分析")
    try:
        await ipo_job()
        return {"message": "IPO分析任务已执行"}
    except Exception as e:
        logger.error(f"IPO分析任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/hot")
async def trigger_hot_stock(current_user: str = Depends(get_current_user)):
    """手动触发热点个股"""
    logger.info(f"管理员 {current_user} 手动触发热点个股")
    try:
        await hot_stock_job()
        return {"message": "热点个股任务已执行"}
    except Exception as e:
        logger.error(f"热点个股任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_content_stats(current_user: str = Depends(get_current_user)):
    """获取内容统计"""
    session = get_session()
    try:
        today = date.today().strftime("%Y-%m-%d")
        today_count = session.query(Content).filter(Content.created_at >= today).count()

        total_count = session.query(Content).count()

        return {"today_count": today_count, "total_count": total_count}
    finally:
        session.close()
