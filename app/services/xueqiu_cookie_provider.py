#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雪球 Cookie 提供器
使用 Playwright 无头浏览器自动获取雪球反爬所需的 cookie（xq_a_token 等）。
无需登录账号，仅利用浏览器自动执行雪球首页的 JS 来通过反爬校验。
"""

import asyncio
import time
from typing import Dict, Optional

from loguru import logger


class XueqiuCookieProvider:
    """通过 Playwright 无头浏览器获取雪球 cookie 并缓存复用。"""

    def __init__(self, cache_ttl: int = 1800):
        """
        Args:
            cache_ttl: cookie 缓存有效期（秒），默认 30 分钟
        """
        self._cache_ttl = cache_ttl
        self._cached_cookies: Optional[Dict[str, str]] = None
        self._cached_at: float = 0
        self._lock = asyncio.Lock()

    def _is_cache_valid(self) -> bool:
        return (
            self._cached_cookies is not None
            and (time.time() - self._cached_at) < self._cache_ttl
            and self._cached_cookies.get("xq_a_token")
        )

    async def get_cookies(self, force_refresh: bool = False) -> Dict[str, str]:
        """获取雪球 cookie，优先使用缓存。

        Returns:
            dict: cookie 键值对，至少包含 xq_a_token
        """
        if not force_refresh and self._is_cache_valid():
            logger.debug("雪球 cookie 命中缓存")
            return self._cached_cookies

        async with self._lock:
            # double-check after acquiring lock
            if not force_refresh and self._is_cache_valid():
                return self._cached_cookies

            logger.info("🌐 使用 Playwright 获取雪球 cookie...")
            cookies = await self._fetch_cookies_via_playwright()
            if cookies.get("xq_a_token"):
                self._cached_cookies = cookies
                self._cached_at = time.time()
                logger.info(f"✅ 雪球 cookie 获取成功，xq_a_token={cookies['xq_a_token'][:8]}...")
            else:
                logger.warning("⚠️ Playwright 未能获取 xq_a_token，cookie 可能不完整")
                # 仍然缓存，避免短时间内反复启动浏览器
                self._cached_cookies = cookies
                self._cached_at = time.time()
            return cookies

    async def _fetch_cookies_via_playwright(self) -> Dict[str, str]:
        """启动无头浏览器访问雪球首页，等待 JS 执行完毕后提取 cookie。"""
        cookies_dict: Dict[str, str] = {}
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/143.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()

                # 访问雪球首页，等待 JS 执行和页面加载
                await page.goto("https://xueqiu.com/", wait_until="networkidle", timeout=30000)

                # 额外等待确保 cookie 已写入
                await page.wait_for_timeout(2000)

                # 提取所有 cookie
                all_cookies = await context.cookies()
                for c in all_cookies:
                    cookies_dict[c["name"]] = c["value"]

                await browser.close()

            logger.debug(f"Playwright 获取到 {len(cookies_dict)} 个 cookie: {list(cookies_dict.keys())}")

        except Exception as e:
            logger.error(f"❌ Playwright 获取雪球 cookie 失败: {e}")

        return cookies_dict

    def invalidate_cache(self):
        """手动使缓存失效，下次调用 get_cookies 时会重新获取。"""
        self._cached_cookies = None
        self._cached_at = 0


# 全局单例
xueqiu_cookie_provider = XueqiuCookieProvider()
