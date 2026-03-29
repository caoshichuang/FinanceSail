"""
内容分发API模块
"""

import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from .auth import get_current_user
from ..models.db import Content, get_session
from ..distributors import XiaohongshuPublisher, WeChatPublisher, ToutiaoPublisher
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger("distribution_api")

router = APIRouter(prefix="/api/distribution", tags=["内容分发"])


class DistributionRequest(BaseModel):
    content_id: int
    platform: str  # xiaohongshu/wechat/toutiao
    auto_publish: bool = False


class DistributionResponse(BaseModel):
    success: bool
    message: str
    data: dict = None


@router.post("/xiaohongshu/{content_id}", response_model=DistributionResponse)
async def distribute_to_xiaohongshu(
    content_id: int,
    current_user: str = Depends(get_current_user),
):
    """分发到小红书"""
    session = get_session()
    try:
        content = session.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="内容不存在")

        # 获取图片URL
        image_urls = []
        if content.image_paths:
            try:
                image_paths = json.loads(content.image_paths)
                base_url = settings.BASE_URL
                for path in image_paths:
                    # 转换为可访问的URL
                    image_urls.append(f"{base_url}/images/{path.split('/')[-1]}")
            except json.JSONDecodeError:
                pass

        # 格式化内容
        publisher = XiaohongshuPublisher()
        tags = content.tags.split() if content.tags else []
        formatted_content = publisher.format_content(
            title=content.title,
            content=content.content,
            tags=tags,
        )

        # 验证内容
        validation = publisher.validate_content(formatted_content)
        if not validation["valid"]:
            return DistributionResponse(
                success=False,
                message=f"内容验证失败: {', '.join(validation['errors'])}",
            )

        # 生成发布指引
        instructions = publisher.generate_publish_instructions(
            formatted_content, image_urls
        )

        return DistributionResponse(
            success=True,
            message="小红书内容已准备好",
            data={
                "formatted_content": formatted_content,
                "image_urls": image_urls,
                "instructions": instructions,
                "warnings": validation.get("warnings", []),
            },
        )
    except Exception as e:
        logger.error(f"小红书分发失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/wechat/{content_id}", response_model=DistributionResponse)
async def distribute_to_wechat(
    content_id: int,
    auto_publish: bool = False,
    current_user: str = Depends(get_current_user),
):
    """分发到微信公众号"""
    session = get_session()
    try:
        content = session.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="内容不存在")

        # 检查微信配置
        app_id = getattr(settings, "WECHAT_APP_ID", "")
        app_secret = getattr(settings, "WECHAT_APP_SECRET", "")
        if not app_id or not app_secret:
            return DistributionResponse(
                success=False,
                message="微信公众号未配置，请先配置WECHAT_APP_ID和WECHAT_APP_SECRET",
            )

        # 获取封面图
        cover_media_id = None
        if content.image_paths:
            try:
                image_paths = json.loads(content.image_paths)
                if image_paths:
                    publisher = WeChatPublisher(app_id, app_secret)
                    base_url = settings.BASE_URL
                    cover_url = f"{base_url}/images/{image_paths[0].split('/')[-1]}"
                    cover_media_id = publisher.upload_image(cover_url)
            except Exception as e:
                logger.error(f"上传封面图失败: {e}")

        if not cover_media_id:
            return DistributionResponse(
                success=False,
                message="封面图上传失败",
            )

        # 格式化内容
        publisher = WeChatPublisher(app_id, app_secret)
        tags = content.tags.split() if content.tags else []
        html_content = publisher.format_content_for_wechat(
            title=content.title,
            content=content.content,
            tags=tags,
        )

        # 创建草稿
        draft_media_id = publisher.create_draft(
            title=content.title,
            content=html_content,
            thumb_media_id=cover_media_id,
            author="FinanceSail",
            digest=content.content[:54],
        )

        if not draft_media_id:
            return DistributionResponse(
                success=False,
                message="创建草稿失败",
            )

        # 自动发布
        if auto_publish:
            publish_id = publisher.publish_article(draft_media_id)
            if publish_id:
                return DistributionResponse(
                    success=True,
                    message="文章已提交发布",
                    data={
                        "draft_media_id": draft_media_id,
                        "publish_id": publish_id,
                        "status": "publishing",
                    },
                )
            else:
                return DistributionResponse(
                    success=False,
                    message="发布失败",
                )

        return DistributionResponse(
            success=True,
            message="草稿已创建",
            data={
                "draft_media_id": draft_media_id,
                "status": "draft",
            },
        )
    except Exception as e:
        logger.error(f"微信公众号分发失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/toutiao/{content_id}", response_model=DistributionResponse)
async def distribute_to_toutiao(
    content_id: int,
    auto_publish: bool = False,
    current_user: str = Depends(get_current_user),
):
    """分发到今日头条"""
    session = get_session()
    try:
        content = session.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="内容不存在")

        # 检查头条配置
        access_token = getattr(settings, "TOUTIAO_ACCESS_TOKEN", "")
        if not access_token:
            return DistributionResponse(
                success=False,
                message="今日头条未配置，请先配置TOUTIAO_ACCESS_TOKEN",
            )

        # 获取封面图URL
        cover_images = []
        if content.image_paths:
            try:
                image_paths = json.loads(content.image_paths)
                base_url = settings.BASE_URL
                for path in image_paths[:3]:
                    cover_images.append(f"{base_url}/images/{path.split('/')[-1]}")
            except json.JSONDecodeError:
                pass

        # 格式化内容
        publisher = ToutiaoPublisher(access_token)
        tags = content.tags.split() if content.tags else []
        html_content = publisher.format_content_for_toutiao(
            title=content.title,
            content=content.content,
            tags=tags,
        )

        # 创建文章
        article_id = publisher.create_article(
            title=content.title,
            content=html_content,
            cover_images=cover_images,
            abstract=content.content[:120],
        )

        if not article_id:
            return DistributionResponse(
                success=False,
                message="创建文章失败",
            )

        # 自动发布
        if auto_publish:
            success = publisher.publish_article(article_id)
            if success:
                return DistributionResponse(
                    success=True,
                    message="文章已发布",
                    data={
                        "article_id": article_id,
                        "status": "published",
                    },
                )
            else:
                return DistributionResponse(
                    success=False,
                    message="发布失败",
                )

        return DistributionResponse(
            success=True,
            message="文章已创建",
            data={
                "article_id": article_id,
                "status": "draft",
            },
        )
    except Exception as e:
        logger.error(f"今日头条分发失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/status/{content_id}")
async def get_distribution_status(
    content_id: int,
    current_user: str = Depends(get_current_user),
):
    """获取分发状态"""
    # TODO: 实现分发状态查询
    return {
        "content_id": content_id,
        "platforms": {
            "xiaohongshu": {"status": "not_distributed"},
            "wechat": {"status": "not_distributed"},
            "toutiao": {"status": "not_distributed"},
        },
    }
