#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试聚类结果：查看各平台标题样本 + 跨平台匹配情况"""
import json

with open("cache/hot_news_stock_hot_aligned_2026-02-11.json", "r", encoding="utf-8") as f:
    data = json.load(f)

clusters = data["clusters"]
print(f"=== 聚类结果: {len(clusters)} 个话题 ===\n")

for i, c in enumerate(clusters[:10]):
    pids = c["platform_ids"]
    pcount = c["platform_count"]
    title = c["title"]
    print(f"{i+1}. [{pcount}平台: {','.join(pids)}] {title[:80]}")
    for ev in c["evidence"][:3]:
        print(f"   - [{ev['platform_id']}] {ev['title'][:70]}")
    print()

# 查看各平台的标题样本
print("\n=== 各平台标题样本 ===")
by_platform = {}
for c in clusters:
    for ev in c["evidence"]:
        pid = ev["platform_id"]
        if pid not in by_platform:
            by_platform[pid] = []
        by_platform[pid].append(ev["title"][:60])

for pid, titles in by_platform.items():
    print(f"\n--- {pid} ({len(titles)} 条) ---")
    for t in titles[:5]:
        print(f"  {t}")
