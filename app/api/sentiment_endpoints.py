"""
散户情绪分析 API 路由

包含情绪指数查询、历史数据、评论样本、数据源状态、手动触发和权重配置端点。
Requirements: 9.18, 9.21, 9.29, 9.30
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select

from app.database import async_session_factory
from app.models import SentimentCommentDB
from app.schemas import SentimentSnapshot, SentimentSourceStatus

router = APIRouter()


# ---------------------------------------------------------------------------
# Singleton service instances (lazy-loaded)
# ---------------------------------------------------------------------------

def _get_analyzer():
    from app.services.sentiment_analyzer import SentimentAnalyzer
    if not hasattr(_get_analyzer, "_instance"):
        _get_analyzer._instance = SentimentAnalyzer()
    return _get_analyzer._instance


def _get_mixed_data_service():
    return _get_analyzer().mixed_data_service


def _get_crawler():
    return _get_analyzer().crawler


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class WeightsUpdateRequest(BaseModel):
    """权重更新请求"""
    comment_sentiment: Optional[float] = None
    baidu_vote: Optional[float] = None
    akshare_aggregate: Optional[float] = None
    news_sentiment: Optional[float] = None
    margin_trading: Optional[float] = None


class TriggerRequest(BaseModel):
    """手动触发请求"""
    stock_code: Optional[str] = None
    time_window_hours: int = 24


# ---------------------------------------------------------------------------
# GET /index — 获取大盘整体情绪指数
# ---------------------------------------------------------------------------

@router.get("/index")
async def get_market_sentiment_index():
    """获取大盘整体情绪指数（含综合指数和各分项得分）。

    Returns the latest overall market sentiment snapshot, or a default
    neutral response if no data is available yet.
    """
    analyzer = _get_analyzer()

    try:
        snapshot = await analyzer.get_latest_index(stock_code=None)
        if snapshot is None:
            return {
                "success": True,
                "data": None,
                "message": "暂无情绪数据，请先触发一轮情绪采集",
            }
        return {"success": True, "data": snapshot.model_dump()}
    except Exception as e:
        logger.error(f"获取大盘情绪指数失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取情绪指数失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /index/{stock_code} — 获取个股情绪指数
# ---------------------------------------------------------------------------

@router.get("/index/{stock_code}")
async def get_stock_sentiment_index(stock_code: str):
    """获取指定股票的情绪指数（含综合指数和各分项得分）。"""
    stock_code = stock_code.strip()
    if not stock_code:
        raise HTTPException(status_code=400, detail="stock_code 不能为空")

    analyzer = _get_analyzer()

    try:
        snapshot = await analyzer.get_latest_index(stock_code=stock_code)
        if snapshot is None:
            return {
                "success": True,
                "data": None,
                "message": f"暂无 {stock_code} 的情绪数据",
            }
        return {"success": True, "data": snapshot.model_dump()}
    except Exception as e:
        logger.error(f"获取个股情绪指数失败 ({stock_code}): {e}")
        raise HTTPException(status_code=500, detail=f"获取情绪指数失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /history — 获取情绪指数历史数据
# ---------------------------------------------------------------------------

@router.get("/history")
async def get_sentiment_history(
    stock_code: Optional[str] = None,
    days: int = 30,
):
    """获取情绪指数历史数据，支持 stock_code 和 days 参数。

    - stock_code: 股票代码，为空时返回大盘历史
    - days: 历史天数（1-365，默认30）
    """
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days 必须在 1-365 之间")

    analyzer = _get_analyzer()

    try:
        history = await analyzer.get_index_history(
            stock_code=stock_code, days=days
        )
        return {
            "success": True,
            "items": [s.model_dump() for s in history],
            "total": len(history),
            "stock_code": stock_code,
            "days": days,
        }
    except Exception as e:
        logger.error(f"获取情绪历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /comments — 获取最近评论样本
# ---------------------------------------------------------------------------

@router.get("/comments")
async def get_recent_comments(
    stock_code: Optional[str] = None,
    limit: int = 50,
):
    """获取最近的评论样本。

    - stock_code: 按股票代码筛选，为空时返回所有
    - limit: 返回条数上限（1-200，默认50）
    """
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit 必须在 1-200 之间")

    try:
        async with async_session_factory() as session:
            stmt = select(SentimentCommentDB).order_by(
                SentimentCommentDB.published_time.desc()
            )
            if stock_code:
                stmt = stmt.where(SentimentCommentDB.stock_code == stock_code)
            stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            rows = result.scalars().all()

            comments = []
            for row in rows:
                pub_time = ""
                if row.published_time:
                    pub_time = (
                        row.published_time.isoformat()
                        if hasattr(row.published_time, "isoformat")
                        else str(row.published_time)
                    )
                comments.append({
                    "id": row.id,
                    "content": row.content,
                    "source_platform": row.source_platform,
                    "stock_code": row.stock_code,
                    "author_nickname": row.author_nickname,
                    "published_time": pub_time,
                    "sentiment_label": row.sentiment_label,
                    "sentiment_score": row.sentiment_score,
                })

        return {
            "success": True,
            "items": comments,
            "total": len(comments),
            "stock_code": stock_code,
        }
    except Exception as e:
        logger.error(f"获取评论样本失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评论数据失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /status — 获取各数据源采集状态
# ---------------------------------------------------------------------------

@router.get("/status")
async def get_source_status():
    """获取各情绪数据源的采集状态（分评论爬虫源和聚合指标源两组）。"""
    crawler = _get_crawler()

    try:
        crawler_statuses = crawler.get_source_status()

        # Build aggregate source statuses from mixed data service
        aggregate_sources = {
            "akshare_comment": "AKShare 千股千评",
            "baidu_vote": "百度股市通投票",
            "news_sentiment": "新闻情绪指数",
            "margin_trading": "融资融券数据",
            "xueqiu_heat": "雪球热度数据",
        }

        aggregate_statuses = {}
        for source_id, display_name in aggregate_sources.items():
            aggregate_statuses[source_id] = SentimentSourceStatus(
                source_id=source_id,
                source_type="aggregate",
                status="normal",
            ).model_dump()

        return {
            "success": True,
            "crawler_sources": {
                k: v.model_dump() for k, v in crawler_statuses.items()
            },
            "aggregate_sources": aggregate_statuses,
        }
    except Exception as e:
        logger.error(f"获取数据源状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST /trigger — 手动触发一轮情绪采集和分析
# ---------------------------------------------------------------------------

@router.post("/trigger")
async def trigger_sentiment_analysis(request: Optional[TriggerRequest] = None):
    """手动触发一轮情绪采集和分析。

    可选参数：
    - stock_code: 指定个股代码，为空时分析大盘
    - time_window_hours: 采集时间窗口（默认24小时）
    """
    stock_code = request.stock_code if request else None
    time_window_hours = request.time_window_hours if request else 24

    analyzer = _get_analyzer()

    try:
        snapshot = await analyzer.run_analysis_cycle(
            stock_code=stock_code,
            time_window_hours=time_window_hours,
        )
        if snapshot is None:
            return {
                "success": False,
                "message": "情绪分析执行失败，请查看日志",
            }
        return {
            "success": True,
            "data": snapshot.model_dump(),
            "message": "情绪分析完成",
        }
    except Exception as e:
        logger.error(f"手动触发情绪分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"情绪分析失败: {str(e)}")


# ---------------------------------------------------------------------------
# PUT /weights — 更新各分项权重配置
# ---------------------------------------------------------------------------

@router.put("/weights")
async def update_sentiment_weights(request: WeightsUpdateRequest):
    """更新各分项权重配置。

    权重值为 0-1 之间的浮点数，总和应为 1.0。
    仅更新请求中提供的字段，未提供的保持不变。
    """
    mixed_service = _get_mixed_data_service()

    new_weights = {}
    if request.comment_sentiment is not None:
        new_weights["comment_sentiment"] = request.comment_sentiment
    if request.baidu_vote is not None:
        new_weights["baidu_vote"] = request.baidu_vote
    if request.akshare_aggregate is not None:
        new_weights["akshare_aggregate"] = request.akshare_aggregate
    if request.news_sentiment is not None:
        new_weights["news_sentiment"] = request.news_sentiment
    if request.margin_trading is not None:
        new_weights["margin_trading"] = request.margin_trading

    if not new_weights:
        raise HTTPException(status_code=400, detail="至少需要提供一个权重字段")

    # Validate: all values must be in [0, 1]
    for key, val in new_weights.items():
        if val < 0 or val > 1:
            raise HTTPException(
                status_code=400,
                detail=f"权重 {key} 必须在 0-1 之间，当前值: {val}",
            )

    try:
        mixed_service.update_weights(new_weights)

        # Also update scheduler interval if provided via settings
        return {
            "success": True,
            "message": "权重配置已更新",
            "current_weights": mixed_service.weights,
        }
    except Exception as e:
        logger.error(f"更新权重配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新权重失败: {str(e)}")
