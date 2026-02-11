#!/usr/bin/env python3
"""从东方财富首页 DOM 抓取股市焦点内容"""
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://www.eastmoney.com/default.html", timeout=30000)
        await page.wait_for_timeout(5000)

        # 找股市焦点区域的新闻列表
        # 先看 hsgs_news 区域的结构
        hsgs = await page.query_selector(".hsgs_news")
        if hsgs:
            inner = await hsgs.inner_html()
            print("=== hsgs_news 区域 HTML (前2000字符) ===")
            print(inner[:2000])
            print()

        # 尝试直接提取链接和标题
        print("\n=== 尝试提取股市焦点新闻 ===")
        items = await page.query_selector_all(".hsgs_news a")
        for i, item in enumerate(items[:20]):
            text = (await item.inner_text()).strip()
            href = await item.get_attribute("href")
            if text and href and "eastmoney.com" in (href or ""):
                if len(text) > 5:  # 过滤掉太短的导航文字
                    print(f"  {i+1}. {text}")
                    print(f"     URL: {href}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
