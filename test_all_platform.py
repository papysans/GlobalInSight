#!/usr/bin/env python3
"""测试全榜平台数据返回"""

import requests
import json

def test_all_platforms():
    """测试全榜请求"""
    url = 'http://127.0.0.1:8000/api/hot-news/collect'
    
    # 测试1: 全榜请求 (platforms=['all'])
    print("=" * 60)
    print("测试1: 全榜请求 (platforms=['all'])")
    print("=" * 60)
    
    resp = requests.post(url, json={
        'platforms': ['all'],
        'force_refresh': False
    })
    
    if resp.status_code != 200:
        print(f"ERROR: 状态码 {resp.status_code}")
        print(resp.text)
        return
    
    data = resp.json()
    print(f"success: {data['success']}")
    print(f"total_news: {data['total_news']}")
    print(f"successful_sources: {data['successful_sources']}")
    print(f"news_by_platform 平台数: {len(data['news_by_platform'])}")
    print(f"平台列表: {list(data['news_by_platform'].keys())}")
    print()
    
    # 显示每个平台的新闻数
    for platform, news_list in data['news_by_platform'].items():
        print(f"  {platform}: {len(news_list)} 条新闻")
    print()
    
    # 显示第一个平台的第一条新闻详情
    if data['news_by_platform']:
        first_platform = list(data['news_by_platform'].keys())[0]
        first_news = data['news_by_platform'][first_platform][0]
        print(f"第一个平台 ({first_platform}) 的第一条新闻:")
        print(f"  rank: {first_news.get('rank')}")
        print(f"  title: {first_news.get('title')[:50]}...")
        print(f"  hot_value: {first_news.get('hot_value')}")
        print(f"  source: {first_news.get('source')}")
        print(f"  platform: {first_news.get('platform')}")
        print(f"  source_id: {first_news.get('source_id')}")
    
    print()
    print("=" * 60)
    print("测试2: 单个平台请求 (platforms=['weibo'])")
    print("=" * 60)
    
    resp2 = requests.post(url, json={
        'platforms': ['weibo'],
        'force_refresh': False
    })
    
    data2 = resp2.json()
    print(f"success: {data2['success']}")
    print(f"total_news: {data2['total_news']}")
    print(f"news_by_platform 平台数: {len(data2['news_by_platform'])}")
    print(f"平台列表: {list(data2['news_by_platform'].keys())}")
    
    for platform, news_list in data2['news_by_platform'].items():
        print(f"  {platform}: {len(news_list)} 条新闻")

if __name__ == '__main__':
    test_all_platforms()
