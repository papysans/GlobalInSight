#!/usr/bin/env python3
"""用 Playwright 拦截东方财富财经频道的头条API"""
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for page_url, label in [
            ("https://finance.eastmoney.com/", "财经频道"),
            ("https://caifuhao.eastmoney.com/", "财富号"),
            ("https://guba.eastmoney.com/", "股吧首页"),
        ]:
            page = await browser.new_page()
            captured = []
            async def make_handler(cap):
                async def on_resp(response):
                    u = response.url
                    if response.status == 200:
                        skip = (".js", ".css", ".png", ".jpg", ".svg", ".gif", ".ico", ".woff", ".ttf")
                        if not any(u.endswith(s) for s in skip):
                            if "hm.baidu" not in u and "cnzz" not in u and "log" not in u:
                                try:
                                    body = await response.text()
                                    if body and len(body) > 100 and not body.strip().startswith("<!"):
                                        if "title" in body[:500].lower():
                                            cap.append((u, body[:500]))
                                except:
                                    pass
                return on_resp
            handler = await make_handler(captured)
            page.on("response", handler)

            print(f"\n=== {label}: {page_url} ===")
            try:
                await page.goto(page_url, timeout=20000)
                await page.wait_for_timeout(4000)
            except Exception as e:
                print(f"  加载失败: {e}")
                await page.close()
                continue

            print(f"  捕获 {len(captured)} 个含title的API")
            for u, body in captured[:5]:
                print(f"  URL: {u}")
                print(f"  Body: {body[:250]}")
                print()
            await page.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
