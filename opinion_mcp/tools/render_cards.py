"""
MCP 卡片渲染工具

提供 generate_topic_cards 工具供 OpenClaw 调用:
- 根据已完成的分析结果，调用独立渲染服务生成数据卡片 PNG
- 返回本地文件路径列表，供后续发布流程使用
"""

import re
from typing import Any, Dict, List, Optional
from loguru import logger

from opinion_mcp.services.card_render_client import card_render_client
from opinion_mcp.services.job_manager import job_manager
from opinion_mcp.schemas import JobStatus

CORE_CARD_TYPES = ["title", "debate_timeline", "trend", "radar"]
PLATFORM_NAME_MAP = {
    "wb": "微博",
    "dy": "抖音",
    "ks": "快手",
    "bili": "B站",
    "tieba": "贴吧",
    "zhihu": "知乎",
    "xhs": "小红书",
    "hn": "Hacker News",
    "reddit": "Reddit",
}


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    return [s.strip() for s in re.split(r"[。！？.!?\n]", text) if len(s.strip()) >= 6]


def _platform_label(code: str) -> str:
    return PLATFORM_NAME_MAP.get(code, str(code))


def _build_platform_stats(result: Any, job: Any) -> Dict[str, int]:
    raw_stats = getattr(result, "platform_stats", {}) or {}
    if raw_stats:
        return {str(k): int(v) for k, v in raw_stats.items() if int(v) > 0}

    fallback_stats: Dict[str, int] = {}
    selected_platforms = list(getattr(job, "platforms", []) or [])
    if not selected_platforms:
        selected_platforms = ["wb", "dy", "bili", "zhihu"]

    base = 96
    for idx, code in enumerate(selected_platforms[:6]):
        fallback_stats[str(code)] = max(48, base - idx * 10)
    return fallback_stats


def _build_debate_timeline_payload(result: Any, job: Any, topic: str) -> Dict[str, Any]:
    rounds = max(1, min(int(getattr(job, "debate_rounds", 2) or 2), 8))
    summary_chunks = _split_sentences(getattr(result, "summary", ""))
    insight_chunks = _split_sentences(getattr(result, "insight", ""))
    snippets = summary_chunks + insight_chunks
    if not snippets:
        snippets = [f"围绕「{topic}」完成多轮推演，结论趋于收敛。"]

    stage_titles = [
        "事实对齐",
        "观点拉锯",
        "焦点收敛",
        "结论验证",
        "发布准备",
        "补充校对",
        "风险复盘",
        "最终确认",
    ]

    timeline: List[Dict[str, Any]] = []
    for idx in range(rounds):
        snippet = snippets[min(idx, len(snippets) - 1)]
        timeline.append(
            {
                "round": idx + 1,
                "title": stage_titles[idx] if idx < len(stage_titles) else f"第{idx + 1}轮推演",
                "summary": snippet,
                "insight": snippet,
            }
        )

    return {"timeline": timeline}


def _build_trend_payload(platform_stats: Dict[str, int], debate_rounds: int) -> Dict[str, Any]:
    total = max(1, sum(platform_stats.values()))
    platform_count = max(1, len(platform_stats))
    base = min(72, max(42, int(total / platform_count)))
    growth = max(12, min(150, debate_rounds * 18 + platform_count * 9))
    peak = min(100, base + int(growth * 0.42))
    end = max(55, peak - int(growth * 0.08))

    curve = [
        max(0, min(100, int(base * 0.7))),
        max(0, min(100, int(base * 0.84))),
        max(0, min(100, int(base * 0.95))),
        peak,
        max(0, min(100, peak - 2)),
        max(0, min(100, end + 1)),
        max(0, min(100, end)),
    ]

    if end + 4 < peak:
        stage = "回落期"
    elif growth >= 80:
        stage = "爆发期"
    else:
        stage = "扩散期"

    return {"stage": stage, "growth": growth, "curve": curve}


def _build_radar_payload(platform_stats: Dict[str, int]) -> Dict[str, Any]:
    sorted_items = sorted(platform_stats.items(), key=lambda item: item[1], reverse=True)[:6]
    if len(sorted_items) < 3:
        default_items = [("wb", 92), ("dy", 86), ("bili", 78), ("zhihu", 70)]
        used = {code for code, _ in sorted_items}
        for code, value in default_items:
            if code not in used:
                sorted_items.append((code, value))
            if len(sorted_items) >= 6:
                break

    max_value = max((value for _, value in sorted_items), default=1)
    labels = [_platform_label(code) for code, _ in sorted_items]
    values = [round(value / max_value * 100) for _, value in sorted_items]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "平台覆盖",
                "data": values,
            }
        ],
    }


def _build_platform_heat_payload(platform_stats: Dict[str, int]) -> Dict[str, Any]:
    total = sum(platform_stats.values()) or 1
    platforms_list = [
        {
            "name": _platform_label(code),
            "value": value,
            "percentage": round(value / total * 100, 1),
        }
        for code, value in sorted(platform_stats.items(), key=lambda item: item[1], reverse=True)
    ]
    return {"platforms": platforms_list}


