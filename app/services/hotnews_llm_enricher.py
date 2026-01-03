from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        logger.warning(f"[HotNewsLLM] Failed saving cache: {e}")


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


async def enrich_hotnews_clusters(
    clusters: List[Dict[str, Any]],
    *,
    collection_time: str,
    top_n: int = 20,
) -> List[Dict[str, Any]]:
    """Optional LLM enrichment for top clusters.

    Disabled by default. Enable by setting environment:
      HOTNEWS_LLM_ENRICH=1

    Adds/overrides:
    - title (normalized/canonical)
    - keywords (list)
    - conflicts (LLM summary points, optional)
    """
    enabled = os.getenv("HOTNEWS_LLM_ENRICH", "").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return clusters

    try:
        from app.llm import get_agent_llm
        from langchain_core.messages import SystemMessage, HumanMessage
    except Exception as e:
        logger.warning(f"[HotNewsLLM] LLM deps unavailable: {e}")
        return clusters

    repo_root = Path(__file__).resolve().parents[2]
    cache_path = repo_root / "outputs" / "hotnews_llm_cache.json"
    cache = _load_cache(cache_path)

    day = (collection_time or datetime.now().isoformat())[:10]
    llm = get_agent_llm("analyst")

    for c in clusters[:top_n]:
        cid = str(c.get("id") or "")
        if not cid:
            continue
        cache_key = f"{day}:{cid}"
        if cache_key in cache:
            enriched = cache.get(cache_key) or {}
            if isinstance(enriched, dict):
                if enriched.get("title"):
                    c["title"] = enriched["title"]
                if enriched.get("keywords"):
                    c["keywords"] = enriched["keywords"]
                if enriched.get("conflicts"):
                    c["conflicts"] = enriched["conflicts"]
            continue

        evidence = c.get("evidence") or []
        ev_lines = []
        for ev in evidence[:6]:
            ev_lines.append(f"- [{ev.get('platform')}] {ev.get('title')} | {ev.get('hot_value')}")

        prompt = (
            "你将看到一个“跨平台对齐”的热点话题簇（来自不同平台的热榜标题）。\n"
            "请输出严格 JSON（不要 markdown），字段如下：\n"
            '{\n'
            '  "title": "归一后的统一标题（<=30字）",\n'
            '  "keywords": ["关键词1","关键词2","关键词3"],\n'
            '  "conflicts": ["可能争议点1","可能争议点2"]\n'
            '}\n'
            "注意：conflicts 是“可能争议点/分歧点”，不做事实核验；如果没有明显争议，可输出空数组。\n\n"
            f"当前簇标题: {c.get('title')}\n"
            "证据标题列表:\n"
            + "\n".join(ev_lines)
        )

        try:
            resp = await llm.ainvoke(
                [
                    SystemMessage(content="你是一个严谨的热点聚类标注助手，只输出 JSON。"),
                    HumanMessage(content=prompt),
                ]
            )
            text = getattr(resp, "content", None) or str(resp)
            obj = _extract_json(text) or {}
            title = obj.get("title")
            keywords = obj.get("keywords")
            conflicts = obj.get("conflicts")

            enriched = {
                "title": title if isinstance(title, str) else None,
                "keywords": keywords if isinstance(keywords, list) else None,
                "conflicts": conflicts if isinstance(conflicts, list) else None,
            }
            cache[cache_key] = enriched
            _save_cache(cache_path, cache)

            if enriched.get("title"):
                c["title"] = enriched["title"]
            if enriched.get("keywords"):
                c["keywords"] = enriched["keywords"]
            if enriched.get("conflicts"):
                c["conflicts"] = enriched["conflicts"]
        except Exception as e:
            logger.warning(f"[HotNewsLLM] Enrich failed for {cid}: {e}")
            continue

    return clusters

