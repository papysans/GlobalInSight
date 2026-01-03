from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def _load_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(path: Path, data: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"[HotNewsInterpret] Failed saving cache: {e}")


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    m = _JSON_BLOCK_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _heuristic_stage(is_new: bool, growth: float, delta: float) -> str:
    # Simple lifecycle heuristic; LLM may refine.
    if is_new and growth >= 0:
        return "爆发期"
    if growth >= 30 or delta >= 0:
        return "扩散期"
    if growth <= -15 or delta < 0:
        return "回落期"
    return "盘整期"


def _trace_steps_default(cache_hit: bool) -> List[str]:
    if cache_hit:
        return [
            "S1 规则信号提取（平台覆盖/增速/变化）",
            "S2 LLM 舆情解读（生命周期/扩散/分歧/观察点）",
            "S3 缓存命中（复用结果，降低成本）",
        ]
    return [
        "S1 规则信号提取（平台覆盖/增速/变化）",
        "S2 LLM 舆情解读（生命周期/扩散/分歧/观察点）",
        "S3 缓存写入（供后续复用）",
    ]


def _summarize_platforms(platforms_data: List[Dict[str, Any]], evidence: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    platforms: List[str] = []
    titles: List[str] = []

    for p in platforms_data[:10]:
        name = (p.get("platform") or p.get("platform_id") or "").strip()
        if name and name not in platforms:
            platforms.append(name)

    for ev in evidence[:8]:
        t = (ev.get("title") or "").strip()
        if t:
            titles.append(t)
    return platforms, titles


async def interpret_hot_topic(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an evolution interpretation card for a single topic/cluster.

    Calls LLM only when available; otherwise returns heuristic summary.
    Uses a small JSON cache under outputs/ to avoid repeated token spend.
    """
    topic_id = str(payload.get("id") or "")
    title = str(payload.get("title") or "")
    collection_time = payload.get("collection_time") or payload.get("timestamp") or datetime.now().isoformat()
    day = str(collection_time)[:10]

    growth = payload.get("growth")
    delta = payload.get("hot_score_delta")
    is_new = bool(payload.get("is_new", False))

    try:
        growth_f = float(growth) if growth is not None else 0.0
    except Exception:
        growth_f = 0.0
    try:
        delta_f = float(delta) if delta is not None else 0.0
    except Exception:
        delta_f = 0.0

    stage = _heuristic_stage(is_new, growth_f, delta_f)

    platforms_data = payload.get("platforms_data") or []
    evidence = payload.get("evidence") or []
    platforms, evidence_titles = _summarize_platforms(platforms_data, evidence)
    platform_count = len(platforms) if platforms else len({(e.get("platform") or "") for e in evidence if e.get("platform")})

    # Cache key per day + topic id + collection_time (so new snapshots get new analysis)
    repo_root = Path(__file__).resolve().parents[2]
    cache_path = repo_root / "outputs" / "hotnews_interpret_cache.json"
    cache = _load_cache(cache_path)
    cache_key = f"{day}:{topic_id}:{collection_time}"
    if cache_key in cache and isinstance(cache.get(cache_key), dict):
        cached = cache[cache_key]
        return {
            "success": True,
            "id": topic_id,
            "title": title,
            "agent_name": "hotnews_interpretation_agent",
            "cache_hit": True,
            "trace_steps": cached.get("trace_steps") or _trace_steps_default(cache_hit=True),
            **cached,
            "used_llm": cached.get("used_llm", False),
        }

    # Heuristic fallback (no LLM)
    heuristic = {
        "agent_name": "hotnews_interpretation_agent",
        "cache_hit": False,
        "trace_steps": _trace_steps_default(cache_hit=False),
        "lifecycle_stage": stage,
        "diffusion_summary": f"覆盖平台数约 {platform_count}。当前增速 {int(growth_f)}，热度变化 {delta_f:.1f}，整体处于{stage}。",
        "divergence_points": [],
        "watch_points": [
            "观察是否出现新的核心叙事/关键词（标题措辞变化）",
            "观察是否从单一平台扩散到多平台（覆盖平台数变化）",
        ],
        "confidence": 0.45,
        "used_llm": False,
    }

    # LLM enabled? (default ON for this endpoint; if keys missing, it will fall back)
    try:
        from app.llm import get_agent_llm
        from langchain_core.messages import SystemMessage, HumanMessage
    except Exception as e:
        logger.warning(f"[HotNewsInterpret] LLM deps unavailable: {e}")
        cache[cache_key] = heuristic
        _save_cache(cache_path, cache)
        return {"success": True, "id": topic_id, "title": title, **heuristic}

    llm = get_agent_llm("hotnews_interpretation_agent")

    prompt = (
        "你是舆情分析师。你只能看到热榜标题/平台覆盖/粗略的增速信号（注意各平台热度口径不同）。\n"
        "请输出严格 JSON（不要 markdown），字段如下：\n"
        '{\n'
        '  "lifecycle_stage": "爆发期/扩散期/回落期/盘整期",\n'
        '  "diffusion_summary": "2-4句：扩散态势与节奏解读（避免把热度当绝对值）",\n'
        '  "divergence_points": ["2-4条：跨平台表述差异/关注点差异"],\n'
        '  "watch_points": ["2-4条：接下来值得观察的变量/可能拐点"],\n'
        '  "confidence": 0.0\n'
        '}\n'
        "约束：不做事实核验；不要引用外部信息；如果信息不足，降低 confidence。\n\n"
        f"话题: {title}\n"
        f"建议生命周期(启发式): {stage}\n"
        f"覆盖平台数(估计): {platform_count}\n"
        f"平台列表: {platforms[:10]}\n"
        f"增速(growth): {growth}\n"
        f"热度变化(delta): {delta}\n"
        "各平台标题样本:\n"
        + "\n".join([f"- {t}" for t in evidence_titles[:8]])
    )

    try:
        resp = await llm.ainvoke(
            [
                SystemMessage(content="你是严谨的舆情分析师，只输出 JSON。"),
                HumanMessage(content=prompt),
            ]
        )
        text = getattr(resp, "content", None) or str(resp)
        obj = _extract_json(text) or {}

        result = {
            "agent_name": "hotnews_interpretation_agent",
            "cache_hit": False,
            "trace_steps": heuristic["trace_steps"],
            "lifecycle_stage": str(obj.get("lifecycle_stage") or stage),
            "diffusion_summary": str(obj.get("diffusion_summary") or heuristic["diffusion_summary"]),
            "divergence_points": obj.get("divergence_points") if isinstance(obj.get("divergence_points"), list) else [],
            "watch_points": obj.get("watch_points") if isinstance(obj.get("watch_points"), list) else heuristic["watch_points"],
            "confidence": float(obj.get("confidence")) if isinstance(obj.get("confidence"), (int, float)) else 0.6,
            "used_llm": True,
        }

        cache[cache_key] = result
        _save_cache(cache_path, cache)
        return {"success": True, "id": topic_id, "title": title, **result}
    except Exception as e:
        logger.warning(f"[HotNewsInterpret] LLM call failed: {e}")
        cache[cache_key] = heuristic
        _save_cache(cache_path, cache)
        return {"success": True, "id": topic_id, "title": title, **heuristic}