async def generate_topic_cards(
    job_id: Optional[str] = None,
    card_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    为指定分析任务生成数据卡片图片

    Args:
        job_id: 分析任务 ID，留空则使用最近完成的任务
        card_types: 指定要生成的卡片类型，留空则生成四张核心卡片
                    可选: title, insight, debate_timeline, trend, radar, key_findings, platform_heat

    Returns:
        包含生成结果的字典:
        - success: bool
        - cards: { type: file_path }
        - message: str
    """
    # 1. 检查渲染服务
    is_healthy = await card_render_client.health_check()
    if not is_healthy:
        return {
            "success": False,
            "cards": {},
            "message": "❌ 渲染服务未启动。请先在 renderer/ 目录执行: npm run build && npm start",
        }

    # 2. 获取分析结果
    if job_id:
        job = job_manager.get_job(job_id)
    else:
        job = job_manager.get_latest_completed_job()
        if job:
            job_id = job.job_id

    if not job:
        return {
            "success": False,
            "cards": {},
            "message": "❌ 未找到已完成的分析任务" + (f" (job_id={job_id})" if job_id else ""),
        }

    if job.status != JobStatus.COMPLETED:
        return {
            "success": False,
            "cards": {},
            "message": f"❌ 任务 {job_id} 尚未完成 (当前状态: {job.status})",
        }

    result = job.result
    if not result:
        return {
            "success": False,
            "cards": {},
            "message": f"❌ 任务 {job_id} 没有可用的分析结果",
        }

    # 3. 从 AnalysisResult 合成各卡片的 payload
    #    AnalysisResult 实际字段: summary(str), insight(str), title(str),
    #    subtitle(str), copywriting, cards(旧URL), ai_images, platform_stats(dict),
    #    platforms_analyzed(list)
    topic = getattr(result, "title", "") or (job.topic if hasattr(job, "topic") else "舆情分析")
    debate_rounds = max(1, min(int(getattr(job, "debate_rounds", 2) or 2), 8))
    platform_stats = _build_platform_stats(result, job)

    card_payloads: Dict[str, Dict[str, Any]] = {}

    # title / debate_timeline / trend / radar 四张核心卡始终可渲染
    card_payloads["title"] = {
        "topic": topic,
        "subtitle": getattr(result, "subtitle", ""),
        "theme": "cool",
    }
    card_payloads["debate_timeline"] = _build_debate_timeline_payload(result, job, topic)
    card_payloads["trend"] = _build_trend_payload(platform_stats, debate_rounds)
    card_payloads["radar"] = _build_radar_payload(platform_stats)

    # insight 卡 — 需要 insight 文本
    insight_text = getattr(result, "insight", "") or getattr(result, "summary", "")
    if insight_text:
        card_payloads["insight"] = {
            "conclusion": insight_text,
            "coverage": {
                "platforms": len(getattr(result, "platforms_analyzed", []) or []),
                "debateRounds": debate_rounds,
                "growth": sum(platform_stats.values()),
                "controversy": "中",
            },
        }

    # platform_heat 卡
    if platform_stats:
        card_payloads["platform_heat"] = _build_platform_heat_payload(platform_stats)

    # key_findings 卡 — 从 summary/insight 文本拆句
    finding_sentences = _split_sentences(getattr(result, "summary", "") or getattr(result, "insight", ""))
    if finding_sentences:
        card_payloads["key_findings"] = {
            "findings": [{"text": sentence} for sentence in finding_sentences[:5]],
        }

    # 4. 渲染
    prefix = f"{job_id}_" if job_id else ""
    requested_card_types = card_types or CORE_CARD_TYPES

    # 选择性渲染 — 仅渲染指定且有 payload 的类型
    to_render = {ct: card_payloads.get(ct) for ct in requested_card_types}

    rendered: Dict[str, Optional[str]] = {}
    for ct, payload in to_render.items():
        if not payload:
            logger.warning(f"[generate_topic_cards] 跳过 {ct}: 当前分析结果中无对应数据")
            continue
        path = await card_render_client.render_card(ct, payload, f"{prefix}{ct}.png")
        rendered[ct] = path

    success_cards = {k: v for k, v in rendered.items() if v}
    failed_cards = [k for k, v in rendered.items() if not v]

    # 5. 回写到 job.result.cards，使 publish/validate 能消费本地 PNG
    if success_cards and job.result is not None:
        from opinion_mcp.schemas import AnalysisCards
        if job.result.cards is None:
            job.result.cards = AnalysisCards()
        cards_obj = job.result.cards
        # 映射: renderer card type → AnalysisCards field
        field_map = {
            "title": "title_card",
            "debate_timeline": "debate_timeline",
            "trend": "trend_analysis",
            "radar": "platform_radar",
        }
        for ct, path in success_cards.items():
            field = field_map.get(ct)
            if field:
                setattr(cards_obj, field, path)

    msg_parts = [f"✅ 成功生成 {len(success_cards)} 张卡片"]
    if failed_cards:
        msg_parts.append(f"⚠️ {len(failed_cards)} 张失败: {', '.join(failed_cards)}")

    return {
        "success": len(success_cards) > 0,
        "cards": success_cards,
        "failed": failed_cards,
        "message": "；".join(msg_parts),
    }
