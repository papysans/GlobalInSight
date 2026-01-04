from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Optional, Tuple

from loguru import logger


_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[`~!@#$%^&*()_\-+=\[\]{}\\|;:'\",.<>/?，。？！、；：“”‘’（）【】《》…·•]+")
_RANK_PREFIX_RE = re.compile(r"^(#?\s*\d+[\.\-、\s]+)+")


CONTROVERSY_KEYWORDS = [
    "塌房",
    "曝光",
    "怒怼",
    "抵制",
    "封禁",
    "涉黄",
    "造假",
    "维权",
    "翻车",
    "暴雷",
    "举报",
    "争议",
    "撕",
    "冲突",
    "开除",
    "辞职",
    "道歉",
    "反转",
    "谣言",
    "辟谣",
    "起诉",
    "判决",
    "事故",
    "伤亡",
]


@dataclass(frozen=True)
class RawItem:
    platform_id: str
    source_id: str
    source_name: str
    title: str
    url: str
    hot_value: str
    rank: Optional[int] = None
    ts: Optional[str] = None

    # Derived
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
    ts: Optional[str]
    source_id: str
    source_name: str


@dataclass
class TopicCluster:
    cluster_id: str
    canonical_title: str
    norm_title: str
    total_hot_score: float
    platforms: List[str] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)

    # Signals
    is_new: bool = False
    hot_score_delta: float = 0.0
    growth: float = 0.0
    controversy_score: float = 0.0
    controversy_reasons: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


def normalize_title(title: str) -> str:
    """Normalize for clustering: remove ranks, punctuation, extra spaces, lowercase."""
    t = (title or "").strip()
    t = _RANK_PREFIX_RE.sub("", t)
    t = t.replace("｜", "|").replace("—", "-").replace("–", "-")
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip().lower()
    return t


def _ngram_set(text: str, n: int = 2) -> set[str]:
    text = (text or "").strip()
    if len(text) <= n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(0, len(text) - n + 1)}


def title_similarity(a: str, b: str) -> float:
    """Cheap hybrid similarity for Chinese/English titles."""
    a_n = normalize_title(a)
    b_n = normalize_title(b)
    if not a_n or not b_n:
        return 0.0
    if a_n == b_n:
        return 1.0

    # 2-gram Jaccard (works ok for Chinese)
    a2 = _ngram_set(a_n, 2)
    b2 = _ngram_set(b_n, 2)
    j = (len(a2 & b2) / max(1, len(a2 | b2))) if (a2 or b2) else 0.0

    # SequenceMatcher (works ok for English + mixed)
    s = SequenceMatcher(None, a_n, b_n).ratio()

    return 0.55 * s + 0.45 * j


def parse_hot_value(raw: Any) -> Tuple[float, str]:
    """Parse hot_value to hot_score and display string.

    Supports:
    - '684万热度' / '1.2亿' / '12345次播放' / '12,345'
    - fallback: 0
    """
    if raw is None:
        return 0.0, "-"
    text = str(raw).strip()
    if not text:
        return 0.0, "-"

    # 次播放
    m_play = re.search(r"([\d,.]+)\s*次播放", text)
    if m_play:
        try:
            return float(m_play.group(1).replace(",", "")), text
        except Exception:
            return 0.0, text

    # 数字 + 单位
    m = re.search(r"([\d,.]+)\s*(亿|万)?", text)
    if not m:
        return 0.0, text

    try:
        num = float(m.group(1).replace(",", ""))
    except Exception:
        num = 0.0
    unit = m.group(2) or ""
    if unit == "亿":
        num *= 1e8
    elif unit == "万":
        num *= 1e4
    return num, text


def make_raw_item(
    *,
    platform_id: str,
    source_id: str,
    source_name: str,
    title: str,
    url: str,
    hot_value: Any,
    rank: Optional[int],
    ts: Optional[str],
) -> RawItem:
    score, display = parse_hot_value(hot_value)
    nt = normalize_title(title)
    return RawItem(
        platform_id=platform_id,
        source_id=source_id,
        source_name=source_name,
        title=title or "",
        url=url or "",
        hot_value=display,
        rank=rank,
        ts=ts,
        norm_title=nt,
        hot_score=score,
    )


def cluster_items(
    items: List[RawItem],
    *,
    similarity_threshold: float = 0.74,
    max_clusters: int = 200,
) -> List[TopicCluster]:
    """Greedy clustering by title similarity."""
    # Prefer high-signal items first
    items_sorted = sorted(items, key=lambda x: (x.hot_score, -(x.rank or 9999)), reverse=True)

    clusters: List[TopicCluster] = []

    for it in items_sorted:
        if not it.norm_title:
            continue
        best_idx = -1
        best_sim = 0.0
        for idx, c in enumerate(clusters):
            sim = title_similarity(it.norm_title, c.norm_title)
            if sim > best_sim:
                best_sim = sim
                best_idx = idx
        if best_idx >= 0 and best_sim >= similarity_threshold:
            c = clusters[best_idx]
            c.total_hot_score += it.hot_score
            if it.platform_id not in c.platforms:
                c.platforms.append(it.platform_id)
            c.evidence.append(
                EvidenceItem(
                    platform_id=it.platform_id,
                    platform_name=it.source_name,
                    title=it.title,
                    url=it.url,
                    hot_value=it.hot_value,
                    hot_score=it.hot_score,
                    rank=it.rank,
                    ts=it.ts,
                    source_id=it.source_id,
                    source_name=it.source_name,
                )
            )
            # Keep canonical title as the highest hot_score evidence
            if it.hot_score >= max((e.hot_score for e in c.evidence), default=0.0):
                c.canonical_title = it.title
                c.norm_title = it.norm_title
        else:
            if len(clusters) >= max_clusters:
                continue
            cid = hashlib.sha1(it.norm_title.encode("utf-8")).hexdigest()[:12]
            clusters.append(
                TopicCluster(
                    cluster_id=cid,
                    canonical_title=it.title,
                    norm_title=it.norm_title,
                    total_hot_score=it.hot_score,
                    platforms=[it.platform_id],
                    evidence=[
                        EvidenceItem(
                            platform_id=it.platform_id,
                            platform_name=it.source_name,
                            title=it.title,
                            url=it.url,
                            hot_value=it.hot_value,
                            hot_score=it.hot_score,
                            rank=it.rank,
                            ts=it.ts,
                            source_id=it.source_id,
                            source_name=it.source_name,
                        )
                    ],
                )
            )

    # Dedup evidence per (platform_id,url,title)
    for c in clusters:
        seen = set()
        deduped = []
        for e in sorted(c.evidence, key=lambda x: x.hot_score, reverse=True):
            k = (e.platform_id, (e.url or "").lower(), (e.title or "").lower())
            if k in seen:
                continue
            seen.add(k)
            deduped.append(e)
        c.evidence = deduped

    # Order clusters by total score desc
    clusters.sort(key=lambda x: x.total_hot_score, reverse=True)
    return clusters


def compute_controversy(cluster: TopicCluster) -> Tuple[float, List[str], List[str]]:
    """Rule-based controversy score with reasons and keyword list."""
    reasons: List[str] = []
    hits: List[str] = []

    joined = " ".join([e.title for e in cluster.evidence if e.title])
    for kw in CONTROVERSY_KEYWORDS:
        if kw in joined:
            hits.append(kw)
    if hits:
        reasons.append(f"命中争议词: {', '.join(sorted(set(hits))[:6])}")

    # Cross-platform disagreement: if titles vary a lot, increase score.
    titles = [e.title for e in cluster.evidence if e.title]
    if len(titles) >= 2:
        sims = []
        for i in range(min(6, len(titles))):
            for j in range(i + 1, min(6, len(titles))):
                sims.append(title_similarity(titles[i], titles[j]))
        if sims:
            avg_sim = sum(sims) / len(sims)
            disagreement = max(0.0, 1.0 - avg_sim)
            if disagreement >= 0.25:
                reasons.append(f"跨平台表述分歧: {disagreement:.2f}")
        else:
            disagreement = 0.0
    else:
        disagreement = 0.0

    # Growth proxy: stronger total score -> a bit higher baseline
    score = 0.0
    score += 18.0 * len(set(hits))
    score += 60.0 * disagreement
    score += min(20.0, math.log1p(max(0.0, cluster.total_hot_score)) / 2.0)

    # Clamp to 0-100
    score = max(0.0, min(100.0, score))
    return score, reasons, sorted(set(hits))


def format_hot_score(score: float) -> str:
    """Format aggregated hot score for display (avoid platform-specific strings like 次播放)."""
    try:
        s = float(score)
    except Exception:
        return "-"
    if s <= 0:
        return "-"
    if s >= 1e8:
        return f"{s / 1e8:.1f}亿"
    if s >= 1e4:
        return f"{s / 1e4:.1f}万"
    return str(int(round(s)))


def clusters_to_api(
    clusters: List[TopicCluster],
    *,
    collection_time: str,
) -> List[Dict[str, Any]]:
    """Convert clusters to the existing frontend-friendly shape."""
    out: List[Dict[str, Any]] = []
    for idx, c in enumerate(clusters, 1):
        controversy, reasons, kws = compute_controversy(c)
        c.controversy_score = controversy
        c.controversy_reasons = reasons
        c.keywords = kws

        platforms_data = [
            {
                "platform": e.platform_name or e.platform_id,
                "platform_id": e.platform_id,
                "hot_value": e.hot_value,
                "hot_score": e.hot_score,
                "url": e.url,
                "title": e.title,
                "rank": e.rank,
            }
            for e in sorted(c.evidence, key=lambda x: x.hot_score, reverse=True)[:10]
        ]

        evidence = [
            {
                "platform": e.platform_name or e.platform_id,
                "platform_id": e.platform_id,
                "title": e.title,
                "url": e.url,
                "hot_value": e.hot_value,
                "hot_score": e.hot_score,
                "rank": e.rank,
                "timestamp": e.ts or collection_time,
                "source_id": e.source_id,
                "source_name": e.source_name,
            }
            for e in sorted(c.evidence, key=lambda x: x.hot_score, reverse=True)[:20]
        ]

        out.append(
            {
                "id": c.cluster_id,
                "title": c.canonical_title,
                "url": evidence[0]["url"] if evidence else "",
                # Use aggregated score for main display to avoid confusing mixed units (e.g. 次播放).
                "hot_value": format_hot_score(c.total_hot_score),
                "rank": idx,
                "source": "Aligned",
                "source_id": "aligned",
                "category": "aligned",
                "timestamp": collection_time,
                "platform": f"{len(set(c.platforms))}平台对齐",
                # IMPORTANT: use this for platform filtering on frontend; do not rely only on top-N evidence
                # because some low-score platforms (e.g. HN / Tieba) may be trimmed out of evidence.
                "platform_ids": sorted(list(set(c.platforms))),
                "platforms_data": platforms_data,
                "evidence": evidence,
                "conflicts": c.controversy_reasons,
                "controversy": c.controversy_score,
                "keywords": c.keywords,
                # placeholders to be filled by history signals layer
                "growth": c.growth,
                "hot_score": c.total_hot_score,
                "hot_score_delta": c.hot_score_delta,
                "is_new": c.is_new,
            }
        )
    return out

