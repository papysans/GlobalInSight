"""
股票资讯相关 API 路由
包含资讯列表、数据源管理、投行研报共识评级、行情推演等端点
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from app.schemas import (
    DataSourceConfig,
    DataSourceConfigResponse,
    DataSourceStatus,
    StockAnalysisRequest,
    StockAnalysisStep,
    StockNewsCollectResponse,
    StockNewsItem,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# 数据源元信息（合并国内 + 国际 + 研报三类）
# ---------------------------------------------------------------------------

def _build_all_source_configs() -> list[DataSourceConfig]:
    """构建所有数据源的配置信息列表（国内 + 国际 + 研报）"""
    from app.services.stock_news_collector import STOCK_SOURCES
    from app.services.international_news_service import INTERNATIONAL_SOURCES
    from app.services.research_report_service import RESEARCH_SOURCES
    from app.config import Config

    configs: list[DataSourceConfig] = []

    # 国内数据源
    for sid, info in STOCK_SOURCES.items():
        requires_key = info.get("requires_api_key", False)
        if requires_key:
            has_key = bool(getattr(Config, "TUSHARE_TOKEN", "")) if sid == "tushare" else False
            status = DataSourceStatus.CONFIGURED if has_key else DataSourceStatus.NOT_CONFIGURED
        else:
            status = DataSourceStatus.FREE
        configs.append(DataSourceConfig(
            source_id=sid,
            display_name=info.get("name", sid),
            category="domestic",
            requires_api_key=requires_key,
            enabled=info.get("enabled", True),
            status=status,
        ))

    # 国际财经数据源
    _intl_key_map = {
        "finnhub": "FINNHUB_API_KEY",
        "newsapi": "NEWSAPI_API_KEY",
        "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
        "marketaux": "MARKETAUX_API_KEY",
    }
    for sid, info in INTERNATIONAL_SOURCES.items():
        requires_key = info.get("requires_api_key", False)
        if requires_key:
            attr = _intl_key_map.get(sid, "")
            has_key = bool(getattr(Config, attr, "")) if attr else False
            status = DataSourceStatus.CONFIGURED if has_key else DataSourceStatus.NOT_CONFIGURED
        else:
            status = DataSourceStatus.FREE
        configs.append(DataSourceConfig(
            source_id=sid,
            display_name=info.get("name", sid),
            category="international",
            requires_api_key=requires_key,
            enabled=info.get("enabled", True),
            status=status,
        ))

    # 投行研报数据源
    _research_key_map = {
        "finnhub_research": "FINNHUB_API_KEY",
        "benzinga": "BENZINGA_API_KEY",
        "seekingalpha": "SEEKING_ALPHA_API_KEY",
    }
    for sid, info in RESEARCH_SOURCES.items():
        requires_key = info.get("requires_api_key", False)
        if requires_key:
            attr = _research_key_map.get(sid, "")
            has_key = bool(getattr(Config, attr, "")) if attr else False
            status = DataSourceStatus.CONFIGURED if has_key else DataSourceStatus.NOT_CONFIGURED
        else:
            status = DataSourceStatus.FREE
        configs.append(DataSourceConfig(
            source_id=sid,
            display_name=info.get("name", sid),
            category="research_report",
            requires_api_key=requires_key,
            enabled=True,
            status=status,
        ))

    return configs


# ---------------------------------------------------------------------------
# GET /hot — 热榜聚类数据（话题聚类 + 跨平台对齐 + 历史信号）
# ---------------------------------------------------------------------------

@router.get("/hot")
async def get_hot_news(force_refresh: bool = False):
    """获取热榜聚类数据。

    数据源：新浪财经 + 东方财富(AKShare) + 雪球 + 同花顺
    返回话题聚类结果，包含跨平台热度叠加、争议检测、历史信号。
    """
    from app.services.stock_news_collector import stock_news_collector

    try:
        result = await stock_news_collector.collect_hot_news(
            force_refresh=force_refresh,
        )
        return result
    except Exception as e:
        logger.error(f"热榜聚类采集失败: {e}")
        raise HTTPException(status_code=500, detail=f"热榜采集失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /news — 获取股票资讯列表
# ---------------------------------------------------------------------------

@router.get("/news")
async def get_stock_news(
    limit: int = 50,
    source: Optional[str] = None,
    category: Optional[str] = None,
    force_refresh: bool = False,
):
    """获取股票资讯列表。

    - limit: 返回条数上限（1-200）
    - source: 按数据源筛选（如 akshare、sina、finnhub 等）
    - category: 按类别筛选（domestic / international / research_report）
    - force_refresh: 是否跳过缓存
    """
    # 参数校验
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit 必须在 1-200 之间")

    valid_categories = {"domestic", "international", "research_report"}
    if category and category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"category 无效，可选值: {', '.join(sorted(valid_categories))}",
        )

    from app.services.stock_news_collector import stock_news_collector

    # 根据 category 决定是否包含国际/研报
    include_international = category in (None, "international")
    include_research = category in (None, "research_report")

    # 根据 source 决定国内数据源列表
    source_ids = [source] if source else None

    try:
        result: StockNewsCollectResponse = await stock_news_collector.collect_news(
            source_ids=source_ids,
            force_refresh=force_refresh,
            include_international=include_international,
            include_research=include_research,
        )
    except Exception as e:
        logger.error(f"股票资讯采集失败: {e}")
        raise HTTPException(status_code=500, detail=f"资讯采集失败: {str(e)}")

    items = result.items

    # 按 category 过滤
    if category:
        items = [i for i in items if i.category == category]

    # 按 source 过滤（国际/研报源也可能匹配）
    if source:
        items = [i for i in items if i.source_platform == source]

    # 截断
    items = items[:limit]

    return {
        "success": True,
        "items": [i.model_dump() for i in items],
        "total": len(items),
        "source_stats": result.source_stats,
        "category_stats": result.category_stats,
        "collection_time": result.collection_time,
        "from_cache": result.from_cache,
    }


# ---------------------------------------------------------------------------
# GET /sources — 获取数据源列表及状态
# ---------------------------------------------------------------------------

@router.get("/sources")
async def get_stock_sources():
    """获取所有支持的数据源列表及状态（国内 + 国际 + 研报）"""
    configs = _build_all_source_configs()

    # 按类别分组
    by_category: dict[str, list[dict]] = {
        "domestic": [],
        "international": [],
        "research_report": [],
    }
    for c in configs:
        by_category.setdefault(c.category, []).append(c.model_dump())

    return {
        "success": True,
        "sources": [c.model_dump() for c in configs],
        "by_category": by_category,
        "total": len(configs),
    }


# ---------------------------------------------------------------------------
# GET /research/consensus/{symbol} — 共识评级
# ---------------------------------------------------------------------------

@router.get("/research/consensus/{symbol}")
async def get_consensus_rating(symbol: str):
    """获取指定股票的共识评级（汇总所有投行分析师评级）"""
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol 不能为空")

    from app.services.research_report_service import research_report_service

    try:
        consensus = await research_report_service.get_consensus_rating(symbol)
        return {"success": True, "data": consensus.model_dump()}
    except Exception as e:
        logger.error(f"共识评级获取失败 ({symbol}): {e}")
        raise HTTPException(status_code=500, detail=f"共识评级获取失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /research/ratings/{symbol} — 分析师评级列表
# ---------------------------------------------------------------------------

@router.get("/research/ratings/{symbol}")
async def get_analyst_ratings(
    symbol: str,
    source: Optional[str] = None,
):
    """获取指定股票的分析师评级列表，支持 source 参数筛选"""
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol 不能为空")

    from app.services.research_report_service import research_report_service

    source_ids = [source] if source else None

    try:
        result = await research_report_service.collect_research_reports(
            symbols=[symbol],
            source_ids=source_ids,
        )
        ratings = result.get("ratings", [])
        return {
            "success": True,
            "symbol": symbol,
            "ratings": [r.model_dump() for r in ratings],
            "total": len(ratings),
            "tier_status": result.get("tier_status", {}),
            "collection_time": result.get("collection_time", ""),
            "from_cache": result.get("from_cache", False),
        }
    except Exception as e:
        logger.error(f"分析师评级获取失败 ({symbol}): {e}")
        raise HTTPException(status_code=500, detail=f"分析师评级获取失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /datasource/config — 获取所有数据源配置状态
# ---------------------------------------------------------------------------

@router.get("/datasource/config", response_model=DataSourceConfigResponse)
async def get_datasource_config():
    """获取所有数据源的配置状态（启用/禁用、API Key 是否已配置）"""
    configs = _build_all_source_configs()
    return DataSourceConfigResponse(sources=configs)


# ---------------------------------------------------------------------------
# PUT /datasource/config — 保存数据源配置
# ---------------------------------------------------------------------------

@router.put("/datasource/config")
async def update_datasource_config(payload: DataSourceConfigResponse):
    """保存数据源配置（API Key、启用/禁用状态）。

    持久化到 user_settings，重启后保留。
    """
    from app.services.user_settings import load_user_settings, save_user_settings

    settings_data = load_user_settings()
    ds_config = settings_data.get("datasource_config", {})

    for src in payload.sources:
        ds_config[src.source_id] = {
            "enabled": src.enabled,
            "api_key": src.api_key,
            "last_tested": src.last_tested,
            "status": src.status.value if isinstance(src.status, DataSourceStatus) else src.status,
        }

    settings_data["datasource_config"] = ds_config
    save_user_settings(settings_data)

    return {"success": True, "message": "数据源配置已保存", "updated": len(payload.sources)}


# ---------------------------------------------------------------------------
# POST /analyze — 触发行情推演（SSE 流式返回）
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def trigger_stock_analysis(request: StockAnalysisRequest):
    """触发行情推演，以 SSE 流式返回各步骤输出。

    请求体：
    - topic: 推演主题（必填）
    - debate_rounds: 辩论轮数（1-5，默认2）
    - news_items: 可选关联资讯列表
    """
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="topic 不能为空")

    if request.debate_rounds < 1 or request.debate_rounds > 5:
        raise HTTPException(status_code=400, detail="debate_rounds 必须在 1-5 之间")

    from app.services.stock_analysis_service import stock_analysis_service

    async def event_generator():
        try:
            async for step in stock_analysis_service.analyze(request):
                yield f"data: {step.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"行情推演 SSE 异常: {e}")
            error_step = StockAnalysisStep(
                agent_name="error",
                step_content=f"推演过程出错: {str(e)}",
                status="error",
            )
            yield f"data: {error_step.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# GET /analyze/history — 获取历史推演记录列表
# ---------------------------------------------------------------------------

@router.get("/analyze/history")
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
):
    """获取历史推演记录列表，按时间倒序排列。

    - limit: 每页条数（1-100，默认20）
    - offset: 偏移量（默认0）
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit 必须在 1-100 之间")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset 不能为负数")

    from app.services.stock_analysis_service import stock_analysis_service

    try:
        records = await stock_analysis_service.get_history(limit=limit, offset=offset)
        return {
            "success": True,
            "items": [r.model_dump() for r in records],
            "total": len(records),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"查询推演历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询历史记录失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /analyze/{analysis_id} — 获取单条推演结果详情
# ---------------------------------------------------------------------------

@router.get("/analyze/{analysis_id}")
async def get_analysis_detail(analysis_id: str):
    """获取单条推演结果详情"""
    analysis_id = analysis_id.strip()
    if not analysis_id:
        raise HTTPException(status_code=400, detail="analysis_id 不能为空")

    from app.services.stock_analysis_service import stock_analysis_service

    try:
        result = await stock_analysis_service.get_by_id(analysis_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"推演结果不存在: {analysis_id}")
        return {
            "success": True,
            "data": result.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询推演结果失败 ({analysis_id}): {e}")
        raise HTTPException(status_code=500, detail=f"查询推演结果失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST /datasource/test/{source_id} — 测试数据源连通性
# ---------------------------------------------------------------------------

@router.post("/datasource/test/{source_id}")
async def test_datasource(source_id: str):
    """测试指定数据源的 API Key 连通性，返回成功/失败和延迟信息"""
    import time as _time

    source_id = source_id.strip().lower()
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id 不能为空")

    start = _time.time()
    success = False
    message = ""

    try:
        success, message = await _test_source_connectivity(source_id)
    except Exception as e:
        message = f"测试异常: {str(e)}"

    latency_ms = round((_time.time() - start) * 1000)

    return {
        "success": success,
        "source_id": source_id,
        "message": message,
        "latency_ms": latency_ms,
        "tested_at": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# 连通性测试实现
# ---------------------------------------------------------------------------

async def _test_source_connectivity(source_id: str) -> tuple[bool, str]:
    """对指定数据源执行轻量级连通性测试。

    Returns:
        (success: bool, message: str)
    """
    import httpx
    from app.config import Config

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/143.0.0.0",
    }

    # --- 国内数据源 ---
    if source_id == "akshare":
        try:
            import akshare as ak
            import asyncio
            df = await asyncio.to_thread(ak.stock_hot_rank_em)
            if df is not None and not df.empty:
                return True, f"AKShare 连通正常，获取到 {len(df)} 条热股数据"
            return False, "AKShare 返回空数据"
        except Exception as e:
            return False, f"AKShare 连通失败: {str(e)}"

    if source_id == "sina":
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://feed.mix.sina.com.cn/api/roll/get",
                    params={"pageid": "153", "lid": "2516", "num": "1", "page": "1"},
                    headers=headers,
                )
                resp.raise_for_status()
                return True, "新浪财经 API 连通正常"
        except Exception as e:
            return False, f"新浪财经连通失败: {str(e)}"

    if source_id == "10jqka":
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock",
                    params={"stock_type": "a", "type": "hour", "list_type": "normal"},
                    headers={**headers, "Referer": "https://www.10jqka.com.cn/"},
                )
                resp.raise_for_status()
                return True, "同花顺 API 连通正常"
        except Exception as e:
            return False, f"同花顺连通失败: {str(e)}"

    if source_id == "xueqiu":
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                await client.get("https://xueqiu.com/", headers=headers)
                return True, "雪球连通正常（Cookie 获取成功）"
        except Exception as e:
            return False, f"雪球连通失败: {str(e)}"

    if source_id == "tushare":
        token = Config.TUSHARE_TOKEN
        if not token:
            return False, "Tushare Token 未配置"
        try:
            import tushare as ts
            import asyncio
            pro = await asyncio.to_thread(ts.pro_api, token)
            return True, "Tushare Token 验证通过"
        except Exception as e:
            return False, f"Tushare 连通失败: {str(e)}"

    # --- 国际财经数据源 ---
    if source_id == "finnhub":
        api_key = Config.FINNHUB_API_KEY
        if not api_key:
            return False, "Finnhub API Key 未配置"
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://finnhub.io/api/v1/news",
                    params={"category": "general", "token": api_key},
                    headers=headers,
                )
                resp.raise_for_status()
                return True, "Finnhub API 连通正常"
        except Exception as e:
            return False, f"Finnhub 连通失败: {str(e)}"

    if source_id == "newsapi":
        api_key = Config.NEWSAPI_API_KEY
        if not api_key:
            return False, "NewsAPI API Key 未配置"
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://newsapi.org/v2/top-headlines",
                    params={"category": "business", "country": "us", "pageSize": "1", "apiKey": api_key},
                    headers=headers,
                )
                resp.raise_for_status()
                return True, "NewsAPI 连通正常"
        except Exception as e:
            return False, f"NewsAPI 连通失败: {str(e)}"

    if source_id == "alpha_vantage":
        api_key = Config.ALPHA_VANTAGE_API_KEY
        if not api_key:
            return False, "Alpha Vantage API Key 未配置"
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://www.alphavantage.co/query",
                    params={"function": "NEWS_SENTIMENT", "limit": "1", "apikey": api_key},
                    headers=headers,
                )
                resp.raise_for_status()
                return True, "Alpha Vantage API 连通正常"
        except Exception as e:
            return False, f"Alpha Vantage 连通失败: {str(e)}"

    if source_id == "gdelt":
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://api.gdeltproject.org/api/v2/doc/doc",
                    params={"query": "stock market", "mode": "artlist", "maxrecords": "1", "format": "json"},
                    headers=headers,
                )
                resp.raise_for_status()
                return True, "GDELT API 连通正常"
        except Exception as e:
            return False, f"GDELT 连通失败: {str(e)}"

    if source_id == "google_rss":
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://news.google.com/rss/search",
                    params={"q": "stock market", "hl": "en-US", "gl": "US", "ceid": "US:en"},
                    headers=headers,
                )
                resp.raise_for_status()
                return True, "Google News RSS 连通正常"
        except Exception as e:
            return False, f"Google News RSS 连通失败: {str(e)}"

    if source_id == "marketaux":
        api_key = Config.MARKETAUX_API_KEY
        if not api_key:
            return False, "Marketaux API Key 未配置"
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://api.marketaux.com/v1/news/all",
                    params={"api_token": api_key, "limit": "1"},
                    headers=headers,
                )
                resp.raise_for_status()
                return True, "Marketaux API 连通正常"
        except Exception as e:
            return False, f"Marketaux 连通失败: {str(e)}"

    # --- 投行研报数据源 ---
    if source_id == "finnhub_research":
        api_key = Config.FINNHUB_API_KEY
        if not api_key:
            return False, "Finnhub API Key 未配置（研报与国际新闻共用）"
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(
                    "https://finnhub.io/api/v1/stock/recommendation",
                    params={"symbol": "AAPL", "token": api_key},
                    headers=headers,
                )
                resp.raise_for_status()
                return True, "Finnhub Research API 连通正常"
        except Exception as e:
            return False, f"Finnhub Research 连通失败: {str(e)}"

    if source_id == "yahoo":
        try:
            import yfinance as yf
            import asyncio
            ticker = await asyncio.to_thread(yf.Ticker, "AAPL")
            info = await asyncio.to_thread(lambda: ticker.info)
            if info:
                return True, "Yahoo Finance 连通正常"
            return False, "Yahoo Finance 返回空数据"
        except Exception as e:
            return False, f"Yahoo Finance 连通失败: {str(e)}"

    if source_id == "benzinga":
        return False, "Benzinga 已移除（付费源）"

    if source_id == "seekingalpha":
        return False, "Seeking Alpha 已移除（付费源）"

    # Tier 4 sources — best-effort
    if source_id in ("tipranks", "marketbeat", "simplywallst", "last10k", "wisesheets"):
        return True, f"{source_id} 为 Tier 4 尽力而为数据源，无需 API Key"

    if source_id in ("finviz", "zacks"):
        return True, f"{source_id} 为免费数据源，无需 API Key"

    return False, f"未知数据源: {source_id}"
