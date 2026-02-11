#!/usr/bin/env python3
"""Generate app/services/hotnews_alignment.py with full Chinese content."""
import os

CONTENT = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
\u70ed\u699c\u8bdd\u9898\u805a\u7c7b\u4e0e\u7edf\u4e00\u70ed\u5ea6\u8bc4\u5206
"""
from __future__ import annotations
import hashlib, math, re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[`~!@#$%^&*()_\-+=\[\]{}\\|;:'\",.<>/?]+")
_PUNCT_ZH_RE = re.compile(r"[\uff0c\u3002\uff1f\uff01\u3001\uff1b\uff1a\u201c\u201d\u2018\u2019\uff08\uff09\u3010\u3011\u300a\u300b\u2026\u00b7\u2022\U0001f525\U0001f4b0\U0001f4c8\U0001f4c9]+")
_RANK_PREFIX_RE = re.compile(r"^(#?\s*\d+[\.\-\u3001\s]+)+")

FINANCE_CONTROVERSY_KEYWORDS = [
    "\u66b4\u96f7","\u9000\u5e02","\u7206\u4ed3","\u8dcc\u505c","\u5229\u7a7a","\u505a\u7a7a","\u66b4\u8dcc",
    "\u8fdd\u89c4","\u5904\u7f5a","\u7f5a\u6b3e","\u9020\u5047","\u8d22\u52a1\u9020\u5047","\u5185\u5e55\u4ea4\u6613",
    "\u51cf\u6301","\u6e05\u4ed3","\u8d28\u62bc","\u7206\u96f7","\u4e8f\u635f","\u7834\u4ea7",
    "\u76d1\u7ba1","\u8c03\u67e5","\u7acb\u6848","\u8b66\u793a","\u98ce\u9669","ST",
    "\u5d29\u76d8","\u5272\u97ed\u83dc","\u95ea\u5d29","\u9ed1\u5929\u9e45","\u8e29\u96f7",
    "\u8bc9\u8bbc","\u4ef2\u88c1","\u8fdd\u7ea6","\u6b3a\u8bc8",
]


@dataclass(frozen=True)
class RawItem:
    platform_id: str
    source_name: str
    title: str
    url: str
    hot_value: str
    rank: Optional[int] = None
    published_time: Optional[str] = None
    summary: str = ""
    original_id: str = ""
    category: str = "domestic"
    norm_title: str = ""
    hot_score: float = 0.0


@dataclass
class EvidenceItem:
    platform_id: str
    platform_name: str
    title: str
    url: str
    hot_value: str
    hot_score: float
    rank: Optional[int]
    published_time: Optional[str]
    summary: str = ""
    original_id: str = ""


@dataclass
class TopicCluster:
    cluster_id: str
    canonical_title: str
    norm_title: str
    total_hot_score: float
    platforms: List[str] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)
    heat_score: float = 0.0
    is_new: bool = True
    hot_score_delta: float = 0.0
    growth: float = 0.0
    controversy_score: float = 0.0
    controversy_reasons: List[str] = field(default_factory=list)
    controversy_keywords: List[str] = field(default_factory=list)


def normalize_title(title: str) -> str:
    t = (title or "").strip()
    t = _RANK_PREFIX_RE.sub("", t)
    t = _PUNCT_RE.sub(" ", t)
    t = _PUNCT_ZH_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip().lower()
    return t


def _ngram_set(text: str, n: int = 2) -> set:
    text = (text or "").strip()
    if len(text) <= n:
        return {text} if text else set()
    return {text[i:i+n] for i in range(len(text)-n+1)}


def title_similarity(a: str, b: str) -> float:
    a_n, b_n = normalize_title(a), normalize_title(b)
    if not a_n or not b_n:
        return 0.0
    if a_n == b_n:
        return 1.0
    a2, b2 = _ngram_set(a_n, 2), _ngram_set(b_n, 2)
    j = (len(a2 & b2) / max(1, len(a2 | b2))) if (a2 or b2) else 0.0
    s = SequenceMatcher(None, a_n, b_n).ratio()
    return 0.55 * s + 0.45 * j


def parse_hot_value(raw: Any) -> Tuple[float, str]:
    if raw is None:
        return 0.0, "-"
    text = str(raw).strip()
    if not text:
        return 0.0, "-"
    m_pct = re.search(r"([\d,.]+)\s*%", text)
    if m_pct:
        try:
            return abs(float(m_pct.group(1).replace(",", ""))) * 1000, text
        except Exception:
            return 0.0, text
    m = re.search(r"([\d,.]+)\s*(\u4ebf|\u4e07)?", text)
    if not m:
        return 0.0, text
    try:
        num = float(m.group(1).replace(",", ""))
    except Exception:
        num = 0.0
    unit = m.group(2) or ""
    if unit == "\u4ebf":
        num *= 1e8
    elif unit == "\u4e07":
        num *= 1e4
    return num, text


def format_hot_score(score: float) -> str:
    if score <= 0:
        return "-"
    if score >= 1e8:
        return f"{score / 1e8:.1f}\u4ebf"
    if score >= 1e4:
        return f"{score / 1e4:.1f}\u4e07"
    return str(int(round(score)))


def make_raw_item(
    *,
    platform_id: str,
    source_name: str,
    title: str,
    url: str,
    hot_value: Any,
    rank: Optional[int],
    published_time: Optional[str],
    summary: str = "",
    original_id: str = "",
    category: str = "domestic",
) -> RawItem:
    score, display = parse_hot_value(hot_value)
    nt = normalize_title(title)
    return RawItem(
        platform_id=platform_id, source_name=source_name,
        title=title or "", url=url or "", hot_value=display,
        rank=rank, published_time=published_time,
        summary=summary, original_id=original_id,
        category=category, norm_title=nt, hot_score=score,
    )


def cluster_items(
    items: List[RawItem],
    *,
    similarity_threshold: float = 0.74,
    max_clusters: int = 200,
) -> List[TopicCluster]:
    items_sorted = sorted(items, key=lambda x: (x.hot_score, -(x.rank or 9999)), reverse=True)
    clusters: List[TopicCluster] = []
    for it in items_sorted:
        if not it.norm_title:
            continue
        best_idx, best_sim = -1, 0.0
        for idx, c in enumerate(clusters):
            sim = title_similarity(it.norm_title, c.norm_title)
            if sim > best_sim:
                best_sim, best_idx = sim, idx
        ev = EvidenceItem(
            platform_id=it.platform_id, platform_name=it.source_name,
            title=it.title, url=it.url, hot_value=it.hot_value,
            hot_score=it.hot_score, rank=it.rank,
            published_time=it.published_time, summary=it.summary,
            original_id=it.original_id,
        )
        if best_idx >= 0 and best_sim >= similarity_threshold:
            c = clusters[best_idx]
            c.total_hot_score += it.hot_score
            if it.platform_id not in c.platforms:
                c.platforms.append(it.platform_id)
            c.evidence.append(ev)
            if it.hot_score >= max((e.hot_score for e in c.evidence), default=0.0):
                c.canonical_title = it.title
                c.norm_title = it.norm_title
        else:
            if len(clusters) >= max_clusters:
                continue
            cid = hashlib.sha1(it.norm_title.encode("utf-8")).hexdigest()[:12]
            clusters.append(TopicCluster(
                cluster_id=cid, canonical_title=it.title,
                norm_title=it.norm_title, total_hot_score=it.hot_score,
                platforms=[it.platform_id], evidence=[ev],
            ))
    for c in clusters:
        seen = set()
        deduped = []
        for e in sorted(c.evidence, key=lambda x: x.hot_score, reverse=True):
            k = (e.platform_id, (e.url or "").lower(), (e.title or "").lower())
            if k not in seen:
                seen.add(k)
                deduped.append(e)
        c.evidence = deduped
    clusters.sort(key=lambda x: x.total_hot_score, reverse=True)
    return clusters


def _best_published_time(cluster: TopicCluster) -> Optional[str]:
    times = [e.published_time for e in cluster.evidence if e.published_time]
    return max(times) if times else None


def _time_decay_factor(published_time: Optional[str]) -> float:
    if not published_time:
        return 0.5
    try:
        pub_dt = datetime.fromisoformat(published_time.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc) if pub_dt.tzinfo else datetime.now()
        hours_ago = max(0, (now - pub_dt).total_seconds() / 3600)
    except (ValueError, TypeError):
        hours_ago = 12
    return max(0.3, min(1.0, math.exp(-0.05 * hours_ago)))


def score_clusters(clusters: List[TopicCluster]) -> None:
    if not clusters:
        return
    raw_scores: List[float] = []
    for c in clusters:
        n_platforms = len(set(c.platforms))
        boost = 1.0 + max(0, n_platforms - 1) * 0.2
        tf = _time_decay_factor(_best_published_time(c))
        raw_scores.append(c.total_hot_score * boost * tf)
    min_s, max_s = min(raw_scores), max(raw_scores)
    spread = max_s - min_s
    for c, raw in zip(clusters, raw_scores):
        if spread > 0:
            c.heat_score = round(((raw - min_s) / spread) * 100, 1)
        elif raw > 0:
            c.heat_score = 50.0
        else:
            c.heat_score = 0.0
    clusters.sort(key=lambda x: x.heat_score, reverse=True)


def compute_controversy(cluster: TopicCluster) -> None:
    reasons: List[str] = []
    hits: List[str] = []
    joined = " ".join(e.title for e in cluster.evidence if e.title)
    for kw in FINANCE_CONTROVERSY_KEYWORDS:
        if kw in joined:
            hits.append(kw)
    if hits:
        reasons.append(f"\u547d\u4e2d\u4e89\u8bae\u8bcd: {', '.join(sorted(set(hits))[:6])}")
    titles = [e.title for e in cluster.evidence if e.title]
    disagreement = 0.0
    if len(titles) >= 2:
        sims = []
        for i in range(min(6, len(titles))):
            for j in range(i+1, min(6, len(titles))):
                sims.append(title_similarity(titles[i], titles[j]))
        if sims:
            avg_sim = sum(sims) / len(sims)
            disagreement = max(0.0, 1.0 - avg_sim)
            if disagreement >= 0.25:
                reasons.append(f"\u8de8\u5e73\u53f0\u8868\u8ff0\u5206\u6b67: {disagreement:.2f}")
    score = 18.0 * len(set(hits)) + 60.0 * disagreement
    score += min(20.0, math.log1p(max(0.0, cluster.total_hot_score)) / 2.0)
    cluster.controversy_score = round(max(0.0, min(100.0, score)), 1)
    cluster.controversy_reasons = reasons
    cluster.controversy_keywords = sorted(set(hits))


def _build_prev_map(prev_snapshot: Optional[Dict[str, Any]]) -> Dict[str, float]:
    if not prev_snapshot:
        return {}
    out: Dict[str, float] = {}
    for c in (prev_snapshot.get("clusters") or []):
        cid = c.get("id") or c.get("cluster_id")
        if cid:
            try:
                out[str(cid)] = float(c.get("hot_score") or c.get("total_hot_score") or 0.0)
            except Exception:
                out[str(cid)] = 0.0
    return out


def apply_history_signals(clusters: List[TopicCluster], prev_snapshot: Optional[Dict[str, Any]]) -> None:
    prev_map = _build_prev_map(prev_snapshot)
    for c in clusters:
        cur = c.total_hot_score
        prev = prev_map.get(c.cluster_id, 0.0)
        c.is_new = c.cluster_id not in prev_map
        c.hot_score_delta = round(cur - prev, 2)
        denom = prev if prev > 1.0 else 1.0
        c.growth = round(max(-999.0, min(999.0, ((cur - prev) / denom) * 100.0)))


def make_history_snapshot(clusters: List[TopicCluster], ts: str) -> Dict[str, Any]:
    return {
        "ts": ts, "collection_time": ts,
        "clusters": [
            {"id": c.cluster_id, "title": c.canonical_title,
             "hot_score": c.total_hot_score, "platforms": list(set(c.platforms))}
            for c in clusters
        ],
    }


def align_and_score(
    raw_items: List[RawItem],
    *,
    prev_snapshot: Optional[Dict[str, Any]] = None,
    similarity_threshold: float = 0.74,
) -> Tuple[List[TopicCluster], Dict[str, Any]]:
    if not raw_items:
        return [], {}
    logger.info(f"\U0001f504 \u70ed\u699c\u5bf9\u9f50: {len(raw_items)} \u6761\u539f\u59cb\u6570\u636e")
    clusters = cluster_items(raw_items, similarity_threshold=similarity_threshold)
    logger.info(f"\U0001f4ca \u805a\u7c7b\u7ed3\u679c: {len(clusters)} \u4e2a\u8bdd\u9898")
    score_clusters(clusters)
    for c in clusters:
        compute_controversy(c)
    apply_history_signals(clusters, prev_snapshot)
    ts = datetime.now().isoformat()
    snapshot = make_history_snapshot(clusters, ts)
    cross = sum(1 for c in clusters if len(set(c.platforms)) > 1)
    logger.info(f"\u2705 \u70ed\u699c\u5bf9\u9f50\u5b8c\u6210: {len(clusters)} \u4e2a\u8bdd\u9898, \u8de8\u5e73\u53f0: {cross} \u4e2a")
    return clusters, snapshot


def clusters_to_api(clusters: List[TopicCluster], collection_time: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx, c in enumerate(clusters, 1):
        platforms_data = [
            {"platform": e.platform_name, "platform_id": e.platform_id,
             "hot_value": e.hot_value, "hot_score": e.hot_score,
             "url": e.url, "title": e.title, "rank": e.rank}
            for e in sorted(c.evidence, key=lambda x: x.hot_score, reverse=True)[:10]
        ]
        evidence = [
            {"platform": e.platform_name, "platform_id": e.platform_id,
             "title": e.title, "url": e.url, "hot_value": e.hot_value,
             "hot_score": e.hot_score, "rank": e.rank,
             "published_time": e.published_time or collection_time,
             "summary": e.summary}
            for e in sorted(c.evidence, key=lambda x: x.hot_score, reverse=True)[:20]
        ]
        best_url = evidence[0]["url"] if evidence else ""
        best_summary = next((e.summary for e in c.evidence if e.summary), c.canonical_title)
        n_plat = len(set(c.platforms))
        out.append({
            "id": c.cluster_id, "title": c.canonical_title,
            "summary": best_summary, "url": best_url,
            "hot_value": format_hot_score(c.total_hot_score),
            "heat_score": c.heat_score, "rank": idx,
            "category": "domestic", "collection_time": collection_time,
            "platform_count": n_plat,
            "platform_label": f"{n_plat}\u5e73\u53f0\u70ed\u8bae",
            "platform_ids": sorted(set(c.platforms)),
            "platforms_data": platforms_data, "evidence": evidence,
            "controversy": c.controversy_score,
            "controversy_reasons": c.controversy_reasons,
            "controversy_keywords": c.controversy_keywords,
            "is_new": c.is_new, "growth": c.growth,
            "hot_score_delta": c.hot_score_delta,
        })
    return out
'''

target = os.path.join("app", "services", "hotnews_alignment.py")
with open(target, "w", encoding="utf-8") as f:
    f.write(CONTENT)
print(f"Written {os.path.getsize(target)} bytes to {target}")
