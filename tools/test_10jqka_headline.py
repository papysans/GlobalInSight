#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取同花顺首页headlineList头条新闻"""
import httpx
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
    r = client.get("https://www.10jqka.com.cn/")
    html = r.text

# 提取所有RSC数据块并合并
chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
all_text = "".join(chunks)

# 反转义
all_text = all_text.replace('\\"', '"').replace('\\\\', '\\')

# 提取 headlineList
m = re.search(r'"headlineList":(\[.*?\])\s*[,}]', all_text)
if m:
    try:
        headline_list = json.loads(m.group(1))
        print(f"headlineList: {len(headline_list)} 条头条新闻\n")
        for i, item in enumerate(headline_list[:20]):
            title = item.get('title', '')
            source = item.get('source', '')
            url = item.get('url', '')
            ctime = item.get('ctime', '')
            pic = item.get('picUrl', '')
            sort_score = item.get('sortScore', '')
            print(f"{i+1}. [{source}] {title}")
            print(f"   URL: {url}")
            print(f"   时间戳: {ctime}, 排序分: {sort_score}")
            print(f"   keys: {list(item.keys())}")
            print()
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        # 打印原始数据
        raw = m.group(1)[:2000]
        print(f"原始: {raw}")
else:
    print("未找到 headlineList")
    # 尝试更宽松的匹配
    idx = all_text.find('headlineList')
    if idx >= 0:
        print(f"headlineList 位置: {idx}")
        print(all_text[idx:idx+1000])
