#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 Playwright 浏览器是否能正常弹出"""

import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    async with async_playwright() as p:
        print("正在启动浏览器...")
        browser = await p.chromium.launch(
            headless=False,  # 非无头模式，应该能看到窗口
            args=['--start-maximized']
        )
        print("浏览器已启动，创建页面...")
        context = await browser.new_context()
        page = await context.new_page()
        
        print("正在访问百度...")
        await page.goto("https://www.baidu.com")
        print("页面已加载，等待5秒...")
        await asyncio.sleep(5)
        
        print("关闭浏览器...")
        await browser.close()
        print("测试完成！")

if __name__ == "__main__":
    asyncio.run(test_browser())
