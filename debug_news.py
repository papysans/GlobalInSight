#!/usr/bin/env python3
"""直接查看后端返回的原始数据"""

import requests
import json

url = 'http://127.0.0.1:8000/api/hot-news/collect'

resp = requests.post(url, json={
    'platforms': ['all'],
    'force_refresh': True
})

data = resp.json()

if data['news_by_platform']:
    first_platform = list(data['news_by_platform'].keys())[0]
    
    # 查看前5条新闻
    print(f"\n{first_platform} 前5条新闻:\n")
    for i, news in enumerate(data['news_by_platform'][first_platform][:5], 1):
        print(f"新闻 #{i}:")
        print(f"  rank: {news.get('rank')}")
        print(f"  title: {news.get('title')[:40]}...")
        print(f"  hot_value: {news.get('hot_value')}")
        print(f"  platform: {news.get('platform')}")
        print(f"  source: {news.get('source')}")
        print(f"  所有字段: {list(news.keys())}")
        print()
