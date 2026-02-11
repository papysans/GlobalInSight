#!/usr/bin/env python3
"""检查 AKShare stock_news_em 的数据结构"""
import akshare as ak

df = ak.stock_news_em()
print(f"列名: {list(df.columns)}")
print(f"总行数: {len(df)}")
print()

for idx, row in df.head(8).iterrows():
    title = str(row.get("新闻标题", row.get("title", ""))).strip()
    content = str(row.get("新闻内容", row.get("content", ""))).strip()
    source = str(row.get("文章来源", row.get("source", ""))).strip()
    url = str(row.get("新闻链接", row.get("url", ""))).strip()
    pub_time = str(row.get("发布时间", row.get("datetime", ""))).strip()
    print(f"--- {idx+1} ---")
    print(f"  标题: {title}")
    print(f"  内容(前150): {content[:150]}")
    print(f"  来源: {source}")
    print(f"  时间: {pub_time}")
    print(f"  URL: {url[:80]}")
    print()
