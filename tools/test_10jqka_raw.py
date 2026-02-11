#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接查看同花顺首页HTML中headlineList的原始格式"""
import httpx

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
    r = client.get("https://www.10jqka.com.cn/")
    html = r.text

idx = html.find('headlineList')
if idx >= 0:
    # 打印前后各2000字符看看格式
    start = max(0, idx - 50)
    end = min(len(html), idx + 3000)
    snippet = html[start:end]
    print(f"headlineList 位置: {idx}")
    print(f"上下文:\n{repr(snippet[:200])}")
    print("---")
    # 找到 [ 开始
    bracket_start = html.find('[', idx)
    print(f"\n[ 位置: {bracket_start}")
    print(f"原始字节: {repr(html[bracket_start:bracket_start+500])}")
else:
    print("未找到 headlineList")
