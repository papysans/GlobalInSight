#!/usr/bin/env python3
"""检查URL字段是否存在"""

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
    
    # 查看前3条新闻的URL
    print(f"\n{first_platform} 前3条新闻的URL:\n")
    for i, news in enumerate(data['news_by_platform'][first_platform][:3], 1):
        url_field = news.get('url', '')
        print(f"新闻 #{i}:")
        print(f"  URL: {url_field[:60]}...")
        
        # 检查URL中的域名
        if 'zhihu' in url_field:
            print(f"  → 识别为: 知乎")
        elif 'weibo' in url_field:
            print(f"  → 识别为: 微博")
        elif 'bilibili' in url_field:
            print(f"  → 识别为: B站")
        elif 'douyin' in url_field:
            print(f"  → 识别为: 抖音")
        else:
            print(f"  → 识别为: 其他")
        print()
