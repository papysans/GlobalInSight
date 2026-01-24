from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from loguru import logger
from app.schemas import (
    NewsRequest, AgentState, ConfigResponse, ConfigUpdateRequest,
    OutputFileListResponse, OutputFileInfo, OutputFileContentResponse,
    WorkflowStatusResponse, LLMProviderConfig, CrawlerLimit,
    GenerateContrastRequest, GenerateContrastResponse,
    GenerateSentimentRequest, GenerateSentimentResponse, EmotionItem,
    GenerateKeywordsRequest, GenerateKeywordsResponse, KeywordItem,
    HotNewsCollectRequest,
    HotNewsInterpretRequest,
    HotNewsInterpretResponse,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
    XhsPublishRequest,
)
from app.services.workflow import app_graph
from app.services.workflow_status import workflow_status
from app.services.tophub_collector import tophub_collector
from app.services.hn_hot_collector import hn_hot_collector
from app.services.hot_news_scheduler import hot_news_scheduler
from app.services.hot_news_cache import hot_news_cache
from app.services.hotnews_alignment import cluster_items, clusters_to_api, make_raw_item
from app.services.hotnews_signals import apply_history_signals, make_history_snapshot
from app.services.hotnews_history import HotNewsHistoryConfig, HotNewsHistoryStore
from app.services.hotnews_interpreter import interpret_hot_topic
from app.config import settings
from app.services.user_settings import load_user_settings, update_user_settings
from pathlib import Path
from datetime import datetime
import asyncio
import copy

router = APIRouter()

# --- Hot News: SWR (stale-while-revalidate) background refresh ---
_HOTNEWS_REFRESH_TASKS: Dict[str, "asyncio.Task[None]"] = {}


