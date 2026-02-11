#!/usr/bin/env python3
"""测试东方财富快讯接口"""
import asyncio
import httpx
import json
import re


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.eastmoney.com/",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 东方财富快讯 - column 102=全部, 350=财经要闻
        for col, label in [("102", "全部快讯"), ("350", "财经要闻")]:
            url = f"https://newsapi.eastmoney.com/kuaixun/v1/getlist_{col}_ajaxResult_20_1_.html"
            resp = await client.get(url, headers=headers)
            text = resp.text
            # 去掉 JSONP 包装: var ajaxResult={...}
            match = re.search(r"var ajaxResult=(\{.*\})", text, re.DOTALL)
            if not match:
                print(f"=== {label} === 解析失败")
                continue
            data = json.loads(match.group(1))
            items = data.get("LivesList", [])
            print(f"=== {label} === {len(items)} 条")
            for i, item in enumerate(items[:5]):
                title = item.get("title", "")
                digest = item.get("digest", "")[:150]
                showtime = item.get("showtime", "")
                art_url = item.get("url_w", item.get("url_unique", ""))
                print(f"  {i+1}. {title}")
                print(f"     摘要: {digest}")
                print(f"     时间: {showtime} | URL: {art_url[:60]}")
                print()


if __name__ == "__main__":
    asyncio.run(main())
