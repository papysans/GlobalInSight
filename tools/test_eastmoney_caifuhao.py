#!/usr/bin/env python3
"""测试东方财富财富号推荐接口（头条文章）"""
import asyncio
import httpx
import json


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://caifuhao.eastmoney.com/",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            "https://caifuhao.eastmoney.com/v1/recommend",
            params={"pagesize": "10", "isReload": "true"},
            headers=headers,
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        items = data.get("result", {}).get("items", [])
        print(f"获取到 {len(items)} 条")
        for i, item in enumerate(items[:5]):
            item_data = item.get("itemData", {})
            title = item_data.get("title", "")
            digest = item_data.get("digest", item_data.get("summary", ""))
            if digest:
                digest = digest[:150]
            source = item_data.get("source", item_data.get("mediaName", ""))
            info_code = item.get("infoCode", "")
            print(f"  {i+1}. {title}")
            print(f"     摘要: {digest}")
            print(f"     来源: {source}")
            print(f"     字段: {list(item_data.keys())[:15]}")
            print()

        # 也试试东方财富要闻频道的 v2 接口
        print("\n=== 要闻频道 v2 ===")
        # column: 350=要闻, 344=股票, 102=全部
        for col, label in [("350", "要闻"), ("344", "股票")]:
            resp2 = await client.get(
                f"https://newsapi.eastmoney.com/kuaixun/v2/api/list",
                params={"column": col, "limit": "10", "p": "1"},
                headers=headers,
            )
            text = resp2.text
            # 可能是 JSONP
            if text.startswith("{"):
                data2 = json.loads(text)
            else:
                import re
                m = re.search(r"\((\{.*\})\)", text, re.DOTALL)
                if m:
                    data2 = json.loads(m.group(1))
                else:
                    print(f"  {label}: 解析失败, raw={text[:200]}")
                    continue
            news = data2.get("news", data2.get("LivesList", []))
            print(f"  {label}: {len(news)} 条")
            for i, n in enumerate(news[:3]):
                print(f"    {i+1}. {n.get('title', '')}")
                print(f"       摘要: {n.get('digest', '')[:100]}")
                print()


if __name__ == "__main__":
    asyncio.run(main())
