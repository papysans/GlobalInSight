#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查热榜API返回的hot_value"""
import httpx

r = httpx.get("http://localhost:8000/api/stock/hot?force_refresh=true", timeout=60)
d = r.json()
for c in d["clusters"]:
    rank = c["rank"]
    hv = c["hot_value"]
    title = c["title"][:50]
    marker = "⚠️" if (not hv or hv == "-") else "✓"
    print(f"{marker} {rank}. [{hv}] {title}")
