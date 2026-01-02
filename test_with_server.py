#!/usr/bin/env python3
"""启动后端服务器用于测试"""

import subprocess
import time
import requests
import json

# 启动后端服务器
print("启动后端服务器...")
server_process = subprocess.Popen([
    ".venv/Scripts/python.exe",
    "-m", "app.main"
], cwd="d:\\For Study\\Project\\AgentPro")

# 等待服务器启动
time.sleep(5)

print("\n测试全榜平台提取...")

try:
    resp = requests.post('http://127.0.0.1:8000/api/hot-news/collect', json={
        'platforms': ['all'],
        'force_refresh': True
    }, timeout=60)
    
    data = resp.json()
    
    if data['news_by_platform']:
        first_platform = list(data['news_by_platform'].keys())[0]
        first_news = data['news_by_platform'][first_platform][0]
        
        print(f"\n第一个平台: {first_platform}")
        print(f"第一条新闻:")
        print(f"  title: {first_news.get('title')[:50]}...")
        print(f"  platform: {first_news.get('platform')}")
        print(f"  所有字段: {list(first_news.keys())}")
        
except Exception as e:
    print(f"Error: {e}")

finally:
    # 关闭服务器
    print("\n关闭后端服务器...")
    server_process.terminate()
    server_process.wait()
