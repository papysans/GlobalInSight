#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""优化争议检测：扩充关键词 + 检查摘要 + 数值异动检测"""
import re

TARGET = "app/services/hotnews_alignment.py"

with open(TARGET, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 替换 FINANCE_CONTROVERSY_KEYWORDS
old_keywords = '''FINANCE_CONTROVERSY_KEYWORDS = [
    "暴雷","退市","爆仓","跌停","利空","做空","暴跌",
    "违规","处罚","罚款","造假","财务造假","内幕交易",
    "减持","清仓","质押","爆雷","亏损","破产",
    "监管","调查","立案","警示","风险","ST",
    "崩盘","割韭菜","闪崩","黑天鹅","踩雷",
    "诉讼","仲裁","违约","欺诈",
]'''

new_keywords = '''FINANCE_CONTROVERSY_KEYWORDS = [
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
)'''

content = content.replace(old_keywords, new_keywords)

# 2. 替换 compute_controversy 函数
old_func = '''def compute_controversy(cluster: TopicCluster) -> None:
    reasons: List[str] = []
    hits: List[str] = []
    joined = " ".join(e.title for e in cluster.evidence if e.title)
    for kw in FINANCE_CONTROVERSY_KEYWORDS:
        if kw in joined:
            hits.append(kw)
    if hits:
        reasons.append(f"命中争议词: {', '.join(sorted(set(hits))[:6])}")
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
                reasons.append(f"跨平台表述分歧: {disagreement:.2f}")
    score = 18.0 * len(set(hits)) + 60.0 * disagreement
    score += min(20.0, math.log1p(max(0.0, cluster.total_hot_score)) / 2.0)
    cluster.controversy_score = round(max(0.0, min(100.0, score)), 1)
    cluster.controversy_reasons = reasons
    cluster.controversy_keywords = sorted(set(hits))'''

new_func = '''def compute_controversy(cluster: TopicCluster) -> None:
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
        reasons.append(f"监管动作: {', '.join(set(action_matches)[:3])}")

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
    cluster.controversy_keywords = sorted(set(hits))'''

content = content.replace(old_func, new_func)

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 争议检测已优化，文件大小: {len(content)} 字符")

# 验证替换是否成功
if "_CONTROVERSY_NUM_RE" in content and "数值异动检测" in content:
    print("✅ 验证通过：新的争议检测逻辑已写入")
else:
    print("❌ 验证失败：替换可能不完整")
