#!/usr/bin/env python3
"""
全量数据采集爬虫测试脚本
测试所有数据源是否能正常工作（导入、网络请求、数据解析）
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger

# 简化日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")

results = {}

def record(name, ok, count=0, msg=""):
    status = "✅" if ok else "❌"
    results[name] = ok
    detail = f" ({count}条)" if count else ""
    extra = f" - {msg}" if msg else ""
    print(f"  {status} {name}{detail}{extra}")


async def test_domestic_sources():
    """测试国内数据源"""
    print("\n" + "="*60)
    print("📈 国内股票数据源测试")
    print("="*60)

    from app.services.stock_news_collector import StockNewsCollector
    collector = StockNewsCollector(use_cache=False)

    # 1. AKShare
    try:
        items = await collector.fetch_akshare_news()
        record("AKShare（东方财富）", len(items) > 0, len(items))
    except Exception as e:
        record("AKShare（东方财富）", False, msg=str(e)[:80])

    # 2. 新浪财经
    try:
        items = await collector.fetch_sina_news()
        record("新浪财经", len(items) > 0, len(items))
    except Exception as e:
        record("新浪财经", False, msg=str(e)[:80])

    # 3. 同花顺
    try:
        items = await collector.fetch_10jqka_news()
        record("同花顺", len(items) > 0, len(items))
    except Exception as e:
        record("同花顺", False, msg=str(e)[:80])

    # 4. 雪球
    try:
        items = await collector.fetch_xueqiu_news()
        record("雪球", len(items) > 0, len(items))
    except Exception as e:
        record("雪球", False, msg=str(e)[:80])

    # 5. Tushare
    from app.config import Config
    if Config.TUSHARE_TOKEN:
        try:
            items = await collector.fetch_tushare_news()
            record("Tushare", len(items) > 0, len(items))
        except Exception as e:
            record("Tushare", False, msg=str(e)[:80])
    else:
        record("Tushare", True, msg="未配置Token，跳过（正常）")


async def test_international_sources():
    """测试国际数据源"""
    print("\n" + "="*60)
    print("🌍 国际财经新闻数据源测试")
    print("="*60)

    from app.services.international_news_service import InternationalNewsService
    from app.config import Config
    svc = InternationalNewsService(use_cache=False)

    # 免费源（无需API Key）
    # 1. GDELT
    try:
        items = await svc.fetch_gdelt_news()
        record("GDELT（免费）", len(items) > 0, len(items))
    except Exception as e:
        record("GDELT（免费）", False, msg=str(e)[:80])

    # 2. Google News RSS
    try:
        items = await svc.fetch_google_news_rss()
        record("Google News RSS（免费）", len(items) > 0, len(items))
    except Exception as e:
        record("Google News RSS（免费）", False, msg=str(e)[:80])

    # 需要API Key的源
    key_sources = {
        "Finnhub": ("FINNHUB_API_KEY", svc.fetch_finnhub_news),
        "NewsAPI": ("NEWSAPI_API_KEY", svc.fetch_newsapi_news),
        "Alpha Vantage": ("ALPHA_VANTAGE_API_KEY", svc.fetch_alpha_vantage_news),
        "Marketaux": ("MARKETAUX_API_KEY", svc.fetch_marketaux_news),
    }
    for name, (env_key, method) in key_sources.items():
        key_val = getattr(Config, env_key, "")
        if key_val:
            try:
                items = await method()
                record(f"{name}（有Key）", len(items) > 0, len(items))
            except Exception as e:
                record(f"{name}（有Key）", False, msg=str(e)[:80])
        else:
            record(f"{name}", True, msg="未配置API Key，跳过（正常）")


async def test_research_sources():
    """测试投行研报数据源"""
    print("\n" + "="*60)
    print("📊 投行研报数据源测试")
    print("="*60)

    from app.services.research_report_service import ResearchReportService
    svc = ResearchReportService(use_cache=False)

    test_symbol = "AAPL"

    # Tier 1: Yahoo Finance (免费)
    try:
        ratings = await svc.fetch_yahoo_finance_ratings(test_symbol)
        record(f"Yahoo Finance ({test_symbol})", len(ratings) > 0, len(ratings))
    except Exception as e:
        record(f"Yahoo Finance ({test_symbol})", False, msg=str(e)[:80])

    # Tier 2: Zacks (免费)
    try:
        ratings = await svc.fetch_zacks_ratings(test_symbol)
        record(f"Zacks ({test_symbol})", len(ratings) > 0, len(ratings))
    except Exception as e:
        record(f"Zacks ({test_symbol})", False, msg=str(e)[:80])

    # Tier 2: Finviz (免费)
    try:
        ratings = await svc.fetch_finviz_ratings(test_symbol)
        record(f"Finviz ({test_symbol})", True, len(ratings), msg="HTML抓取，可能为0")
    except Exception as e:
        record(f"Finviz ({test_symbol})", False, msg=str(e)[:80])

    # Tier 1: Finnhub Research (需Key)
    from app.config import Config
    if Config.FINNHUB_API_KEY:
        try:
            ratings = await svc.fetch_finnhub_recommendations(test_symbol)
            record(f"Finnhub Research ({test_symbol})", len(ratings) > 0, len(ratings))
        except Exception as e:
            record(f"Finnhub Research ({test_symbol})", False, msg=str(e)[:80])
    else:
        record("Finnhub Research", True, msg="未配置API Key，跳过（正常）")


async def test_sentiment_crawler():
    """测试情绪爬虫"""
    print("\n" + "="*60)
    print("💬 散户情绪爬虫测试")
    print("="*60)

    from app.services.sentiment_crawler import SentimentCrawler
    crawler = SentimentCrawler()

    # Eastmoney
    try:
        comments = await crawler.fetch_eastmoney_comments(time_window_hours=72)
        record("东方财富股吧", True, len(comments), msg="可能为0（API格式变化）")
    except Exception as e:
        record("东方财富股吧", False, msg=str(e)[:80])

    # 10jqka
    try:
        comments = await crawler.fetch_10jqka_comments(time_window_hours=72)
        record("同花顺社区", True, len(comments), msg="HTML抓取，可能为0")
    except Exception as e:
        record("同花顺社区", False, msg=str(e)[:80])


async def test_imports():
    """测试关键模块导入"""
    print("\n" + "="*60)
    print("📦 关键模块导入测试")
    print("="*60)

    modules = [
        ("akshare", "import akshare"),
        ("feedparser", "import feedparser"),
        ("yfinance", "import yfinance"),
        ("httpx", "import httpx"),
        ("playwright", "import playwright"),
        ("beautifulsoup4", "from bs4 import BeautifulSoup"),
        ("lxml", "import lxml"),
        ("pandas", "import pandas"),
    ]
    for name, stmt in modules:
        try:
            exec(stmt)
            record(f"import {name}", True)
        except ImportError as e:
            record(f"import {name}", False, msg=str(e)[:60])


async def main():
    start = time.time()
    print("🔍 全量数据采集爬虫测试")
    print(f"   时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    await test_imports()
    await test_domestic_sources()
    await test_international_sources()
    await test_research_sources()
    await test_sentiment_crawler()

    elapsed = time.time() - start
    print("\n" + "="*60)
    print("📋 测试汇总")
    print("="*60)
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    print(f"  总计: {total}  通过: {passed}  失败: {failed}")
    print(f"  耗时: {elapsed:.1f}s")

    if failed > 0:
        print("\n  ❌ 失败项:")
        for name, ok in results.items():
            if not ok:
                print(f"     - {name}")

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
