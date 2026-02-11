#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试争议检测：查看当前热榜的争议分数分布"""
import json

with open("cache/hot_news_stock_hot_aligned_2026-02-11.json", "r", encoding="utf-8") as f:
    data = json.load(f)

clusters = data["clusters"]
print(f"=== 争议检测分析（共 {len(clusters)} 个话题）===\n")

# 按争议分排序
sorted_c = sorted(clusters, key=lambda x: x.get("controversy", 0), reverse=True)

for i, c in enumerate(sorted_c):
    score = c.get("controversy", 0)
    reasons = c.get("controversy_reasons", [])
    keywords = c.get("controversy_keywords", [])
    title = c["title"][:60]
    pcount = c["platform_count"]
    
    # 也看看标题和摘要中有没有潜在争议内容
    evidence_titles = [e["title"] for e in c.get("evidence", [])]
    evidence_summaries = [e.get("summary", "") for e in c.get("evidence", [])]
    all_text = " ".join(evidence_titles + evidence_summaries)
    
    marker = "🔴" if score >= 30 else "🟡" if score >= 10 else "⚪"
    print(f"{marker} {i+1}. [{score:.1f}分] {title}")
    if reasons:
        print(f"   原因: {'; '.join(reasons)}")
    if keywords:
        print(f"   关键词: {', '.join(keywords)}")
    print(f"   [{pcount}平台] 标题: {'; '.join(t[:40] for t in evidence_titles[:3])}")
    # 检查摘要中是否有争议信号
    summary_preview = evidence_summaries[0][:80] if evidence_summaries and evidence_summaries[0] else ""
    if summary_preview:
        print(f"   摘要: {summary_preview}")
    print()
