#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从同花顺首页SSR HTML中提取头条新闻数据"""
import httpx
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
    r = client.get("https://www.10jqka.com.cn/")
    html = r.text
    print(f"页面大小: {len(html)} 字符")
    
    # Next.js SSR 通常把数据放在 __NEXT_DATA__ script标签里
    m = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>', html, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        print(f"找到 __NEXT_DATA__!")
        print(f"顶层keys: {list(data.keys())}")
        props = data.get('props', {}).get('pageProps', {})
        print(f"pageProps keys: {list(props.keys())[:15]}")
        
        # 遍历pageProps找新闻列表
        for k, v in props.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                sample = v[0]
                if 'title' in sample or 'headline' in sample:
                    print(f"\n=== {k}: {len(v)} 条 ===")
                    for item in v[:5]:
                        title = item.get('title', item.get('headline', ''))[:60]
                        src = item.get('source', item.get('media', ''))
                        digest = item.get('digest', item.get('summary', item.get('brief', '')))[:50]
                        url = item.get('url', item.get('link', ''))
                        print(f"  [{src}] {title}")
                        if digest:
                            print(f"    摘要: {digest}")
                        if url:
                            print(f"    URL: {url}")
                        print(f"    keys: {list(item.keys())[:12]}")
            elif isinstance(v, dict):
                # 可能嵌套了一层
                for k2, v2 in v.items():
                    if isinstance(v2, list) and v2 and isinstance(v2[0], dict):
                        sample = v2[0]
                        if 'title' in sample or 'headline' in sample:
                            print(f"\n=== {k}.{k2}: {len(v2)} 条 ===")
                            for item in v2[:3]:
                                title = item.get('title', '')[:60]
                                src = item.get('source', '')
                                print(f"  [{src}] {title}")
                                print(f"    keys: {list(item.keys())[:12]}")
    else:
        print("未找到 __NEXT_DATA__")
        # 尝试其他方式
        # 查找JSON数据块
        json_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for i, block in enumerate(json_blocks):
            if 'title' in block and ('news' in block.lower() or 'article' in block.lower()):
                print(f"\nScript块 {i}: {block[:300]}")
