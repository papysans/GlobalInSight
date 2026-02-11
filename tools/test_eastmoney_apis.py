#!/usr/bin/env python3
"""测试东方财富的新闻/话题API"""
import asyncio
import httpx
import json


async def test_eastmoney_news():
    """东方财富财经要闻API"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.eastmoney.com/",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. 财经要闻
        urls = [
            ("财经要闻", "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns", {
                "client": "web", "biz": "web_news_col",
                "column": "350", "order": "1",
                "needInteractData": "0", "page_index": "1", "page_size": "10",
            }),
            ("7x24快讯", "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns", {
                "client": "web", "biz": "web_news_col",
                "column": "102", "order": "1",
                "needInteractData": "0", "page_index": "1", "page_size": "10",
            }),
            ("股票要闻", "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns", {
                "client": "web", "biz": "web_news_col",
                "column": "344", "order": "1",
                "needInteractData": "0", "page_index": "1", "page_size": "10",
            }),
        ]

        for label, url, params in urls:
            try:
                resp = await client.get(url, params=params, headers=headers)
                print(f"=== {label} === status={resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    news = data.get("data", {}).get("list", [])
                    print(f"  获取到 {len(news)} 条")
                    for i, item in enumerate(news[:3]):
                        title = item.get("title", "")
                        digest = item.get("digest", item.get("content", ""))
                        if digest:
                            digest = digest[:120]
                        art_url = item.get("url", item.get("art_url", ""))
                        source = item.get("source", "")
                        showtime = item.get("showtime", item.get("display_time", ""))
                        print(f"  {i+1}. {title}")
                        print(f"     摘要: {digest}")
                        print(f"     来源: {source} | 时间: {showtime}")
                        print(f"     字段: {list(item.keys())[:10]}")
                        print()
                print()
            except Exception as e:
                print(f"=== {label} === ERROR: {e}")
                print()


async def main():
    await test_eastmoney_news()


if __name__ == "__main__":
    asyncio.run(main())
