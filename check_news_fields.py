#!/usr/bin/env python3
"""直接查看全榜第一条新闻的完整字段"""

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
    first_news = data['news_by_platform'][first_platform][0]
    
    print(f"第一个平台: {first_platform}")
    print(f"第一条新闻的所有字段:")
    print(json.dumps(first_news, indent=2, ensure_ascii=False))
