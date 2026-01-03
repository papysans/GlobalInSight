from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


def _build_prev_map(prev_snapshot: Dict[str, Any]) -> Dict[str, float]:
    prev_clusters = prev_snapshot.get("clusters") or []
    out: Dict[str, float] = {}
    for c in prev_clusters:
        cid = c.get("id") or c.get("cluster_id")
        if not cid:
            continue
        try:
            out[str(cid)] = float(c.get("hot_score") or c.get("total_hot_score") or 0.0)
        except Exception:
            out[str(cid)] = 0.0
    return out


def apply_history_signals(
    cluster_items: List[Dict[str, Any]],
    *,
    prev_snapshot: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    """Attach simple trend/growth signals from previous snapshot.

    We keep it intentionally lightweight:
    - match by `id` (stable sha1(norm_title) for clusters)
    - compute delta and growth percentage
    """
    prev_map: Dict[str, float] = _build_prev_map(prev_snapshot or {})

    for item in cluster_items:
        cid = str(item.get("id") or "")
        cur = float(item.get("hot_score") or 0.0)
        prev = float(prev_map.get(cid, 0.0))

        is_new = cid not in prev_map
        delta = cur - prev
        denom = prev if prev > 1.0 else 1.0
        growth_pct = (delta / denom) * 100.0

        # Clamp to reasonable UI range
        if growth_pct > 999:
            growth_pct = 999.0
        if growth_pct < -999:
            growth_pct = -999.0

        item["is_new"] = is_new
        item["hot_score_delta"] = round(delta, 2)
        item["growth"] = int(round(growth_pct))

    return cluster_items


def make_history_snapshot(
    *,
    ts: str,
    clusters: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Minimized snapshot for future diffs."""
    slim = []
    for c in clusters:
        slim.append(
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "hot_score": c.get("hot_score") or 0.0,
                "platforms": [
                    p.get("platform_id")
                    for p in (c.get("platforms_data") or [])
                    if isinstance(p, dict) and p.get("platform_id")
                ],
            }
        )
    return {"ts": ts, "clusters": slim}

