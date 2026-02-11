#!/usr/bin/env python3
"""用 Playwright 去东方财富 default.html 找股市焦点接口"""
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
                skip = (".css", ".png", ".jpg", ".svg", ".gif", ".ico", ".woff", ".ttf")
                if not any(u.endswith(s) for s in skip):
                    if "hm.baidu" not in u and "cnzz" not in u and "log" not in u and "same.eastmoney" not in u and "anonflow" not in u:
                        try:
                            body = await response.text()
                            if body and len(body) > 100 and not body.strip().startswith("<!"):
                                captured.append((u, body[:500]))
                        except:
                            pass
        page.on("response", on_resp)

        await page.goto("https://www.eastmoney.com/default.html", timeout=30000)
        await page.wait_for_timeout(6000)

        # 找页面中"焦点"相关内容
        content = await page.content()
        for keyword in ["焦点", "股市焦点", "热点"]:
            if keyword in content:
                idx = content.index(keyword)
                print(f"=== 页面中找到'{keyword}' ===")
                print(content[max(0,idx-300):idx+300])
                print()

        # 打印所有捕获的API中含有新闻数据的
        print(f"\n=== 捕获 {len(captured)} 个API ===")
        for u, body in captured:
            if "title" in body[:300] and ("news" in u or "listapi" in u or "article" in u or "kuaixun" in u or "focus" in u or "jiaodian" in u):
                print(f"URL: {u}")
                print(f"Body: {body[:350]}")
                print()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
