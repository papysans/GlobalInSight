#!/usr/bin/env python3
"""测试热榜聚类接口"""
import httpx
import json

resp = httpx.get("http://localhost:8000/api/stock/hot?force_refresh=true", timeout=90.0)
data = resp.json()
clusters = data.get("clusters", [])
print(f"总话题数: {len(clusters)}")
print(f"跨平台: {data.get('cross_platform_count', 0)}")
print(f"原始数据: {data.get('raw_count', 0)}")
print(f"数据源: {json.dumps(data.get('source_stats', {}), ensure_ascii=False)}")
print()
for i, c in enumerate(clusters[:15]):
    title = c.get("title", "")
    summary = c.get("summary", "")[:100]
    platforms = c.get("platform_ids", [])
    heat = c.get("heat_score", 0)
    hot = c.get("hot_value", "")
    pcount = c.get("platform_count", 1)
    print(f"{i+1}. [{heat}分] {title}")
    print(f"   平台({pcount}): {platforms} | 热度: {hot}")
    if summary and summary != title:
        print(f"   摘要: {summary}")
    print()
