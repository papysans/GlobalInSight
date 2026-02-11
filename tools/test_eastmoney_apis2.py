#!/usr/bin/env python3
"""测试东方财富API - 查看原始返回结构"""
import asyncio
import httpx
import json


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.eastmoney.com/",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 财经要闻
        resp = await client.get(
            "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns",
            params={
                "client": "web", "biz": "web_news_col",
                "column": "350", "order": "1",
                "needInteractData": "0", "page_index": "1", "page_size": "5",
            },
            headers=headers,
        )
        print(f"Status: {resp.status_code}")
        print(f"Raw (500 chars): {resp.text[:500]}")
        print()

        # 试试另一个接口
        resp2 = await client.get(
            "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html",
            headers=headers,
        )
        print(f"快讯接口 Status: {resp2.status_code}")
        text2 = resp2.text[:500]
        print(f"Raw: {text2}")
        print()

        # 东方财富股吧热帖
        resp3 = await client.get(
            "https://gbapi.eastmoney.com/search/api/HotRank",
            params={"pageindex": "1", "pagesize": "10", "appkey": "quoteapi"},
            headers=headers,
        )
        print(f"股吧热帖 Status: {resp3.status_code}")
        print(f"Raw: {resp3.text[:500]}")
        print()

        # 东方财富首页要闻 - 直接用 Playwright 拦截
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            captured = []
            async def on_resp(response):
                u = response.url
                if response.status == 200 and ("news" in u or "article" in u or "kuaixun" in u):
                    if not u.endswith((".js", ".css", ".png", ".jpg", ".svg", ".gif", ".ico")):
                        try:
                            body = await response.text()
                            if body and len(body) > 100 and not body.strip().startswith("<!"):
                                captured.append((u, body[:400]))
                        except:
                            pass
            page.on("response", on_resp)

            await page.goto("https://www.eastmoney.com/", timeout=25000)
            await page.wait_for_timeout(5000)

            print(f"=== Playwright 捕获 {len(captured)} 个API ===")
            for u, body in captured[:10]:
                print(f"URL: {u}")
                print(f"Body: {body[:250]}")
                print()

            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
