#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取同花顺首页headlineList - 简单转义处理"""
import httpx
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

# 找到headlineList
idx = html.find('headlineList')
bracket_start = html.find('[', idx)

# 匹配括号
depth = 0
end = bracket_start
i = bracket_start
while i < len(html):
    c = html[i]
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

# 只做 \\" -> " 替换，不做unicode_escape
cleaned = raw.replace('\\"', '"')
# 处理 \\u0026 等 -> 先还原为 \u0026
cleaned = cleaned.replace('\\\\u', '\\u')
# 处理 \/ -> /
cleaned = cleaned.replace('\\/', '/')

# 尝试找到控制字符并清理
import re
cleaned = re.sub(r'[\x00-\x1f]', '', cleaned)

try:
    headline_list = json.loads(cleaned)
    print(f"✅ headlineList: {len(headline_list)} 条头条新闻\n")
    for i, item in enumerate(headline_list):
        title = item.get('title', '')
        source = item.get('source', '')
        url = item.get('url', '')
        ctime = item.get('ctime', 0)
        time_str = datetime.fromtimestamp(ctime).strftime('%H:%M') if ctime else ''
        print(f"{i+1}. [{source}] {title}")
        print(f"   {url}  ({time_str})")
        print()
except json.JSONDecodeError as e:
    print(f"JSON解析失败: {e}")
    # 找到出错位置附近的内容
    pos = e.pos if hasattr(e, 'pos') else 0
    print(f"出错位置附近: {repr(cleaned[max(0,pos-50):pos+50])}")
