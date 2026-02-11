#!/usr/bin/env python3
"""用 Playwright 找东方财富"股市焦点"接口"""
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
                    if "hm.baidu" not in u and "cnzz" not in u and "log" not in u and "bulletin" not in u:
                        try:
                            body = await response.text()
                            if body and len(body) > 80 and not body.strip().startswith("<!"):
                                captured.append((u, body[:600]))
                        except:
                            pass
        page.on("response", on_resp)

        await page.goto("https://stock.eastmoney.com/", timeout=25000)
        await page.wait_for_timeout(5000)

        # 看看页面上有没有"焦点"文字
        content = await page.content()
        if "焦点" in content:
            idx = content.index("焦点")
            print(f"页面中找到'焦点'，周围HTML:")
            print(content[max(0,idx-200):idx+300])
            print()

        print(f"\n=== 全部捕获的API ({len(captured)} 个) ===")
        for u, body in captured:
            print(f"URL: {u}")
            print(f"Body: {body[:300]}")
            print()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
