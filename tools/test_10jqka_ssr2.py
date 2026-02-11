#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从同花顺首页RSC数据中提取头条新闻"""
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

# 提取所有 self.__next_f.push 数据块
chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
print(f"找到 {len(chunks)} 个RSC数据块")

# 合并所有块，搜索新闻数据
all_text = "\n".join(chunks)

# 查找包含新闻标题的数据块
# 同花顺头条新闻的特征：有title, source, ctime/time, url等字段
news_pattern = re.compile(r'"title":"([^"]{10,80})".*?"source":"([^"]*)"', re.DOTALL)
matches = news_pattern.findall(all_text[:50000])
if matches:
    print(f"\n找到 {len(matches)} 条标题+来源:")
    for title, source in matches[:10]:
        print(f"  [{source}] {title}")

# 更精确地找新闻列表数据
# 查找包含 articleId 或 newsId 的JSON结构
for i, chunk in enumerate(chunks):
    # 反转义
    try:
        unescaped = chunk.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')
    except:
        unescaped = chunk
    
    if ('articleId' in unescaped or 'newsId' in unescaped or 
        '"ctime"' in unescaped or '"digest"' in unescaped):
        print(f"\n=== 数据块 {i} (含新闻字段) ===")
        print(unescaped[:800])
        print("...")

# 也查找 initialNewsList 或类似的初始数据
for keyword in ['initialNewsList', 'newsList', 'articleList', 'headlineList', 'flowList', 'newsData']:
    if keyword in all_text:
        idx = all_text.index(keyword)
        print(f"\n找到 '{keyword}' 在位置 {idx}:")
        print(all_text[idx:idx+500])