def _cluster_platform_counts(clusters: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for c in clusters or []:
        pids = c.get("platform_ids") or []
        if isinstance(pids, list):
            for pid in pids:
                if not pid:
                    continue
                counts[str(pid)] = counts.get(str(pid), 0) + 1
    return counts


def _raw_platform_counts(raw_items: List[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for it in raw_items or []:
        pid = getattr(it, "platform_id", None) or (it.get("platform_id") if isinstance(it, dict) else None)
        if not pid:
            continue
        pid = str(pid)
        counts[pid] = counts.get(pid, 0) + 1
    return counts


async def _rebuild_aligned_clusters(*, include_hn: bool, force_refresh: bool) -> Dict[str, Any]:
    """Build aligned clusters from TopHub (+ optional HN) and persist into cache."""
    # Step 1: TopHub
    result = await tophub_collector.collect_news(force_refresh=force_refresh)
    news_list = result.get("news_list", []) or []
    collection_time = result.get("collection_time", datetime.now().isoformat())

    # Step 2: HN (optional)
    if include_hn:
        try:
            hn_result = await hn_hot_collector.collect_news(
                source_ids=["top", "best", "new"],
                max_items=30,
                force_refresh=force_refresh,
            )
            if hn_result.get("success"):
                hn_news = hn_result.get("news_list", []) or []
                for n in hn_news:
                    n["source"] = "Hacker News"
                    n.setdefault("timestamp", hn_result.get("collection_time", datetime.now().isoformat()))
                # Remove any pre-existing HN entries to avoid duplicates, then extend.
                news_list = [n for n in news_list if n.get("source") != "Hacker News"]
                news_list.extend(hn_news)
        except Exception as e:
            logger.warning(f"[hot-news] rebuild: HN fetch failed: {e}")

    # Step 3: cluster alignment (same logic as existing endpoint)
    short_to_id = {
        "微博": "weibo",
        "B站": "bilibili",
        "哔哩哔哩": "bilibili",
        "抖音": "douyin",
        "百度": "baidu",
        "贴吧": "tieba",
        "快手": "kuaishou",
        "知乎": "zhihu",
        "小红书": "xhs",
    }

    try:
        from app.services.tophub_collector import TOPHUB_SOURCES as _TOPHUB_SOURCES
    except Exception:
        _TOPHUB_SOURCES = {}

    raw_items: List[Any] = []
    for n in news_list:
        title = n.get("title") or ""
        url = n.get("url") or ""
        hot_value = n.get("hot_value") or ""
        source_id = str(n.get("source_id") or "")
        source_name = n.get("source") or n.get("source_name") or "Unknown"
        rank = n.get("rank") if isinstance(n.get("rank"), int) else None
        ts = n.get("timestamp") or collection_time

        if source_name == "Hacker News":
            platform_id = "hn"
        elif source_id in _TOPHUB_SOURCES:
            plat = _TOPHUB_SOURCES[source_id].get("platform") or "unknown"
            if plat == "all":
                plat_name = (n.get("platform") or "").strip()
                platform_id = short_to_id.get(plat_name, "all")
            else:
                platform_id = str(plat)
        else:
            platform_id = "unknown"

        raw_items.append(
            make_raw_item(
                platform_id=platform_id,
                source_id=source_id,
                source_name=source_name,
                title=title,
                url=url,
                hot_value=hot_value,
                rank=rank,
                ts=ts,
            )
        )

    # IMPORTANT:
    # Default max_clusters=200 will often drop low-hot-score platforms (e.g. HN / Tieba) entirely,
    # because items are sorted by hot_score and clustering stops creating new clusters after max_clusters.
    # Increase max_clusters to keep long-tail platforms in the aligned cache, then filter/slice for UI.
    clusters = cluster_items(raw_items, max_clusters=900)
    cluster_payload = clusters_to_api(clusters, collection_time=collection_time)

    # History snapshot for growth/delta/is_new
    repo_root = Path(__file__).resolve().parents[1]
    history_store = HotNewsHistoryStore(
        HotNewsHistoryConfig(history_path=repo_root / "outputs" / "hotnews_history.jsonl")
    )
    prev = history_store.load_recent_snapshots(limit=1)
    prev_snapshot = prev[0] if prev else None
    cluster_payload = apply_history_signals(cluster_payload, prev_snapshot=prev_snapshot)
    if not prev_snapshot or prev_snapshot.get("ts") != collection_time:
        history_store.append_snapshot(make_history_snapshot(ts=collection_time, clusters=cluster_payload))

    # Persist
    cache_key = "aligned_with_hn_v2" if include_hn else "aligned_no_hn_v2"
    source_sig = f"t:{collection_time}" + (f"|hn:{datetime.now().strftime('%Y-%m-%d')}" if include_hn else "")
    raw_counts = _raw_platform_counts(raw_items)
    cluster_counts = _cluster_platform_counts(cluster_payload)
    logger.info(
        f"[hot-news] rebuild stats: include_hn={include_hn} raw_counts(hn/tieba)={raw_counts.get('hn',0)}/{raw_counts.get('tieba',0)} "
        f"cluster_counts(hn/tieba)={cluster_counts.get('hn',0)}/{cluster_counts.get('tieba',0)} total_clusters={len(cluster_payload)}"
    )

    hot_news_cache.save_to_cache(
        {"collection_time": collection_time, "source_sig": source_sig, "clusters": cluster_payload},
        cache_key=cache_key,
    )
    return {
        "result": result,
        "collection_time": collection_time,
        "clusters": cluster_payload,
        "cache_key": cache_key,
        "raw_platform_counts": raw_counts,
        "platform_cluster_counts": cluster_counts,
    }


def _ensure_background_refresh(*, include_hn: bool) -> None:
    """Fire-and-forget refresh (dedup by cache_key)."""
    cache_key = "aligned_with_hn_v2" if include_hn else "aligned_no_hn_v2"
    task = _HOTNEWS_REFRESH_TASKS.get(cache_key)
    if task and not task.done():
        return

    async def _runner():
        try:
            logger.info(f"[hot-news] background refresh start: {cache_key}")
            await _rebuild_aligned_clusters(include_hn=include_hn, force_refresh=True)
            logger.info(f"[hot-news] background refresh done: {cache_key}")
        except Exception as e:
            logger.exception(f"[hot-news] background refresh failed: {cache_key}: {e}")
        finally:
            _HOTNEWS_REFRESH_TASKS.pop(cache_key, None)

    _HOTNEWS_REFRESH_TASKS[cache_key] = asyncio.create_task(_runner())

@router.post("/analyze")
async def analyze_news(request: NewsRequest):
    """执行完整的工作流分析（支持平台选择和辩论轮数）"""
    # 验证 debate_rounds 参数
    debate_rounds = request.debate_rounds or 2
    if debate_rounds < 1 or debate_rounds > 5:
        raise HTTPException(status_code=400, detail="debate_rounds 必须在 1-5 之间")
    
    print(f"[IN] Received request: Topic='{request.topic}', URLs={request.urls}, Platforms={request.platforms}, DebateRounds={debate_rounds}")
    
    # 更新工作流状态
    await workflow_status.start_workflow(request.topic)
    
    async def event_generator():
        # Initial input for the graph
        initial_state = {
            "urls": request.urls, 
            "topic": request.topic, 
            "platforms": request.platforms or [],  # 支持根据勾选框选择平台
            "debate_rounds": debate_rounds,  # 传递辩论轮数
            "messages": [],
            "crawler_data": [],
            "platform_data": {}
        }
        
        # Stream the graph execution
        # LangGraph stream yields (node_name, state_update)
        try:
            async for event in app_graph.astream(initial_state):
                for node_name, state_update in event.items():
                    # 更新工作流状态
                    await workflow_status.update_step(node_name)
                    
                    # Construct AgentState
                    # In a real app, we might extract more specific content from state_update
                    # Here we just take the last message added
                    messages = state_update.get("messages", [])
                    content = str(messages[-1]) if messages else "Processing..."
                    
                    # 规范化节点名称
                    node_name_map = {
                        "crawler_agent": "Crawler",
                        "reporter": "Reporter",
                        "analyst": "Analyst",
                        "debater": "Debater",
                        "writer": "Writer",
                        "image_generator": "Image Generator"
                    }
                    display_name = node_name_map.get(node_name, node_name.capitalize())
                    
                    print(f"[SSE] 发送事件: {display_name}, 内容长度: {len(content)}")
                    
                    agent_state = AgentState(
                        agent_name=display_name,
                        step_content=content,
                        status="thinking",
                        image_urls=state_update.get("image_urls")
                    )
                    
                    # Yield SSE format
                    yield f"data: {agent_state.model_dump_json()}\n\n"
            
            # 完成工作流
            await workflow_status.finish_workflow()
            
            # Final event
            final_state = AgentState(
                agent_name="System",
                step_content="Analysis Complete",
                status="finished"
            )
            yield f"data: {final_state.model_dump_json()}\n\n"
            
        except Exception as e:
            # 重置工作流状态
            await workflow_status.reset()
            
            error_state = AgentState(
                agent_name="System",
                step_content=f"Error: {str(e)}",
                status="error"
            )
            yield f"data: {error_state.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """获取当前配置"""
    # 转换 LLM 配置格式
    llm_providers = {
        "reporter": [LLMProviderConfig(**item) for item in settings.AGENT_CONFIG["reporter"]],
        "analyst": [LLMProviderConfig(**item) for item in settings.AGENT_CONFIG["analyst"]],
        "debater": [LLMProviderConfig(**item) for item in settings.AGENT_CONFIG["debater"]],
        "writer": [LLMProviderConfig(**item) for item in settings.AGENT_CONFIG["writer"]],
    }
    
    # 转换爬虫限制格式
    crawler_limits = {
        platform: CrawlerLimit(**limits)
        for platform, limits in settings.CRAWLER_LIMITS.items()
    }
    
    # 转换热榜配置格式
    from app.schemas import HotNewsConfig
    hot_news_config = HotNewsConfig(**settings.HOT_NEWS_CONFIG)
    
    return ConfigResponse(
        llm_providers=llm_providers,
        crawler_limits=crawler_limits,
        debate_max_rounds=settings.DEBATE_MAX_ROUNDS,
        default_platforms=settings.DEFAULT_PLATFORMS,
        hot_news_config=hot_news_config
    )


@router.put("/config")
async def update_config(request: ConfigUpdateRequest):
    """更新配置（部分更新）"""
    updated_fields = []
    
    if request.debate_max_rounds is not None:
        if request.debate_max_rounds < 1:
            raise HTTPException(status_code=400, detail="debate_max_rounds 必须大于0")
        settings.DEBATE_MAX_ROUNDS = request.debate_max_rounds
        updated_fields.append("debate_max_rounds")
    
    if request.crawler_limits is not None:
        for platform, limits in request.crawler_limits.items():
            if platform in settings.CRAWLER_LIMITS:
                settings.CRAWLER_LIMITS[platform].update(limits.dict())
                updated_fields.append(f"crawler_limits.{platform}")
    
    if request.default_platforms is not None:
        # 验证平台是否有效
        valid_platforms = ["wb", "dy", "ks", "bili", "tieba", "zhihu", "xhs", "hn", "reddit"]
        invalid = [p for p in request.default_platforms if p not in valid_platforms]
        if invalid:
            raise HTTPException(status_code=400, detail=f"无效的平台: {invalid}")
        settings.DEFAULT_PLATFORMS = request.default_platforms
        updated_fields.append("default_platforms")
    
    if request.hot_news_config is not None:
        # 更新热榜配置
        settings.HOT_NEWS_CONFIG = request.hot_news_config.dict()
        updated_fields.append("hot_news_config")
    
    if not updated_fields:
        raise HTTPException(status_code=400, detail="没有提供要更新的字段")
    
    return {
        "success": True,
        "message": f"配置已更新: {', '.join(updated_fields)}",
        "updated_fields": updated_fields
    }


@router.get("/user-settings", response_model=UserSettingsResponse)
async def get_user_settings():
    """获取前端可写入的用户设置（存储在 cache/user_settings.json）"""
    data = load_user_settings()
    # Normalize shape for response model
    return UserSettingsResponse(
        llm_apis=data.get("llm_apis") or [],
        volcengine=data.get("volcengine"),
        agent_llm_overrides=data.get("agent_llm_overrides") or {},
    )


@router.put("/user-settings", response_model=UserSettingsResponse)
async def put_user_settings(request: UserSettingsUpdateRequest):
    """更新前端可写入的用户设置（部分更新）"""
    merged = update_user_settings(
        llm_apis=[x.model_dump() for x in request.llm_apis] if request.llm_apis is not None else None,
        volcengine=request.volcengine.model_dump() if request.volcengine is not None else None,
        agent_llm_overrides=request.agent_llm_overrides if request.agent_llm_overrides is not None else None,
    )
    return UserSettingsResponse(
        llm_apis=merged.get("llm_apis") or [],
        volcengine=merged.get("volcengine"),
        agent_llm_overrides=merged.get("agent_llm_overrides") or {},
    )


@router.get("/outputs", response_model=OutputFileListResponse)
async def get_output_files(limit: int = 20, offset: int = 0):
    """获取历史输出文件列表"""
    output_dir = Path("outputs")
    if not output_dir.exists():
        return OutputFileListResponse(files=[], total=0)
    
    # 获取所有 .md 文件
    md_files = list(output_dir.glob("*.md"))
    
    # 排除 TECH_DOC.md
    md_files = [f for f in md_files if f.name != "TECH_DOC.md"]
    
    # 按修改时间排序（最新的在前）
    md_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    # 分页
    total = len(md_files)
    paginated_files = md_files[offset:offset + limit]
    
    # 构建文件信息
    file_infos = []
    for file_path in paginated_files:
        stat = file_path.stat()
        # 从文件名提取主题和时间
        # 格式: YYYY-MM-DD_HH-MM-SS_主题.md
        parts = file_path.stem.split("_", 2)
        if len(parts) >= 3:
            topic = parts[2]
        else:
            topic = file_path.stem
        
        file_infos.append(OutputFileInfo(
            filename=file_path.name,
            topic=topic,
            created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            size=stat.st_size
        ))
    
    return OutputFileListResponse(files=file_infos, total=total)


@router.get("/outputs/{filename}", response_model=OutputFileContentResponse)
async def get_output_file(filename: str):
    """获取指定输出文件的内容"""
    # 安全检查：防止路径遍历攻击
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    file_path = Path("outputs") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="不是有效的文件")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        return OutputFileContentResponse(
            filename=filename,
            content=content,
            created_at=created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@router.get("/hotnews")
async def get_hot_news(limit: int = 10, source: str = "hot", force_refresh: bool = False):
    """获取 TopHub 热榜数据（默认全榜）。

    - limit: 返回条数上限（1-100）
    - source: "hot"=TopHub 全榜；"all"=所有支持榜单；其他值=对应 source_id
    - force_refresh: True 时跳过缓存，立即抓取
    """
    limit = max(1, min(100, int(limit)))
    source_key = (source or "hot").strip().lower()

    if source_key == "all":
        source_ids = None  # 全部来源
    elif source_key:
        source_ids = [source_key]
    else:
        source_ids = ["hot"]

    try:
        result = await tophub_collector.collect_news(
            source_ids=source_ids,
            force_refresh=force_refresh,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"热榜抓取失败: {str(e)}")

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "未知错误"))

    news_list = result.get("news_list", []) or []

    items = []
    seen = set()
    for item in news_list:
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        if not title:
            continue
        dedupe_key = (title.lower(), url.lower())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        items.append({
            "title": title,
            "url": url,
            "rank": item.get("rank"),
            "hot_value": item.get("hot_value"),
            "source": item.get("source"),
            "source_id": item.get("source_id"),
            "platform": item.get("platform"),
        })
        if len(items) >= limit:
            break

    return {
        "success": True,
        "items": items,
        "total": len(items),
        "source": source_key or "hot",
        "from_cache": result.get("from_cache", False),
        "collection_time": result.get("collection_time"),
    }


@router.get("/hotnews/hn")
async def get_hn_news(limit: int = 30, story_type: str = "top", force_refresh: bool = False):
    """获取 Hacker News 热榜数据。

    - limit: 返回条数上限（1-100），支持前30/50条
    - story_type: "top"=最热；"best"=最佳；"new"=最新
    - force_refresh: True 时跳过缓存，立即抓取
    """
    limit = max(1, min(100, int(limit)))
    story_type = (story_type or "top").strip().lower()
    
    if story_type not in ["top", "best", "new"]:
        story_type = "top"

    try:
        result = await hn_hot_collector.collect_news(
            source_ids=[story_type],
            max_items=limit,
            force_refresh=force_refresh,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HN 热榜抓取失败: {str(e)}")

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "未知错误"))

    news_list = result.get("news_list", []) or []

    items = []
    for item in news_list:
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        if not title or not url:
            continue
        items.append({
            "title": title,
            "url": url,
            "rank": item.get("rank"),
            "hot_value": item.get("hot_value"),
            "source": item.get("source"),
            "source_id": item.get("source_id"),
            "score": item.get("score"),
            "descendants": item.get("descendants"),
            "author": item.get("author"),
            "posted_time": item.get("posted_time"),
        })
        if len(items) >= limit:
            break

    return {
        "success": True,
        "items": items,
        "total": len(items),
        "story_type": story_type,
        "source": "hackernews",
        "from_cache": result.get("from_cache", False),
        "collection_time": result.get("collection_time"),
    }


@router.get("/workflow/status", response_model=WorkflowStatusResponse)
async def get_workflow_status():
    """获取当前工作流状态"""
    status = await workflow_status.get_status()
    return WorkflowStatusResponse(**status)


# --- 数据生成接口 ---

@router.post("/generate-data/contrast", response_model=GenerateContrastResponse)
async def generate_contrast_data(request: GenerateContrastRequest):
    """生成舆论对比数据"""
    from app.llm import get_agent_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    
    llm = get_agent_llm("analyst")
    
    prompt = f"""基于以下议题和洞察，生成"中外舆论温差"数据。

议题: {request.topic}
洞察: {request.insight}

请生成两组数据：
1. 国内舆论分布：[支持%, 中立%, 反对%] - 三个数值之和应为100
2. 国际舆论分布：[支持%, 中立%, 反对%] - 三个数值之和应为100

请以JSON格式输出，格式如下：
{{
  "domestic": [支持%, 中立%, 反对%],
  "intl": [支持%, 中立%, 反对%]
}}

只输出JSON，不要其他文字。"""
    
    messages = [
        SystemMessage(content="你是一个数据分析专家，能够基于议题和洞察生成合理的舆论分布数据。"),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = str(response.content).strip()
        
        # 保存LLM原始响应的前300字符作为推理过程展示
        llm_reasoning = content[:300] if len(content) > 300 else content
        if len(content) > 300:
            llm_reasoning += "..."
        
        # 尝试解析JSON
        import json
        import re
        
        # 提取JSON部分
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            domestic = data.get("domestic", [65, 20, 15])
            intl = data.get("intl", [30, 40, 30])
        else:
            # 如果解析失败，使用默认值
            domestic = [65, 20, 15]
            intl = [30, 40, 30]
        
        # 确保数值在合理范围内
        domestic = [max(0, min(100, int(x))) for x in domestic[:3]]
        intl = [max(0, min(100, int(x))) for x in intl[:3]]
        
        # 归一化确保总和为100
        if sum(domestic) != 100:
            total = sum(domestic)
            domestic = [int(x * 100 / total) for x in domestic]
            domestic[0] = 100 - sum(domestic[1:])
        
        if sum(intl) != 100:
            total = sum(intl)
            intl = [int(x * 100 / total) for x in intl]
            intl[0] = 100 - sum(intl[1:])
        
        return GenerateContrastResponse(
            domestic=domestic,
            intl=intl,
            agent_name="analyst",
            used_llm=True,
            cache_hit=False,
            llm_reasoning=llm_reasoning
        )
    except Exception as e:
        # 如果出错，返回默认数据
        return GenerateContrastResponse(
            domestic=[65, 20, 15],
            intl=[30, 40, 30],
            agent_name="analyst",
            used_llm=False,
            cache_hit=False
        )


@router.post("/generate-data/sentiment", response_model=GenerateSentimentResponse)
async def generate_sentiment_data(request: GenerateSentimentRequest):
    """生成情感光谱数据"""
    from app.llm import get_agent_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    
    llm = get_agent_llm("analyst")
    
    prompt = f"""基于以下议题和洞察，生成"网民情感光谱"数据。

议题: {request.topic}
洞察: {request.insight}

请生成4-6种主要情感及其占比，常见情感包括：愤怒、嘲讽、失望、中立、支持、质疑等。

请以JSON格式输出，格式如下：
{{
  "emotions": [
    {{"name": "情感名称", "value": 百分比数值}},
    ...
  ]
}}

所有value之和应接近100。只输出JSON，不要其他文字。"""
    
    messages = [
        SystemMessage(content="你是一个情感分析专家，能够基于议题和洞察生成合理的情感分布数据。"),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = str(response.content).strip()
        
        import json
        import re
        
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            emotions = data.get("emotions", [])
        else:
            emotions = [
                {"name": "愤怒", "value": 55},
                {"name": "嘲讽", "value": 25},
                {"name": "失望", "value": 12},
                {"name": "中立", "value": 8}
            ]
        
        # 确保格式正确
        emotion_items = []
        for item in emotions[:6]:  # 最多6个
            if isinstance(item, dict):
                name = item.get("name", "未知")
                value = max(0, min(100, int(item.get("value", 0))))
                emotion_items.append(EmotionItem(name=name, value=value))
        
        # 如果为空，使用默认值
        if not emotion_items:
            emotion_items = [
                EmotionItem(name="愤怒", value=55),
                EmotionItem(name="嘲讽", value=25),
                EmotionItem(name="失望", value=12),
                EmotionItem(name="中立", value=8)
            ]
        
        return GenerateSentimentResponse(
            emotions=emotion_items,
            agent_name="analyst",
            used_llm=True,
            cache_hit=False
        )
    except Exception as e:
        return GenerateSentimentResponse(
            emotions=[
                EmotionItem(name="愤怒", value=55),
                EmotionItem(name="嘲讽", value=25),
                EmotionItem(name="失望", value=12),
                EmotionItem(name="中立", value=8)
            ],
            agent_name="analyst",
            used_llm=False,
            cache_hit=False,
            llm_reasoning=None
        )


@router.post("/generate-data/keywords", response_model=GenerateKeywordsResponse)
async def generate_keywords_data(request: GenerateKeywordsRequest):
    """生成关键词数据"""
    from app.llm import get_agent_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    from collections import Counter
    import re
    
    llm = get_agent_llm("analyst")
    
    # 如果有爬取数据，提取关键词
    text_content = request.topic
    if request.crawler_data:
        texts = []
        for item in request.crawler_data[:20]:  # 最多使用20条
            title = item.get("title", "")
            content = item.get("content", "")
            texts.append(f"{title} {content}")
        text_content = " ".join(texts)
    
    prompt = f"""基于以下议题和内容，生成高频关键词数据。

议题: {request.topic}
内容摘要: {text_content[:1000]}...

请生成5-8个高频关键词及其频率（相对频率，数值范围100-2000）。

请以JSON格式输出，格式如下：
{{
  "keywords": [
    {{"word": "关键词", "frequency": 频率数值}},
    ...
  ]
}}

只输出JSON，不要其他文字。"""
    
    messages = [
        SystemMessage(content="你是一个文本分析专家，能够提取高频关键词并估算其频率。"),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = str(response.content).strip()
        
        import json
        
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            keywords = data.get("keywords", [])
        else:
            keywords = []
        
        # 确保格式正确
        keyword_items = []
        for item in keywords[:8]:  # 最多8个
            if isinstance(item, dict):
                word = item.get("word", "")
                frequency = max(100, min(2000, int(item.get("frequency", 500))))
                if word:
                    keyword_items.append(KeywordItem(word=word, frequency=frequency))
        
        # 如果为空，使用默认值
        if not keyword_items:
            keyword_items = [
                KeywordItem(word="真相", frequency=1200),
                KeywordItem(word="反转", frequency=950),
                KeywordItem(word="烂尾", frequency=800),
                KeywordItem(word="公信力", frequency=600),
                KeywordItem(word="甚至", frequency=500)
            ]
        
        return GenerateKeywordsResponse(
            keywords=keyword_items,
            agent_name="analyst",
            used_llm=True,
            cache_hit=False
        )
    except Exception as e:
        return GenerateKeywordsResponse(
            keywords=[
                KeywordItem(word="真相", frequency=1200),
                KeywordItem(word="反转", frequency=950),
                KeywordItem(word="烂尾", frequency=800),
                KeywordItem(word="公信力", frequency=600),
                KeywordItem(word="甚至", frequency=500)
            ],
            agent_name="analyst",
            used_llm=False,
            cache_hit=False,
            llm_reasoning=None
        )


# --- 热点新闻接口 ---

@router.post("/hot-news/collect")
async def collect_hot_news(request: HotNewsCollectRequest):
    """
    手动触发热点新闻收集
    
    Args:
        request.platforms: 指定要过滤的平台列表 (如 ['weibo', 'bilibili']) 或 ['all']，None表示不过滤（返回所有）
        request.force_refresh: 是否强制刷新（忽略缓存）
    """
    try:
        logger.info("=" * 80)
        logger.info(f"🎯 收到热榜请求: platforms={request.platforms}, force_refresh={request.force_refresh}")

        # --- SWR: prefer cached aligned clusters, refresh in background when needed ---
        include_hn = bool(request.platforms and ("hn" in request.platforms or "all" in request.platforms))
        cache_key = "aligned_with_hn_v2" if include_hn else "aligned_no_hn_v2"

        if not request.force_refresh:
            cached = hot_news_cache.get_cached_data(cache_key=cache_key)
            cached_clusters = (cached or {}).get("clusters")
            if isinstance(cached_clusters, list) and cached_clusters:
                refreshing = hot_news_cache.is_cache_expired(cache_key=cache_key)
                if refreshing:
                    _ensure_background_refresh(include_hn=include_hn)

                requested_set = set([p for p in (request.platforms or []) if p])
                if not requested_set or "all" in requested_set:
                    filtered_clusters = cached_clusters
                else:
                    def _cluster_has_platform(c: dict) -> bool:
                        pids = c.get("platform_ids") or []
                        if isinstance(pids, list) and any(pid in requested_set for pid in pids):
                            return True
                        for ev in c.get("evidence") or []:
                            if ev.get("platform_id") in requested_set:
                                return True
                        return False
                    filtered_clusters = [c for c in cached_clusters if _cluster_has_platform(c)]

                return {
                    "success": True,
                    "total_news": len(filtered_clusters),
                    "successful_sources": 0,
                    "total_sources": 0,
                    # NOTE: if we only return top-200 clusters for 'all', low-hot-score platforms like HN/Tieba
                    # may never appear, causing frontend local filtering to show empty. Return more here.
                    "news_list": filtered_clusters[:600],
                    "news_by_platform": {},
                    "collection_time": (cached or {}).get("collection_time"),
                    "from_cache": True,
                    "refreshing": bool(refreshing),
                    "platform_cluster_counts": _cluster_platform_counts(cached_clusters),
                    "debug": {
                        "cache_key": cache_key,
                        "requested_platforms": list(requested_set) if requested_set else ["all"],
                        "clusters_in_cache": len(cached_clusters),
                    },
                }

        # If force_refresh OR no cache available: rebuild synchronously.
        rebuilt = await _rebuild_aligned_clusters(include_hn=include_hn, force_refresh=True)
        cluster_payload = rebuilt["clusters"]
        collection_time = rebuilt["collection_time"]

        requested_set = set([p for p in (request.platforms or []) if p])
        if not requested_set or "all" in requested_set:
            filtered_clusters = cluster_payload
        else:
            def _cluster_has_platform(c: dict) -> bool:
                pids = c.get("platform_ids") or []
                if isinstance(pids, list) and any(pid in requested_set for pid in pids):
                    return True
                for ev in c.get("evidence") or []:
                    if ev.get("platform_id") in requested_set:
                        return True
                return False
            filtered_clusters = [c for c in cluster_payload if _cluster_has_platform(c)]

        return {
            "success": True,
            "total_news": len(filtered_clusters),
            "successful_sources": (rebuilt.get("result") or {}).get("successful_sources", 0),
            "total_sources": (rebuilt.get("result") or {}).get("total_sources", 0),
            # Same rationale as cached path: keep enough clusters so local platform filter can find long-tail platforms.
            "news_list": filtered_clusters[:600],
            "news_by_platform": {},
            "collection_time": collection_time,
            "from_cache": False,
            "refreshing": False,
            "platform_cluster_counts": rebuilt.get("platform_cluster_counts") or _cluster_platform_counts(cluster_payload),
            "raw_platform_counts": rebuilt.get("raw_platform_counts"),
            "debug": {
                "cache_key": rebuilt.get("cache_key"),
                "include_hn": include_hn,
                "requested_platforms": list(requested_set) if requested_set else ["all"],
                "clusters_total": len(cluster_payload),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"收集热点新闻失败: {str(e)}")


@router.get("/hot-news/status")
async def get_hot_news_status():
    """获取热点新闻收集任务状态"""
    status = hot_news_scheduler.get_status()
    return status


@router.post("/hot-news/interpret", response_model=HotNewsInterpretResponse)
async def interpret_hot_news_topic(request: HotNewsInterpretRequest):
    """用户点开单条热点时，生成“热点演化解读卡”（只调用这一条的 LLM）。"""
    try:
        result = await interpret_hot_topic(request.model_dump())
        return HotNewsInterpretResponse(**result)
    except Exception as e:
        # Never hard-fail the UI; return heuristic fallback structure.
        return HotNewsInterpretResponse(
            success=False,
            id=request.id,
            title=request.title,
            lifecycle_stage="盘整期",
            diffusion_summary=f"解读生成失败：{str(e)}",
            divergence_points=[],
            watch_points=[],
            confidence=0.2,
            used_llm=False,
        )


@router.post("/hot-news/run-once")
async def run_hot_news_once():
    """立即执行一次热点新闻收集（用于测试）"""
    try:
        await hot_news_scheduler.run_once()
        status = hot_news_scheduler.get_status()
        return {
            "success": True,
            "message": "热点新闻收集任务已执行",
            "last_result": status.get('last_result')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/hot-news/cache-info")
async def get_cache_info():
    """获取缓存信息"""
    from app.services.hot_news_cache import hot_news_cache
    cache_info = hot_news_cache.get_cache_info()
    return cache_info


@router.post("/hot-news/clear-cache")
async def clear_cache():
    """清除热点新闻缓存"""
    try:
        from app.services.hot_news_cache import hot_news_cache
        hot_news_cache.clear_cache()
        return {
            "success": True,
            "message": "缓存已清除"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.get("/hot-news/platforms")
async def get_supported_platforms():
    """获取支持的平台列表"""
    from app.services.tophub_collector import TOPHUB_SOURCES, PENDING_PLATFORMS
    
    platforms = []
    for source_id, info in TOPHUB_SOURCES.items():
        platforms.append({
            "source_id": source_id,
            "name": info['name'],
            "category": info['category'],
            "platform": info['platform'],
            "priority": info['priority'],
            "supported": True
        })
    
    # 添加待支持平台
    for platform_id, name in PENDING_PLATFORMS.items():
        platforms.append({
            "platform": platform_id,
            "name": name,
            "supported": False
        })

    # 添加 HN 平台
    platforms.append({
        "source_id": "hn",
        "name": "Hacker News",
        "category": "tech",
        "platform": "Hacker News",
        "priority": 5,
        "supported": True,
        "description": "全球最大的科技新闻聚合社区"
    })

    # 按优先级排序
    platforms.sort(key=lambda x: x.get('priority', 999))

    return {
        "platforms": platforms,
        "total_supported": len(TOPHUB_SOURCES) + 1,
        "total_pending": len(PENDING_PLATFORMS)
    }


# --- 小红书 MCP 发布接口 ---

@router.get("/xhs/status")
async def get_xhs_status():
    """检查小红书 MCP 服务状态和登录状态"""
    from app.services.xiaohongshu_publisher import xiaohongshu_publisher
    from app.schemas import XhsStatusResponse
    
    status = await xiaohongshu_publisher.get_status()
    return XhsStatusResponse(
        mcp_available=status.get("mcp_available", False),
        login_status=status.get("login_status", False),
        message=status.get("message", "")
    )


@router.post("/xhs/publish")
async def publish_to_xhs(request: XhsPublishRequest):
    """手动发布内容到小红书
    
    请求体：
    - title: 标题
    - content: 正文内容
    - images: 图片列表（本地路径或 HTTP URL）
    """
    from app.services.xiaohongshu_publisher import xiaohongshu_publisher
    from app.schemas import XhsPublishRequest, XhsPublishResponse
    
    if not request.title or not request.content:
        return XhsPublishResponse(
            success=False,
            message="标题和内容不能为空"
        )
    
    if not request.images:
        return XhsPublishResponse(
            success=False,
            message="至少需要一张图片"
        )
    
    result = await xiaohongshu_publisher.publish_content(
        title=request.title,
        content=request.content,
        images=request.images
    )
    
    return XhsPublishResponse(
        success=result.get("success", False),
        message=result.get("message") or result.get("error", "发布失败"),
        data=result.get("data")
    )


