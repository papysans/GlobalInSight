#!/usr/bin/env python3
"""测试东方财富最佳接口 - 看哪个 column 有摘要"""
import asyncio
import httpx
import json
import re


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.eastmoney.com/",
    }

    # 有数据的 columns
    good_columns = [
        ("350", "要闻"),
        ("344", "股票"),
        ("352", "头条"),
        ("353", "热点"),
        ("354", "推荐"),
        ("356", "焦点A"),
        ("357", "焦点B"),
        ("282", "焦点C"),
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for col, label in good_columns:
            cb = f"cb_{col}"
            resp = await client.get(
                "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns",
                params={
                    "client": "web", "biz": "web_news_col",
                    "column": col, "order": "1",
                    "needInteractData": "0",
                    "page_index": "1", "page_size": "5",
                    "req_trace": "0.123",
                    "fields": "code,showTime,title,mediaName,summary,image,url,uniqueUrl",
                    "callback": cb,
                },
                headers=headers,
            )
            m = re.search(rf"{cb}\((\{{.*?\}})\)", resp.text, re.DOTALL)
            if not m:
                continue
            data = json.loads(m.group(1))
            items = data.get("data", {}).get("list", [])
            print(f"\n=== column={col} ({label}) === {len(items)} 条")
            for i, item in enumerate(items[:3]):
                title = item.get("title", "")
                summary = item.get("summary", "")
                media = item.get("mediaName", "")
                show_time = item.get("showTime", "")
                url = item.get("url", item.get("uniqueUrl", ""))
                print(f"  {i+1}. {title}")
                print(f"     摘要: {(summary or '无')[:120]}")
                print(f"     来源: {media} | 时间: {show_time}")
                print(f"     字段: {list(item.keys())}")


if __name__ == "__main__":
    asyncio.run(main())
