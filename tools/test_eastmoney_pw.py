#!/usr/bin/env python3
"""用 Playwright 拦截东方财富的头条/热点API"""
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        captured = []
        async def on_resp(response):
            u = response.url
            if response.status == 200:
                skip = (".js", ".css", ".png", ".jpg", ".svg", ".gif", ".ico", ".woff", ".ttf")
                if not any(u.endswith(s) for s in skip):
                    if "hm.baidu" not in u and "cnzz" not in u and "analytics" not in u and "log" not in u:
                        try:
                            ct = response.headers.get("content-type", "")
                            if "json" in ct or "javascript" in ct or "text/html" not in ct:
                                body = await response.text()
                                if body and len(body) > 80 and not body.strip().startswith("<!"):
                                    captured.append((u, body[:400]))
                        except:
                            pass
        page.on("response", on_resp)

        # 东方财富股票频道
        print("=== 访问东方财富股票频道 ===")
        await page.goto("https://stock.eastmoney.com/", timeout=25000)
        await page.wait_for_timeout(5000)

        print(f"捕获 {len(captured)} 个API")
        for u, body in captured:
            # 只看有 title/标题 相关的
            if "title" in body.lower() or "digest" in body.lower() or "headline" in body.lower():
                print(f"\nURL: {u}")
                print(f"Body: {body[:300]}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
