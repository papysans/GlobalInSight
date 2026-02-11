#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取同花顺首页headlineList - 处理双重转义"""
import httpx
import re
import json
from datetime import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
    r = client.get("https://www.10jqka.com.cn/")
    html = r.text

# 找到headlineList的起始位置
idx = html.find('headlineList')
if idx < 0:
    print("未找到headlineList")
    exit()

# 找到 [ 开始位置
bracket_start = html.find('[', idx)

# 手动匹配括号，处理转义的括号
depth = 0
end = bracket_start
i = bracket_start
while i < len(html):
    c = html[i]
    # 跳过转义字符
    if c == '\\' and i + 1 < len(html):
        i += 2
        continue
    if c == '[':
        depth += 1
    elif c == ']':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
    i += 1

raw = html[bracket_start:end]
print(f"原始数据长度: {len(raw)} 字符")

# 处理双重转义: \\" -> "  \\u0026 -> &
cleaned = raw.replace('\\"', '"').replace('\\\\', '\\')
# 处理unicode转义
cleaned = cleaned.encode().decode('unicode_escape', errors='replace')

try:
    headline_list = json.loads(cleaned)
    print(f"✅ headlineList: {len(headline_list)} 条头条新闻\n")
    for i, item in enumerate(headline_list):
        title = item.get('title', '')
        source = item.get('source', '')
        url = item.get('url', '')
        ctime = item.get('ctime', 0)
        time_str = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M') if ctime else ''
        ai_summary = item.get('aiSummary', '')
        print(f"{i+1}. [{source}] {title}")
        print(f"   URL: {url}")
        print(f"   时间: {time_str}")
        if ai_summary:
            print(f"   AI摘要: {ai_summary[:80]}")
        print()
except json.JSONDecodeError as e:
    print(f"JSON解析失败: {e}")
    print(f"清理后前500: {cleaned[:500]}")
