#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取同花顺首页headlineList - 修复JSON解析"""
import httpx
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
    r = client.get("https://www.10jqka.com.cn/")
    html = r.text

# 直接在原始HTML中搜索headlineList（不做反转义，保持原始JSON格式）
# RSC数据中的JSON是双重转义的：\" 表示 "
m = re.search(r'\\?"headlineList\\?":\s*(\[(?:[^]]*?\{[^}]*?\}[^]]*?)*\])', html)
if not m:
    # 尝试另一种方式：找到headlineList后提取到匹配的]
    idx = html.find('"headlineList"')
    if idx < 0:
        idx = html.find('\\"headlineList\\"')
    if idx >= 0:
        # 从[开始，找到匹配的]
        start = html.index('[', idx)
        depth = 0
        end = start
        for j in range(start, min(start + 50000, len(html))):
            c = html[j]
            if c == '[': depth += 1
            elif c == ']': depth -= 1
            if depth == 0:
                end = j + 1
                break
        raw_json = html[start:end]
        # 处理转义
        raw_json = raw_json.replace('\\"', '"').replace('\\\\', '\\')
        try:
            headline_list = json.loads(raw_json)
            print(f"headlineList: {len(headline_list)} 条头条新闻\n")
            for i, item in enumerate(headline_list[:20]):
                title = item.get('title', '')
                source = item.get('source', '')
                url = item.get('url', '')
                ctime = item.get('ctime', 0)
                from datetime import datetime
                time_str = datetime.fromtimestamp(ctime).strftime('%H:%M') if ctime else ''
                print(f"{i+1}. [{source}] {title}")
                print(f"   URL: {url}")
                print(f"   时间: {time_str}")
                print(f"   字段: {list(item.keys())}")
                print()
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"前500字符: {raw_json[:500]}")
    else:
        print("未找到headlineList")
