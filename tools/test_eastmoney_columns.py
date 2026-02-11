#!/usr/bin/env python3
"""测试东方财富不同 column 编号找到股市焦点"""
import asyncio
import httpx
import json
import re


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://stock.eastmoney.com/",
    }

    # 常见 column 编号: 350=要闻, 344=股票, 102=全部快讯, 948=博主
    # 股市焦点可能是其他编号，试几个
    columns_to_try = [
        ("350", "要闻"),
        ("344", "股票"),
        ("283", "焦点?"),
        ("284", "焦点2?"),
        ("285", "焦点3?"),
        ("352", "头条?"),
        ("353", "热点?"),
        ("354", "推荐?"),
        ("355", "精选?"),
        ("356", "焦点4?"),
        ("357", "焦点5?"),
        ("280", "焦点6?"),
        ("281", "焦点7?"),
        ("282", "焦点8?"),
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for col, label in columns_to_try:
            try:
                cb = f"cb_{col}"
                resp = await client.get(
                    "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns",
                    params={
                        "client": "web", "biz": "web_news_col",
                        "column": col, "order": "1",
                        "needInteractData": "0",
                        "page_index": "1", "page_size": "3",
                        "req_trace": "0.123",
                        "fields": "code,showTime,title,mediaName,summary,image,url,uniqueUrl",
                        "callback": cb,
                    },
                    headers=headers,
                )
                text = resp.text
                m = re.search(rf"{cb}\((\{{.*?\}})\)", text, re.DOTALL)
                if not m:
                    print(f"  column={col} ({label}): 解析失败")
                    continue
                data = json.loads(m.group(1))
                items = data.get("data", {}).get("list", [])
                if items:
                    first_title = items[0].get("title", "无标题")
                    print(f"  column={col} ({label}): {len(items)} 条 -> {first_title}")
                else:
                    code = data.get("code", "?")
                    print(f"  column={col} ({label}): 空 (code={code})")
            except Exception as e:
                print(f"  column={col} ({label}): ERROR {e}")


if __name__ == "__main__":
    asyncio.run(main())
