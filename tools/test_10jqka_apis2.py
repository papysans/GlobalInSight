#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测同花顺首页头条新闻API - 第二轮"""
import httpx
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://www.10jqka.com.cn/',
    'Accept': 'application/json, text/plain, */*',
}

test_urls = [
    # Next.js SSR数据接口
    ("nextjs_data", "https://www.10jqka.com.cn/_next/data/build-id/index.json"),
    # 新闻流API - 不同路径
    ("news_flow_v1", "https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=-10000&track=website&num=20&stamp="),
    ("news_headline", "https://news.10jqka.com.cn/tapp/news/push/headline/?page=1&tag=-10000&track=website&num=20"),
    # 可能的GraphQL或REST API
    ("news_list_api", "https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=toutiao&track=website&num=20"),
    # 同花顺新版首页可能的API
    ("home_news", "https://news.10jqka.com.cn/home/news/list?page=1&pageSize=20&channel=toutiao"),
    ("home_flow", "https://news.10jqka.com.cn/home/flow?page=1&pageSize=20"),
    # 财经头条
    ("cj_headline", "https://news.10jqka.com.cn/cjzx_list/index_1.shtml"),
    # 同花顺圈子热门
    ("field_hot", "https://field.10jqka.com.cn/internal/hot/list"),
    # 同花顺热榜
    ("hot_rank", "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock?stock_type=a&type=hour&list_type=normal"),
]

with httpx.Client(timeout=10, headers=headers, follow_redirects=True) as client:
    for name, url in test_urls:
        try:
            r = client.get(url)
            ct = r.headers.get('content-type', '')
            text = r.text[:3000]
            print(f"\n{'='*60}")
            print(f"[{name}] status={r.status_code} ct={ct[:50]}")
            
            if r.status_code == 200:
                if 'json' in ct or text.strip().startswith('{') or text.strip().startswith('['):
                    try:
                        d = r.json()
                        print(f"  JSON keys: {list(d.keys()) if isinstance(d, dict) else 'array'}")
                        if isinstance(d, dict):
                            data = d.get('data', d)
                            if isinstance(data, dict):
                                print(f"  data keys: {list(data.keys())[:10]}")
                                items = data.get('list', data.get('items', data.get('stock_list', [])))
                                if items and isinstance(items, list):
                                    print(f"  条数: {len(items)}")
                                    for it in items[:3]:
                                        if isinstance(it, dict):
                                            print(f"    keys: {list(it.keys())[:10]}")
                                            name_val = it.get('title', it.get('name', it.get('stock_name', '')))[:60]
                                            print(f"    -> {name_val}")
                            elif isinstance(data, list) and data:
                                print(f"  data是数组, 条数: {len(data)}")
                                print(f"    keys: {list(data[0].keys())[:10]}")
                        print(f"  原始: {json.dumps(d, ensure_ascii=False)[:400]}")
                    except:
                        print(f"  非JSON: {text[:300]}")
                elif 'html' in ct:
                    # 检查是否有新闻内容
                    if 'class="list-con"' in text or 'newslist' in text.lower():
                        print(f"  HTML含新闻列表")
                    print(f"  HTML: {text[:200]}")
                else:
                    print(f"  其他: {text[:200]}")
            else:
                print(f"  {text[:200]}")
        except Exception as e:
            print(f"[{name}] 失败: {e}")
