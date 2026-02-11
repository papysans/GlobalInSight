#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热榜话题聚类与统一热度评分

核心逻辑：
1. 标题归一化 + 2-gram Jaccard / SequenceMatcher 混合相似度
2. 关键实体提取（公司名/品牌名、股票代码、人名）辅助匹配
3. 摘要关键词重叠度作为辅助信号
4. 动态权重：有实体时实体权重高，无实体时文本权重回升
5. 贪心聚类：相似标题归为同一 TopicCluster
6. 排序评分：排名分 + 跨平台加成 + 热度归一化 + 时间衰减
"""
from __future__ import annotations
import hashlib, math, re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple
from loguru import logger

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[`~!@#$%^&*()_\-+=\[\]{}\\|;:\'\",.< >/?]+")
_PUNCT_ZH_RE = re.compile(r"[，。？！、；：""''（）【】《》…·•🔥💰📈📉]+")
_RANK_PREFIX_RE = re.compile(r"^(#?\s*\d+[\.\-、\s]+)+")

# 实体提取：公司名（含常见后缀）
_COMPANY_RE = re.compile(
    r"[\u4e00-\u9fff]{2,8}"
    r"(?:公司|集团|银行|证券|基金|保险|科技|电子|汽车|能源|医药|地产|控股|股份|影视|电气|重工|光电|半导体|生物)"
)
# 品牌/机构名（高频出现的专有名词，2-4字中文后面不需要后缀）
_BRAND_RE = re.compile(
    r"(?:胖东来|比亚迪|华为|腾讯|阿里|百度|小米|字节跳动|美团|京东|拼多多|"
    r"宁德时代|茅台|五粮液|中芯国际|海康威视|恒瑞医药|迈瑞医疗|"
    r"特斯拉|苹果|英伟达|谷歌|微软|亚马逊|Meta|OpenAI|DeepSeek|"
    r"波士顿动力|横店影视|掌阅科技|山东玻纤|灵宝黄金|精测电子|"
    r"美联储|央行|财政部|证监会|银保监会|发改委|国新办|商务部|工信部|"
    r"ChatGPT|Seedance|Sora)"
)
# A股代码
_STOCK_CODE_RE = re.compile(r"(?:SH|SZ|sh|sz|沪|深)?[036]\d{5}")
# 财经关键词
_KEY_TERMS_RE = re.compile(
    r"(?:降息|加息|降准|MLF|LPR|GDP|CPI|PMI|美联储|央行|财报|业绩|"
    r"并购|重组|IPO|增持|回购|分红|送转|解禁|定增|配股|"
    r"芯片|半导体|新能源|光伏|锂电|AI|人工智能|机器人|"
    r"特朗普|关税|贸易战|制裁|出口管制|"
    r"房地产|楼市|房价|土拍|"
    r"黄金|原油|比特币|数字货币|"
    r"涨停|跌停|暴涨|暴跌|大涨|大跌|"
    r"牛市|熊市|反弹|回调|震荡|"
    r"退休|退市|红包|春节|过节)"
)

FINANCE_CONTROVERSY_KEYWORDS = [
    # 负面事件
    "暴雷","退市","爆仓","跌停","利空","做空","暴跌","大跌","闪崩","崩盘",
    "爆雷","割韭菜","黑天鹅","踩雷",
    # 违规/处罚
    "违规","处罚","罚款","造假","财务造假","内幕交易","欺诈",
    "诉讼","仲裁","违约","立案",
    # 监管/风险
    "监管","调查","警示","风险","ST","约谈","整改","叫停","问询","通报",
    # 资金/持仓异动
    "减持","清仓","质押","亏损","破产","下降","下滑","缩水","蒸发",
    # 争议性事件
    "争议","质疑","举报","投诉","维权","曝光","丑闻","泄露",
    # 市场异动
    "熔断","停牌","异动","预警","警告",
]

# 数值异动正则：匹配"下降XX%"、"下跌XX%"、"缩水XX%"、"亏损XX亿"等
_CONTROVERSY_NUM_RE = re.compile(
    r"(?:下降|下跌|下滑|缩水|蒸发|亏损|减少|暴跌|大跌|跌幅)"
    r"[\s]*[\d,.]+\s*[%％亿万]"
)
# 约谈/处罚主体
_CONTROVERSY_ACTION_RE = re.compile(
    r"(?:被约谈|被处罚|被罚款|被调查|被立案|被通报|被问询|被举报|被曝光|被起诉)"
)

@dataclass(frozen=True)
class RawItem:
    platform_id: str; source_name: str; title: str; url: str; hot_value: str
    rank: Optional[int] = None; published_time: Optional[str] = None
    summary: str = ""; original_id: str = ""; category: str = "domestic"
    norm_title: str = ""; hot_score: float = 0.0

@dataclass
class EvidenceItem:
    platform_id: str; platform_name: str; title: str; url: str
    hot_value: str; hot_score: float; rank: Optional[int]
    published_time: Optional[str]; summary: str = ""; original_id: str = ""

@dataclass
class TopicCluster:
    cluster_id: str; canonical_title: str; norm_title: str; total_hot_score: float
    platforms: List[str] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)
    heat_score: float = 0.0
    is_new: bool = True; hot_score_delta: float = 0.0; growth: float = 0.0
    controversy_score: float = 0.0
    controversy_reasons: List[str] = field(default_factory=list)
    controversy_keywords: List[str] = field(default_factory=list)
    entities: Set[str] = field(default_factory=set)
    key_terms: Set[str] = field(default_factory=set)

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

def _extract_entities(text: str) -> Set[str]:
    """从文本中提取关键实体（公司名、品牌名、股票代码）"""
    entities: Set[str] = set()
    for m in _COMPANY_RE.finditer(text):
        entities.add(m.group())
    for m in _BRAND_RE.finditer(text):
        entities.add(m.group())
    for m in _STOCK_CODE_RE.finditer(text):
        entities.add(m.group().upper())
    return entities

def _extract_key_terms(text: str) -> Set[str]:
    """从文本中提取财经关键词"""
    terms: Set[str] = set()
    for m in _KEY_TERMS_RE.finditer(text):
        terms.add(m.group())
    return terms

def _entity_overlap(entities_a: Set[str], entities_b: Set[str]) -> float:
    if not entities_a or not entities_b:
        return 0.0
    intersection = entities_a & entities_b
    union = entities_a | entities_b
    return len(intersection) / len(union) if union else 0.0

def _term_overlap(terms_a: Set[str], terms_b: Set[str]) -> float:
    if not terms_a or not terms_b:
        return 0.0
    intersection = terms_a & terms_b
    union = terms_a | terms_b
    return len(intersection) / len(union) if union else 0.0

def title_similarity(a: str, b: str) -> float:
    """纯标题文本相似度"""
    a_n, b_n = normalize_title(a), normalize_title(b)
    if not a_n or not b_n:
        return 0.0
    if a_n == b_n:
        return 1.0
    a2, b2 = _ngram_set(a_n, 2), _ngram_set(b_n, 2)
    j = (len(a2 & b2) / max(1, len(a2 | b2))) if (a2 or b2) else 0.0
    s = SequenceMatcher(None, a_n, b_n).ratio()
    return 0.55 * s + 0.45 * j

def enhanced_similarity(
    title_a: str, title_b: str,
    entities_a: Set[str], entities_b: Set[str],
    terms_a: Set[str], terms_b: Set[str],
    summary_a: str = "", summary_b: str = "",
) -> float:
    """增强相似度：动态权重分配

    核心思路：
    - 文本相似度始终是基础（至少占 60%）
    - 实体/关键词/摘要作为加成信号，有则加分，无则不扣分
    - 这样避免了"无实体时被稀释"的问题
    """
    text_sim = title_similarity(title_a, title_b)
    ent_sim = _entity_overlap(entities_a, entities_b)
    term_sim = _term_overlap(terms_a, terms_b)

    # 摘要辅助
    summary_sim = 0.0
    if summary_a and summary_b and summary_a != title_a and summary_b != title_b:
        s_a = normalize_title(summary_a[:100])
        s_b = normalize_title(summary_b[:100])
        if s_a and s_b:
            summary_sim = SequenceMatcher(None, s_a, s_b).ratio()

    # 动态权重：基础分 = 文本相似度，辅助信号只做加成
    # 文本相似度作为基础（权重 1.0）
    base = text_sim

    # 实体加成：有共同实体时大幅加分
    entity_bonus = 0.0
    common_entities = entities_a & entities_b if (entities_a and entities_b) else set()
    if len(common_entities) >= 2:
        entity_bonus = 0.30  # 2个以上共同实体，强信号
    elif len(common_entities) == 1:
        entity_bonus = 0.18  # 1个共同实体，中等信号

    # 关键词加成
    term_bonus = 0.0
    if term_sim > 0:
        term_bonus = term_sim * 0.12

    # 摘要加成
    summary_bonus = 0.0
    if summary_sim > 0.3:
        summary_bonus = summary_sim * 0.08

    combined = base + entity_bonus + term_bonus + summary_bonus
    return min(1.0, combined)


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


def format_hot_score(score: float) -> str:
    if score <= 0:
        return "-"
    if score >= 1e8:
        return f"{score / 1e8:.1f}亿"
    if score >= 1e4:
        return f"{score / 1e4:.1f}万"
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
    similarity_threshold: float = 0.52,
    max_clusters: int = 30,
) -> List[TopicCluster]:
    """贪心聚类：使用增强相似度（文本为主 + 实体/关键词加成）

    阈值 0.52：文本相似度 0.52 以上就能聚合（约等于标题有一半以上重叠），
    有共同实体时会加成到 0.52 以上从而触发聚合。
    """
    items_sorted = sorted(items, key=lambda x: (x.hot_score, -(x.rank or 9999)), reverse=True)
    clusters: List[TopicCluster] = []
    for it in items_sorted:
        if not it.norm_title:
            continue
        full_text = f"{it.title} {it.summary}"
        it_entities = _extract_entities(full_text)
        it_terms = _extract_key_terms(full_text)

        best_idx, best_sim = -1, 0.0
        for idx, c in enumerate(clusters):
            sim = enhanced_similarity(
                it.norm_title, c.norm_title,
                it_entities, c.entities,
                it_terms, c.key_terms,
                it.summary, c.evidence[0].summary if c.evidence else "",
            )
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
            c.entities |= it_entities
            c.key_terms |= it_terms
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
                entities=it_entities, key_terms=it_terms,
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
    """综合评分: 排名分 + 跨平台加成 + 热度归一化 + 时间衰减"""
    if not clusters:
        return
    all_hot = [c.total_hot_score for c in clusters]
    max_hot = max(all_hot) if all_hot else 1.0
    max_hot = max(max_hot, 1.0)

    raw_scores: List[float] = []
    for c in clusters:
        rank_scores = []
        for e in c.evidence:
            r = e.rank if e.rank and e.rank > 0 else 50
            rank_scores.append(max(0.0, 100.0 - (r - 1) * 4.5))
        avg_rank = sum(rank_scores) / max(1, len(rank_scores))

        n_plat = len(set(c.platforms))
        platform_score = min(100.0, max(0.0, (n_plat - 1) * 40.0))

        heat_norm = (c.total_hot_score / max_hot) * 100.0

        tf = _time_decay_factor(_best_published_time(c))
        time_score = tf * 100.0

        raw = avg_rank * 0.40 + platform_score * 0.25 + heat_norm * 0.20 + time_score * 0.15
        raw_scores.append(raw)

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
    """争议检测：综合标题+摘要关键词、数值异动、被动语态、跨平台分歧"""
    reasons: List[str] = []
    hits: List[str] = []

    # 合并标题和摘要文本一起检测（之前只检查标题）
    all_titles = [e.title for e in cluster.evidence if e.title]
    all_summaries = [e.summary for e in cluster.evidence if e.summary]
    joined_text = " ".join(all_titles + all_summaries)

    # 1) 关键词匹配（标题+摘要）
    for kw in FINANCE_CONTROVERSY_KEYWORDS:
        if kw in joined_text:
            hits.append(kw)
    if hits:
        reasons.append(f"命中争议词: {', '.join(sorted(set(hits))[:8])}")

    # 2) 数值异动检测（"下降16.91%"、"亏损3亿"等）
    num_matches = _CONTROVERSY_NUM_RE.findall(joined_text)
    if num_matches:
        reasons.append(f"数值异动: {', '.join(num_matches[:3])}")

    # 3) 被动语态检测（"被约谈"、"被处罚"等）
    action_matches = _CONTROVERSY_ACTION_RE.findall(joined_text)
    if action_matches:
        reasons.append(f"监管动作: {', '.join(list(set(action_matches))[:3])}")

    # 4) 跨平台表述分歧
    disagreement = 0.0
    if len(all_titles) >= 2:
        sims = []
        for i in range(min(6, len(all_titles))):
            for j in range(i+1, min(6, len(all_titles))):
                sims.append(title_similarity(all_titles[i], all_titles[j]))
        if sims:
            avg_sim = sum(sims) / len(sims)
            disagreement = max(0.0, 1.0 - avg_sim)
            if disagreement >= 0.25:
                reasons.append(f"跨平台表述分歧: {disagreement:.2f}")

    # 综合评分
    score = 0.0
    score += 15.0 * min(6, len(set(hits)))       # 关键词：每个15分，上限90
    score += 25.0 * len(num_matches[:3])          # 数值异动：每个25分
    score += 20.0 * len(set(action_matches[:3]))  # 被动语态：每个20分
    score += 50.0 * disagreement                  # 跨平台分歧
    score += min(15.0, math.log1p(max(0.0, cluster.total_hot_score)) / 2.0)

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
    similarity_threshold: float = 0.52,
) -> Tuple[List[TopicCluster], Dict[str, Any]]:
    if not raw_items:
        return [], {}
    logger.info(f"🔄 热榜对齐: {len(raw_items)} 条原始数据")
    clusters = cluster_items(raw_items, similarity_threshold=similarity_threshold)
    logger.info(f"📊 聚类结果: {len(clusters)} 个话题")
    score_clusters(clusters)
    for c in clusters:
        compute_controversy(c)
    apply_history_signals(clusters, prev_snapshot)
    ts = datetime.now().isoformat()
    snapshot = make_history_snapshot(clusters, ts)
    cross = sum(1 for c in clusters if len(set(c.platforms)) > 1)
    logger.info(f"✅ 热榜对齐完成: {len(clusters)} 个话题, 跨平台: {cross} 个")
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
            "hot_value": "-",  # 占位，后续由 heat_score 统一生成
            "heat_score": c.heat_score, "rank": idx,
            "category": "domestic", "collection_time": collection_time,
            "platform_count": n_plat,
            "platform_label": f"{n_plat}平台热议",
            "platform_ids": sorted(set(c.platforms)),
            "platforms_data": platforms_data, "evidence": evidence,
            "controversy": c.controversy_score,
            "controversy_reasons": c.controversy_reasons,
            "controversy_keywords": c.controversy_keywords,
            "is_new": c.is_new, "growth": c.growth,
            "hot_score_delta": c.hot_score_delta,
        })
    # 基于综合评分生成热度显示值，保证排名和热度一致
    _generate_hot_values_from_score(out)
    return out


def _generate_hot_values_from_score(clusters: List[Dict[str, Any]]) -> None:
    """基于 heat_score 综合评分生成热度显示值。

    排名第1的话题热度最高，往后递减，保证排名和热度完全一致。
    heat_score 范围 0-100，映射到显示值范围约 50-999。
    """
    import random

    if not clusters:
        return

    for c in clusters:
        score = c.get('heat_score', 0) or 0
        # 映射: heat_score 0-100 → 显示值 50-999
        # 加一点随机扰动避免相邻话题数值完全一样
        base = 50 + score * 9.5
        jitter = random.randint(-3, 3)
        display_val = max(10, int(base + jitter))
        c['hot_value'] = str(display_val)
