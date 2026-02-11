"""
社交内容生成与发布 API 路由

包含内容生成、每日速报、发布、历史记录等端点。
Requirements: 5.1, 5.6, 5.7, 7.3, 7.4
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.schemas import (
    DailyReportRequest,
    SocialContent,
    SocialContentRequest,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /generate — 根据推演结果生成指定平台格式内容
# ---------------------------------------------------------------------------

@router.post("/generate")
async def generate_content(request: SocialContentRequest):
    """根据推演结果生成指定平台格式的社交内容。

    请求体：
    - analysis_id: 关联的推演结果 ID（必填）
    - platform: 目标平台 xhs / weibo / xueqiu / zhihu（必填）
    """
    if not request.analysis_id or not request.analysis_id.strip():
        raise HTTPException(status_code=400, detail="analysis_id 不能为空")

    valid_platforms = {"xhs", "weibo", "xueqiu", "zhihu"}
    if request.platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"platform 无效，可选值: {', '.join(sorted(valid_platforms))}",
        )

    from app.services.stock_analysis_service import stock_analysis_service
    from app.services.social_content_generator import social_content_generator
    from app.services.compliance_service import compliance_service

    # 获取推演结果
    analysis = await stock_analysis_service.get_by_id(request.analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"推演结果不存在: {request.analysis_id}")

    try:
        content = await social_content_generator.generate_content(analysis, request.platform)

        # 合规脱敏处理
        try:
            content.body = compliance_service.desensitize_content(content.body)
        except Exception as e:
            logger.warning(f"合规脱敏处理失败，使用原始内容: {e}")

        return {
            "success": True,
            "data": content.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"内容生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"内容生成失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST /daily-report — 生成每日股市速报
# ---------------------------------------------------------------------------

@router.post("/daily-report")
async def generate_daily_report(request: DailyReportRequest = DailyReportRequest()):
    """生成每日股市速报。

    请求体（可选）：
    - platform: 目标平台格式（默认 xhs）
    - include_analysis: 是否包含 LLM 分析（默认 True）
    """
    from app.services.stock_news_collector import stock_news_collector
    from app.services.social_content_generator import social_content_generator

    try:
        # 采集今日资讯作为速报素材
        news_result = await stock_news_collector.collect_news()
        news_items = news_result.items[:20] if news_result.items else []

        # 生成各平台速报
        reports = await social_content_generator.generate_daily_report(news_items)

        # 持久化到数据库，供 /daily-report/latest 查询
        for content in reports.values():
            await social_content_generator._persist_content(content)

        return {
            "success": True,
            "data": {k: v.model_dump() for k, v in reports.items()},
            "platforms": list(reports.keys()),
            "news_count": len(news_items),
        }
    except Exception as e:
        logger.error(f"每日速报生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"速报生成失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /daily-report/latest — 获取当日最新速报内容
# ---------------------------------------------------------------------------

@router.get("/daily-report/latest")
async def get_latest_daily_report():
    """获取当日最新的速报内容"""
    from app.services.social_content_generator import social_content_generator

    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        history = await social_content_generator.get_history(limit=10)

        # 筛选今日的 daily_report 类型内容
        today_reports = [
            item for item in history
            if item.content_type == "daily_report"
            and item.created_at.startswith(today_str)
        ]

        if not today_reports:
            return {"success": True, "data": None, "message": "今日暂无速报"}

        # 按平台分组，取每个平台最新的一条
        latest_by_platform = {}
        for report in today_reports:
            if report.platform not in latest_by_platform:
                latest_by_platform[report.platform] = report

        return {
            "success": True,
            "data": {k: v.model_dump() for k, v in latest_by_platform.items()},
            "date": today_str,
        }
    except Exception as e:
        logger.error(f"获取最新速报失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取最新速报失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /daily-report/history — 获取历史速报列表
# ---------------------------------------------------------------------------

@router.get("/daily-report/history")
async def get_daily_report_history(limit: int = 20, offset: int = 0):
    """获取历史速报列表，支持分页。

    - limit: 每页条数（1-100，默认20）
    - offset: 偏移量（默认0）
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit 必须在 1-100 之间")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset 不能为负数")

    from app.services.social_content_generator import social_content_generator

    try:
        # 查询 daily_report 类型的历史记录
        all_history = await social_content_generator.get_history(
            limit=limit + offset + 50  # 多取一些用于过滤
        )
        reports = [
            item for item in all_history
            if item.content_type == "daily_report"
        ]
        # 分页
        paged = reports[offset : offset + limit]

        return {
            "success": True,
            "items": [r.model_dump() for r in paged],
            "total": len(reports),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"查询速报历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询速报历史失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST /daily-report/publish-all — 一键发布速报到全平台
# ---------------------------------------------------------------------------

@router.post("/daily-report/publish-all")
async def publish_daily_report_all():
    """一键发布当日最新速报到全平台（当前 = 小红书）"""
    from app.services.social_content_generator import social_content_generator

    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        history = await social_content_generator.get_history(limit=10)

        # 找到今日小红书速报
        xhs_report = None
        for item in history:
            if (
                item.content_type == "daily_report"
                and item.platform == "xhs"
                and item.created_at.startswith(today_str)
            ):
                xhs_report = item
                break

        if not xhs_report:
            raise HTTPException(status_code=404, detail="今日暂无小红书速报，请先生成速报")

        results = await social_content_generator.publish_all_platforms(xhs_report)

        return {
            "success": True,
            "results": results,
            "content_id": xhs_report.id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"速报发布失败: {e}")
        raise HTTPException(status_code=500, detail=f"速报发布失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST /publish/xhs — 一键发布到小红书
# ---------------------------------------------------------------------------

@router.post("/publish/xhs")
async def publish_to_xhs(content_id: str):
    """将指定内容发布到小红书。

    Query 参数：
    - content_id: 要发布的内容 ID
    """
    if not content_id or not content_id.strip():
        raise HTTPException(status_code=400, detail="content_id 不能为空")

    from app.services.social_content_generator import social_content_generator

    content = await social_content_generator.get_by_id(content_id)
    if content is None:
        raise HTTPException(status_code=404, detail=f"内容不存在: {content_id}")

    if content.status == "published":
        return {"success": True, "message": "该内容已发布", "data": content.model_dump()}

    try:
        result = await social_content_generator.publish_to_xhs(content)
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "data": content.model_dump(),
            "publish_result": result,
        }
    except Exception as e:
        logger.error(f"小红书发布失败: {e}")
        raise HTTPException(status_code=500, detail=f"小红书发布失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /history — 获取历史生成/发布记录
# ---------------------------------------------------------------------------

@router.get("/history")
async def get_content_history(
    limit: int = 20,
    offset: int = 0,
    platform: Optional[str] = None,
):
    """获取历史内容记录，支持分页和平台筛选。

    - limit: 每页条数（1-100，默认20）
    - offset: 偏移量（默认0）
    - platform: 按平台筛选（xhs / weibo / xueqiu / zhihu）
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit 必须在 1-100 之间")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset 不能为负数")

    valid_platforms = {"xhs", "weibo", "xueqiu", "zhihu"}
    if platform and platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"platform 无效，可选值: {', '.join(sorted(valid_platforms))}",
        )

    from app.services.social_content_generator import social_content_generator

    try:
        items = await social_content_generator.get_history(
            limit=limit, offset=offset, platform=platform
        )
        return {
            "success": True,
            "items": [i.model_dump() for i in items],
            "total": len(items),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"查询内容历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询内容历史失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /{content_id} — 获取单条内容详情
# ---------------------------------------------------------------------------

@router.get("/{content_id}")
async def get_content_detail(content_id: str):
    """获取单条内容详情"""
    content_id = content_id.strip()
    if not content_id:
        raise HTTPException(status_code=400, detail="content_id 不能为空")

    from app.services.social_content_generator import social_content_generator

    try:
        content = await social_content_generator.get_by_id(content_id)
        if content is None:
            raise HTTPException(status_code=404, detail=f"内容不存在: {content_id}")
        return {
            "success": True,
            "data": content.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询内容详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询内容详情失败: {str(e)}")


# ---------------------------------------------------------------------------
# PUT /{content_id} — 更新/编辑已生成内容
# ---------------------------------------------------------------------------

@router.put("/{content_id}")
async def update_content(content_id: str, payload: dict):
    """更新/编辑已生成的内容。

    支持更新的字段：title, body, tags, image_urls, desensitization_level
    """
    content_id = content_id.strip()
    if not content_id:
        raise HTTPException(status_code=400, detail="content_id 不能为空")

    from sqlalchemy import update
    from app.database import async_session_factory
    from app.models import SocialContentDB
    from app.services.social_content_generator import social_content_generator

    # 先确认内容存在
    content = await social_content_generator.get_by_id(content_id)
    if content is None:
        raise HTTPException(status_code=404, detail=f"内容不存在: {content_id}")

    # 可更新字段白名单
    allowed_fields = {"title", "body", "tags", "image_urls", "desensitization_level"}
    update_values = {}
    for field in allowed_fields:
        if field in payload:
            value = payload[field]
            # tags 和 image_urls 需要序列化为 JSON 字符串
            if field in ("tags", "image_urls") and isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            update_values[field] = value

    if not update_values:
        raise HTTPException(status_code=400, detail="没有可更新的字段")

    try:
        async with async_session_factory() as session:
            stmt = (
                update(SocialContentDB)
                .where(SocialContentDB.id == content_id)
                .values(**update_values)
            )
            await session.execute(stmt)
            await session.commit()

        # 返回更新后的内容
        updated = await social_content_generator.get_by_id(content_id)
        return {
            "success": True,
            "data": updated.model_dump() if updated else None,
            "message": "内容已更新",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新内容失败: {str(e)}")
