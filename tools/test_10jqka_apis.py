#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测同花顺首页头条新闻API"""
import httpx
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://www.10jqka.com.cn/',
    'Accept': 'application/json, text/plain, */*',
}

# 尝试不同的tag参数
test_urls = [
    ("stock默认", "https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=-10000&track=website&num=20"),
    ("stock_tag0", "https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=0&track=website&num=20"),
    ("stock_tag-1", "https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=-1&track=website&num=20"),
    ("头条频道", "https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=-10001&track=website&num=20"),
    # 新版首页API
    ("首页新闻流v2", "https://news.10jqka.com.cn/api/news/home/flow?page=1&pageSize=20&tag=toutiao"),
    ("首页新闻流v3", "https://news.10jqka.com.cn/api/news/home/flow?page=1&pageSize=20"),
    # 热点排行
    ("热点排行", "https://eq.10jqka.com.cn/open/api/hot_list/v1/hot_stock/concept/data?type=day"),
    # 要闻
    ("要闻", "https://news.10jqka.com.cn/tapp/news/push/important/?page=1&tag=-10000&track=website&num=20"),
]

with httpx.Client(timeout=10, headers=headers, follow_redirects=True) as client:
    for name, url in test_urls:
        try:
            r = client.get(url)
            ct = r.headers.get('content-type', '')
            text = r.text[:2000]
            print(f"\n{'='*60}")
            print(f"[{name}] status={r.status_code} content-type={ct[:50]}")
            
            if 'json' in ct or text.startswith('{') or text.startswith('['):
                try:
                    d = r.json()
                    # 尝试不同的数据结构
                    items = None
                    if isinstance(d, dict):
                        items = d.get('data', {})
                        if isinstance(items, dict):
                            items = items.get('list', items.get('items', items.get('data', [])))
                        elif isinstance(items, list):
                            pass
                        else:
                            items = []
                    
                    if items and isinstance(items, list):
                        print(f"  数据条数: {len(items)}")
                        for it in items[:5]:
                            if isinstance(it, dict):
                                title = it.get('title', it.get('name', ''))[:60]
                                src = it.get('source', it.get('media', ''))
                                digest = it.get('digest', it.get('summary', ''))[:40]
                                print(f"  [{src}] {title}")
                                if digest and digest != title[:40]:
                                    print(f"       摘要: {digest}")
                    else:
                        # 打印原始结构
                        print(f"  结构: {json.dumps(d, ensure_ascii=False)[:500]}")
                except:
                    print(f"  非JSON: {text[:300]}")
            else:
                print(f"  响应: {text[:300]}")
        except Exception as e:
            print(f"[{name}] 失败: {e}")
