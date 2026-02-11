#!/usr/bin/env python3
"""测试同花顺头条和雪球热门话题API"""
import asyncio
import httpx
import json


async def test_10jqka_headline():
    """同花顺头条"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://news.10jqka.com.cn/",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            "https://news.10jqka.com.cn/tapp/news/push/stock/",
            headers=headers,
        )
        data = resp.json()
        items = data.get("data", {}).get("list", [])
        print(f"=== 同花顺头条: {len(items)} 条 ===")
        for i, item in enumerate(items[:5]):
            title = item.get("title", "")
            digest = item.get("digest", "")[:150]
            print(f"  {i+1}. {title}")
            print(f"     摘要: {digest}")
            print(f"     字段: {list(item.keys())}")
            print()


async def test_xueqiu_hot_event():
    """雪球热门话题（需要通过Playwright获取cookie后拦截）"""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        hot_data = []
        async def on_resp(response):
            if "hot_event/list.json" in response.url and response.status == 200:
                try:
                    body = await response.json()
                    hot_data.append(body)
                except:
                    pass
        page.on("response", on_resp)

        await page.goto("https://xueqiu.com/", timeout=25000)
        await page.wait_for_timeout(5000)

        if hot_data:
            items = hot_data[0].get("list", [])
            print(f"=== 雪球热门话题: {len(items)} 条 ===")
            for i, item in enumerate(items[:5]):
                tag = item.get("tag", "")
                content = item.get("content", "")[:150]
                status_count = item.get("status_count", 0)
                print(f"  {i+1}. {tag}")
                print(f"     内容: {content}")
                print(f"     讨论数: {status_count}")
                print(f"     字段: {list(item.keys())}")
                print()
        else:
            print("未捕获到雪球热门话题数据")

        await browser.close()


async def test_xueqiu_hot_event_api():
    """雪球热门话题 - 直接用cookie调API"""
    from app.services.xueqiu_cookie_provider import xueqiu_cookie_provider
    cookies = await xueqiu_cookie_provider.get_cookies()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://xueqiu.com/",
        "Origin": "https://xueqiu.com",
    }
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(
            "https://xueqiu.com/hot_event/list.json",
            params={"count": "20"},
            headers=headers,
            cookies=cookies,
        )
        print(f"=== 雪球热门话题API直连 === status={resp.status_code}")
        text = resp.text[:100]
        if resp.status_code == 200 and not text.startswith("<!"):
            data = resp.json()
            items = data.get("list", [])
            print(f"获取到 {len(items)} 条")
            for i, item in enumerate(items[:5]):
                tag = item.get("tag", "")
                content = item.get("content", "")[:150]
                status_count = item.get("status_count", 0)
                print(f"  {i+1}. {tag}")
                print(f"     内容: {content}")
                print(f"     讨论数: {status_count}")
                print()
        else:
            print(f"  失败，返回: {text}")


async def main():
    await test_10jqka_headline()
    print("\n" + "=" * 60 + "\n")
    await test_xueqiu_hot_event_api()


if __name__ == "__main__":
    asyncio.run(main())
