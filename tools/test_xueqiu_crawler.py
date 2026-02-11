#!/usr/bin/env python3
"""测试雪球爬虫：Playwright cookie 获取 + 热股 API 请求"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_cookie_provider():
    """测试 cookie 获取"""
    from app.services.xueqiu_cookie_provider import xueqiu_cookie_provider

    print("=" * 60)
    print("Step 1: 测试 Playwright 获取雪球 cookie")
    print("=" * 60)

    cookies = await xueqiu_cookie_provider.get_cookies()
    print(f"获取到 {len(cookies)} 个 cookie:")
    for k, v in cookies.items():
        display_v = v[:20] + "..." if len(v) > 20 else v
        print(f"  {k} = {display_v}")

    has_token = "xq_a_token" in cookies
    print(f"\nxq_a_token: {'✅ 存在' if has_token else '❌ 缺失'}")

    # 测试缓存
    print("\nStep 1.1: 测试缓存命中")
    cookies2 = await xueqiu_cookie_provider.get_cookies()
    print(f"缓存命中: {'✅' if cookies2 is cookies else '❌ 重新获取了'}")

    return cookies, has_token


async def test_hot_stock_api(cookies: dict):
    """测试热股 API"""
    import httpx

    print("\n" + "=" * 60)
    print("Step 2: 测试雪球热股 API")
    print("=" * 60)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Referer": "https://xueqiu.com/hq",
        "Origin": "https://xueqiu.com",
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        url = "https://stock.xueqiu.com/v5/stock/hot_stock/list.json"
        params = {"size": "10", "order": "desc", "order_by": "percent", "type": "12", "_type": "12"}
        resp = await client.get(url, params=params, headers=headers, cookies=cookies)

        print(f"HTTP Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type', 'N/A')}")

        raw = resp.text.strip()
        if raw.startswith("<"):
            print(f"❌ 返回了 HTML 反爬页面 (前100字符): {raw[:100]}")
            return False

        try:
            data = resp.json()
            items = data.get("data", {}).get("items", [])
            print(f"✅ 获取到 {len(items)} 只热股:")
            for i, item in enumerate(items[:5]):
                name = item.get("name", "")
                symbol = item.get("symbol", "")
                percent = item.get("percent", 0)
                current = item.get("current", 0)
                print(f"  {i+1}. {name}({symbol}) 当前价:{current} 涨跌幅:{percent}%")
            if len(items) > 5:
                print(f"  ... 还有 {len(items) - 5} 只")
            return True
        except Exception as e:
            print(f"❌ JSON 解析失败: {e}")
            print(f"响应前200字符: {raw[:200]}")
            return False


async def test_hot_post_api(cookies: dict):
    """测试热帖 API"""
    import httpx

    print("\n" + "=" * 60)
    print("Step 3: 测试雪球热帖 API (备用接口)")
    print("=" * 60)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Referer": "https://xueqiu.com/",
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        url = "https://xueqiu.com/statuses/hot/listV2.json"
        params = {"since_id": "-1", "max_id": "-1", "size": "10"}
        resp = await client.get(url, params=params, headers=headers, cookies=cookies)

        print(f"HTTP Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type', 'N/A')}")

        raw = resp.text.strip()
        if raw.startswith("<"):
            print(f"❌ 返回了 HTML 反爬页面")
            return False

        try:
            data = resp.json()
            items = data.get("items", [])
            print(f"✅ 获取到 {len(items)} 条热帖:")
            for i, item in enumerate(items[:5]):
                original = item.get("original_status", item)
                title = original.get("title") or original.get("description", "")
                if not title:
                    title = str(original.get("text", ""))[:60]
                print(f"  {i+1}. {title[:60]}")
            return True
        except Exception as e:
            print(f"❌ JSON 解析失败: {e}")
            return False


async def test_full_collector():
    """测试完整的 StockNewsCollector 雪球采集"""
    print("\n" + "=" * 60)
    print("Step 4: 测试完整的 fetch_xueqiu_news()")
    print("=" * 60)

    from app.services.stock_news_collector import stock_news_collector
    items = await stock_news_collector.fetch_xueqiu_news()
    print(f"采集到 {len(items)} 条雪球数据")
    for item in items[:3]:
        print(f"  - {item.title}")
    return len(items) > 0


async def main():
    print("🧪 雪球爬虫测试开始\n")

    cookies, has_token = await test_cookie_provider()

    if not has_token:
        print("\n⚠️ 未获取到 xq_a_token，API 测试可能失败")

    stock_ok = await test_hot_stock_api(cookies)
    post_ok = await test_hot_post_api(cookies)
    collector_ok = await test_full_collector()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"  Cookie 获取:  {'✅' if has_token else '❌'}")
    print(f"  热股 API:     {'✅' if stock_ok else '❌'}")
    print(f"  热帖 API:     {'✅' if post_ok else '❌'}")
    print(f"  完整采集器:   {'✅' if collector_ok else '❌'}")

    if stock_ok or post_ok:
        print("\n🎉 雪球爬虫功能正常!")
    else:
        print("\n💥 雪球爬虫仍有问题，需要进一步排查")


if __name__ == "__main__":
    asyncio.run(main())
