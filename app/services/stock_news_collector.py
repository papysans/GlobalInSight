#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票资讯爬虫服务
从多个国内股票资讯平台采集热点数据
支持 AKShare、新浪财经、同花顺、雪球、Tushare 等数据源
"""

import asyncio
import base64
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from loguru import logger

from app.config import Config
from app.schemas import StockNewsItem, StockNewsCollectResponse


# ---------------------------------------------------------------------------
# RateLimiter: 全局并发控制 + 每源独立 cooldown + 高风险源指数退避
# ---------------------------------------------------------------------------

@dataclass
class SourceRateLimitConfig:
    """每个数据源的独立限速配置"""
    max_concurrent: int = 3
    cooldown_seconds: float = 1.0
    is_high_risk: bool = False


# 默认限速配置
DEFAULT_RATE_LIMIT_CONFIGS: Dict[str, SourceRateLimitConfig] = {
    "akshare": SourceRateLimitConfig(max_concurrent=3, cooldown_seconds=0.5, is_high_risk=False),
    "sina": SourceRateLimitConfig(max_concurrent=3, cooldown_seconds=1.0, is_high_risk=False),
    "10jqka": SourceRateLimitConfig(max_concurrent=2, cooldown_seconds=2.0, is_high_risk=False),
    "xueqiu": SourceRateLimitConfig(max_concurrent=2, cooldown_seconds=3.0, is_high_risk=True),
    "tushare": SourceRateLimitConfig(max_concurrent=3, cooldown_seconds=1.0, is_high_risk=False),
}


class RateLimiter:
    """全局请求速率限制器

    基于 asyncio.Semaphore 实现全局并发上限，
    并为每个数据源配置独立的 cooldown 间隔和并发信号量。
    高风险源失败时执行指数退避策略（5s → 15s → 跳过）。
    """

    def __init__(self, global_max_concurrent: int = 10):
        self.global_semaphore = asyncio.Semaphore(global_max_concurrent)
        self.source_configs: Dict[str, SourceRateLimitConfig] = {}
        self.source_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.source_last_request: Dict[str, float] = {}
        self.source_fail_count: Dict[str, int] = {}

    def configure_source(self, source_id: str, config: SourceRateLimitConfig):
        """为指定数据源配置限速参数"""
        self.source_configs[source_id] = config
        self.source_semaphores[source_id] = asyncio.Semaphore(config.max_concurrent)
        self.source_fail_count[source_id] = 0

    async def acquire(self, source_id: str):
        """获取请求许可：全局信号量 + 源级信号量 + cooldown 等待"""
        await self.global_semaphore.acquire()
        if source_id in self.source_semaphores:
            await self.source_semaphores[source_id].acquire()
        # cooldown 等待
        config = self.source_configs.get(source_id)
        if config:
            last = self.source_last_request.get(source_id, 0)
            elapsed = time.time() - last
            if elapsed < config.cooldown_seconds:
                await asyncio.sleep(config.cooldown_seconds - elapsed)
        self.source_last_request[source_id] = time.time()

    def release(self, source_id: str):
        """释放请求许可"""
        self.global_semaphore.release()
        if source_id in self.source_semaphores:
            self.source_semaphores[source_id].release()

    async def handle_failure(self, source_id: str) -> bool:
        """高风险源失败时执行指数退避策略。

        Returns:
            True  – 可以重试
            False – 应跳过该源
        """
        config = self.source_configs.get(source_id)
        if not config or not config.is_high_risk:
            return False  # 非高风险源不做指数退避

        self.source_fail_count[source_id] = self.source_fail_count.get(source_id, 0) + 1
        fail_count = self.source_fail_count[source_id]

        if fail_count == 1:
            logger.warning(f"⚠️ 高风险源 {source_id} 第 1 次失败，等待 5s 后重试")
            await asyncio.sleep(5)
            return True
        elif fail_count == 2:
            logger.warning(f"⚠️ 高风险源 {source_id} 第 2 次失败，等待 15s 后重试")
            await asyncio.sleep(15)
            return True
        else:
            logger.error(f"❌ 高风险源 {source_id} 连续 {fail_count} 次失败，跳过该源")
            return False

    def reset_fail_count(self, source_id: str):
        """请求成功后重置失败计数"""
        self.source_fail_count[source_id] = 0


# ---------------------------------------------------------------------------
# 数据源配置
# ---------------------------------------------------------------------------

STOCK_SOURCES: Dict[str, Dict] = {
    "akshare": {
        "name": "AKShare（东方财富）",
        "category": "domestic",
        "enabled": True,
        "requires_api_key": False,
    },
    "sina": {
        "name": "新浪财经",
        "category": "domestic",
        "enabled": True,
        "requires_api_key": False,
    },
    "10jqka": {
        "name": "同花顺",
        "category": "domestic",
        "enabled": True,
        "requires_api_key": False,
    },
    "xueqiu": {
        "name": "雪球",
        "category": "domestic",
        "enabled": True,
        "requires_api_key": False,
    },
    "tushare": {
        "name": "Tushare",
        "category": "domestic",
        "enabled": bool(Config.TUSHARE_TOKEN),
        "requires_api_key": True,
    },
}


# ---------------------------------------------------------------------------
# StockNewsCollector
# ---------------------------------------------------------------------------

class StockNewsCollector:
    """股票资讯采集器，聚合国内数据源、国际财经新闻和投行研报"""

    def __init__(self, use_cache: bool = True):
        self.sources = STOCK_SOURCES
        self.use_cache = use_cache
        self.rate_limiter = RateLimiter(global_max_concurrent=10)

        # 初始化各数据源限速配置
        for source_id, config in DEFAULT_RATE_LIMIT_CONFIGS.items():
            self.rate_limiter.configure_source(source_id, config)

        # 缓存服务
        if self.use_cache:
            from app.services.hot_news_cache import hot_news_cache
            self.cache_service = hot_news_cache
        else:
            self.cache_service = None

        # 国际财经新闻服务
        from app.services.international_news_service import InternationalNewsService
        self.intl_news_service = InternationalNewsService(use_cache=use_cache)

        # 投行研报服务
        from app.services.research_report_service import ResearchReportService
        self.research_service = ResearchReportService(use_cache=use_cache)

        self._http_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    # ------------------------------------------------------------------
    # 东方财富（np-listapi JSONP 接口，头条+股票栏目，有标题+摘要）
    # ------------------------------------------------------------------

    async def fetch_akshare_news(self) -> List[StockNewsItem]:
        """通过东方财富 np-listapi JSONP 接口采集头条新闻（含摘要）。

        使用 column=352（头条）和 column=344（股票）两个栏目，
        合并去重后返回，每条都有 title + summary + mediaName + showTime。
        """
        import re as _re
        import json as _json

        source_id = "akshare"
        items: List[StockNewsItem] = []
        seen_titles: set = set()
        await self.rate_limiter.acquire(source_id)
        try:
            headers = {
                **self._http_headers,
                "Referer": "https://www.eastmoney.com/",
            }
            # 采集两个栏目：352(头条) + 344(股票)
            columns = [("352", "头条"), ("344", "股票")]

            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                for col_id, col_label in columns:
                    cb_name = f"cb_{col_id}"
                    params = {
                        "client": "web",
                        "biz": "web_news_col",
                        "column": col_id,
                        "order": "1",
                        "needInteractData": "0",
                        "page_index": "1",
                        "page_size": "15",
                        "req_trace": "0.123",
                        "fields": "code,showTime,title,mediaName,summary,image,url,uniqueUrl",
                        "callback": cb_name,
                    }
                    resp = await client.get(
                        "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns",
                        params=params,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    # 解析 JSONP: cb_352({"code":"1","data":{...}})
                    match = _re.search(
                        rf"{cb_name}\((\{{.*?\}})\)", resp.text, _re.DOTALL,
                    )
                    if not match:
                        logger.warning(f"⚠️ 东方财富 column={col_id} JSONP 解析失败")
                        continue
                    data = _json.loads(match.group(1))
                    news_list = data.get("data", {}).get("list", [])

                    for item in news_list:
                        title = str(item.get("title", "")).strip()
                        if not title or len(title) < 4:
                            continue
                        # 按标题去重
                        if title in seen_titles:
                            continue
                        seen_titles.add(title)

                        summary = str(item.get("summary", "")).strip()
                        media = str(item.get("mediaName", "")).strip()
                        show_time = str(item.get("showTime", "")).strip()
                        url = str(
                            item.get("url", item.get("uniqueUrl", ""))
                        ).strip()

                        idx = len(items)
                        items.append(StockNewsItem(
                            id=f"akshare_{col_id}_{idx}",
                            title=title,
                            summary=summary[:300] if summary else title,
                            source_platform="akshare",
                            source_name=f"东方财富{col_label}" if media else "东方财富",
                            url=url,
                            published_time=show_time or datetime.now().isoformat(),
                            hot_value="",
                            rank=idx + 1,
                            category="domestic",
                        ))
                        if len(items) >= 25:
                            break
                    if len(items) >= 25:
                        break

            logger.info(f"✓ 东方财富头条: {len(items)} 条（含摘要）")
            self.rate_limiter.reset_fail_count(source_id)
        except Exception as e:
            logger.error(f"❌ 东方财富采集失败: {e}")
            await self.rate_limiter.handle_failure(source_id)
        finally:
            self.rate_limiter.release(source_id)
        return items

    # ------------------------------------------------------------------
    # 新浪财经
    # ------------------------------------------------------------------

    async def fetch_sina_news(self) -> List[StockNewsItem]:
        """通过新浪财经 API 采集资讯"""
        source_id = "sina"
        items: List[StockNewsItem] = []
        await self.rate_limiter.acquire(source_id)
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get"
            params = {
                "pageid": "153",
                "lid": "2516",
                "k": "",
                "num": str(Config.STOCK_NEWS_CONFIG.get("max_items_per_source", 50)),
                "page": "1",
            }
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, params=params, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            result = data.get("result", {})
            news_data = result.get("data", [])
            for idx, item in enumerate(news_data):
                title = str(item.get("title", "")).strip()
                if not title:
                    continue
                summary = str(item.get("summary", item.get("intro", ""))).strip()
                link = str(item.get("url", item.get("link", ""))).strip()
                ctime = item.get("ctime", item.get("create_time", ""))
                try:
                    pub_time = datetime.fromtimestamp(int(ctime)).isoformat() if ctime else datetime.now().isoformat()
                except (ValueError, TypeError, OSError):
                    pub_time = str(ctime) if ctime else datetime.now().isoformat()

                items.append(StockNewsItem(
                    id=f"sina_{idx}",
                    title=title,
                    summary=summary[:200] if summary else title,
                    source_platform="sina",
                    source_name="新浪财经",
                    url=link,
                    published_time=pub_time,
                    hot_value="",
                    rank=idx + 1,
                    category="domestic",
                ))
            logger.info(f"✓ 新浪财经: {len(items)} 条")
            self.rate_limiter.reset_fail_count(source_id)
        except Exception as e:
            logger.error(f"❌ 新浪财经采集失败: {e}")
            await self.rate_limiter.handle_failure(source_id)
        finally:
            self.rate_limiter.release(source_id)
        return items

    # ------------------------------------------------------------------
    # 同花顺
    # ------------------------------------------------------------------

    async def fetch_10jqka_news(self) -> List[StockNewsItem]:
        """采集同花顺头条新闻（有标题+摘要的财经要闻）"""
        source_id = "10jqka"
        items: List[StockNewsItem] = []
        await self.rate_limiter.acquire(source_id)
        try:
            url = "https://news.10jqka.com.cn/tapp/news/push/stock/"
            headers = {**self._http_headers, "Referer": "https://news.10jqka.com.cn/"}
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            news_list = data.get("data", {}).get("list", [])
            for idx, item in enumerate(news_list):
                title = str(item.get("title", "")).strip()
                if not title:
                    continue
                digest = str(item.get("digest", "")).strip()
                # 构建完整URL
                news_url = str(item.get("url", "")).strip()
                if not news_url:
                    news_id = item.get("id", "")
                    news_url = f"https://news.10jqka.com.cn/{news_id}/" if news_id else ""
                # 解析时间
                ctime = item.get("ctime", "")
                try:
                    pub_time = datetime.fromtimestamp(int(ctime)).isoformat() if ctime else datetime.now().isoformat()
                except (ValueError, TypeError, OSError):
                    pub_time = datetime.now().isoformat()
                source_name = str(item.get("source", "同花顺")).strip()
                items.append(StockNewsItem(
                    id=f"10jqka_{idx}",
                    title=title,
                    summary=digest[:300] if digest and digest != title else title,
                    source_platform="10jqka",
                    source_name=f"同花顺 - {source_name}" if source_name and source_name != "同花顺" else "同花顺",
                    url=news_url,
                    published_time=pub_time,
                    hot_value="",
                    rank=idx + 1,
                    category="domestic",
                ))
            logger.info(f"✓ 同花顺头条: {len(items)} 条")
            self.rate_limiter.reset_fail_count(source_id)
        except Exception as e:
            logger.error(f"❌ 同花顺头条采集失败: {e}")
            await self.rate_limiter.handle_failure(source_id)
        finally:
            self.rate_limiter.release(source_id)
        return items

    # ------------------------------------------------------------------
    # 雪球（高风险，需处理反爬）
    # ------------------------------------------------------------------

    def _xueqiu_validate_json(self, resp: httpx.Response, label: str) -> dict:
        """校验雪球 API 响应是否为有效 JSON，返回解析后的 dict。"""
        raw_text = resp.text.strip()
        # 反爬页面通常返回 HTML 或空内容
        if not raw_text:
            raise ValueError(f"{label}: 响应体为空")
        if raw_text.startswith("<!") or raw_text.startswith("<html"):
            raise ValueError(f"{label}: 返回了 HTML 反爬页面 (前80字符: {raw_text[:80]})")
        try:
            return resp.json()
        except Exception:
            raise ValueError(f"{label}: JSON 解析失败 (前80字符: {raw_text[:80]})")

    async def fetch_xueqiu_news(self) -> List[StockNewsItem]:
        """采集雪球热门话题（通过 Playwright 获取 cookie 绕过反爬）。

        主接口: hot_event/list.json（热门话题，有标题+详细内容+讨论数）
        备用: 强制刷新cookie后重试
        """
        source_id = "xueqiu"
        items: List[StockNewsItem] = []
        await self.rate_limiter.acquire(source_id)
        try:
            from app.services.xueqiu_cookie_provider import xueqiu_cookie_provider
            cookies = await xueqiu_cookie_provider.get_cookies()

            async with httpx.AsyncClient(
                timeout=20.0,
                trust_env=False,
                follow_redirects=True,
            ) as client:
                # 雪球热门话题接口
                url = "https://xueqiu.com/hot_event/list.json"
                params = {"count": "20"}
                headers = {
                    **self._http_headers,
                    "Referer": "https://xueqiu.com/",
                    "Origin": "https://xueqiu.com",
                }
                resp = await client.get(url, params=params, headers=headers, cookies=cookies)
                resp.raise_for_status()
                data = self._xueqiu_validate_json(resp, "雪球热门话题API")

            topic_list = data.get("list", [])
            for idx, item in enumerate(topic_list):
                # tag 格式: "#春节假期临近，持股过节VS持币过节？#"
                tag = str(item.get("tag", "")).strip().strip("#").strip()
                content = str(item.get("content", "")).strip()
                status_count = item.get("status_count", 0)
                topic_id = item.get("id", "")
                pic = item.get("pic", "")
                if not tag:
                    continue
                items.append(StockNewsItem(
                    id=f"xueqiu_{idx}",
                    title=tag,
                    summary=content[:300] if content else tag,
                    source_platform="xueqiu",
                    source_name="雪球",
                    url=f"https://xueqiu.com/hashtag/{base64.urlsafe_b64encode(item.get('tag', '').encode('utf-8')).decode('ascii')}" if item.get('tag') else "",
                    published_time=datetime.now().isoformat(),
                    hot_value=str(status_count),
                    rank=idx + 1,
                    category="domestic",
                ))
            logger.info(f"✓ 雪球热门话题: {len(items)} 条")
            self.rate_limiter.reset_fail_count(source_id)
        except Exception as e:
            logger.warning(f"⚠️ 雪球热门话题API失败: {e}，尝试备用方案...")
            try:
                from app.services.xueqiu_cookie_provider import xueqiu_cookie_provider
                xueqiu_cookie_provider.invalidate_cache()
                items = await self._xueqiu_fallback()
                if items:
                    self.rate_limiter.reset_fail_count(source_id)
                else:
                    logger.warning("⏭️ 雪球备用接口也无数据，本轮跳过")
            except Exception as fallback_err:
                logger.error(f"❌ 雪球备用接口也失败: {fallback_err}")
                logger.warning("⏭️ 雪球数据源本轮跳过")
        finally:
            self.rate_limiter.release(source_id)
        return items

    async def _xueqiu_fallback(self) -> List[StockNewsItem]:
        """雪球备用方案：强制刷新 cookie 后重试热门话题接口"""
        items: List[StockNewsItem] = []
        from app.services.xueqiu_cookie_provider import xueqiu_cookie_provider
        cookies = await xueqiu_cookie_provider.get_cookies(force_refresh=True)

        async with httpx.AsyncClient(
            timeout=20.0,
            trust_env=False,
            follow_redirects=True,
        ) as client:
            url = "https://xueqiu.com/hot_event/list.json"
            params = {"count": "20"}
            headers = {**self._http_headers, "Referer": "https://xueqiu.com/"}
            resp = await client.get(url, params=params, headers=headers, cookies=cookies)
            resp.raise_for_status()
            data = self._xueqiu_validate_json(resp, "雪球热门话题API(备用)")

        for idx, item in enumerate(data.get("list", [])):
            tag = str(item.get("tag", "")).strip().strip("#").strip()
            content = str(item.get("content", "")).strip()
            status_count = item.get("status_count", 0)
            topic_id = item.get("id", "")
            if not tag:
                continue
            items.append(StockNewsItem(
                id=f"xueqiu_hot_{idx}",
                title=tag,
                summary=content[:300] if content else tag,
                source_platform="xueqiu",
                source_name="雪球",
                url=f"https://xueqiu.com/hashtag/{base64.urlsafe_b64encode(item.get('tag', '').encode('utf-8')).decode('ascii')}" if item.get('tag') else "",
                published_time=datetime.now().isoformat(),
                hot_value=str(status_count),
                rank=idx + 1,
                category="domestic",
            ))
        logger.info(f"✓ 雪球热门话题(备用): {len(items)} 条")
        return items

    # ------------------------------------------------------------------
    # Tushare（可选，需 token）
    # ------------------------------------------------------------------

    async def fetch_tushare_news(self) -> List[StockNewsItem]:
        """通过 Tushare 免费层采集新闻快讯（需 token）"""
        source_id = "tushare"
        items: List[StockNewsItem] = []
        token = Config.TUSHARE_TOKEN
        if not token:
            logger.info("ℹ️ Tushare token 未配置，跳过")
            return items

        await self.rate_limiter.acquire(source_id)
        try:
            import tushare as ts
            pro = await asyncio.to_thread(ts.pro_api, token)
            today = datetime.now().strftime("%Y%m%d")
            df = await asyncio.to_thread(
                pro.news,
                src="sina",
                start_date=today,
                end_date=today,
            )
            if df is not None and not df.empty:
                for idx, row in df.head(Config.STOCK_NEWS_CONFIG.get("max_items_per_source", 50)).iterrows():
                    title = str(row.get("title", "")).strip()
                    content = str(row.get("content", "")).strip()
                    pub_time = str(row.get("datetime", "")).strip()
                    if not title:
                        continue
                    items.append(StockNewsItem(
                        id=f"tushare_{idx}",
                        title=title,
                        summary=content[:200] if content else title,
                        source_platform="tushare",
                        source_name="Tushare",
                        url="",
                        published_time=pub_time or datetime.now().isoformat(),
                        hot_value="",
                        rank=idx + 1,
                        category="domestic",
                    ))
            logger.info(f"✓ Tushare: {len(items)} 条")
            self.rate_limiter.reset_fail_count(source_id)
        except Exception as e:
            logger.error(f"❌ Tushare 采集失败: {e}")
            await self.rate_limiter.handle_failure(source_id)
        finally:
            self.rate_limiter.release(source_id)
        return items

    # ------------------------------------------------------------------
    # 数据源调度映射
    # ------------------------------------------------------------------

    def _get_fetch_method(self, source_id: str):
        """根据 source_id 返回对应的采集方法"""
        mapping = {
            "akshare": self.fetch_akshare_news,
            "sina": self.fetch_sina_news,
            "10jqka": self.fetch_10jqka_news,
            "xueqiu": self.fetch_xueqiu_news,
            "tushare": self.fetch_tushare_news,
        }
        return mapping.get(source_id)

    # ------------------------------------------------------------------
    # 核心采集入口
    # ------------------------------------------------------------------

    async def collect_news(
        self,
        source_ids: Optional[List[str]] = None,
        force_refresh: bool = False,
        include_international: bool = False,
        include_research: bool = False,
        research_symbols: Optional[List[str]] = None,
    ) -> StockNewsCollectResponse:
        """采集股票资讯，支持国内数据源、国际财经新闻和投行研报。

        Args:
            source_ids: 指定国内数据源列表，None 表示所有已启用的源
            force_refresh: 是否强制刷新（跳过缓存）
            include_international: 是否包含国际财经新闻
            include_research: 是否包含投行研报
            research_symbols: 投行研报查询的股票代码列表（如 ["AAPL", "MSFT"]）

        Returns:
            StockNewsCollectResponse
        """
        # Build cache key based on parameters
        cache_suffix_parts = ["stock"]
        if include_international:
            cache_suffix_parts.append("intl")
        if include_research:
            cache_suffix_parts.append("research")
        cache_key = "_".join(cache_suffix_parts)

        # 缓存检查
        if not force_refresh and self.use_cache and self.cache_service:
            cached = self.cache_service.get_cached_data(cache_key=cache_key)
            if cached:
                logger.info("📦 使用股票资讯缓存数据")
                return StockNewsCollectResponse(
                    success=True,
                    items=[StockNewsItem(**i) for i in cached.get("items", [])],
                    total=cached.get("total", 0),
                    source_stats=cached.get("source_stats", {}),
                    category_stats=cached.get("category_stats", {}),
                    collection_time=cached.get("collection_time", ""),
                    from_cache=True,
                )

        logger.info("🚀 开始采集股票资讯...")

        # 确定要采集的国内数据源
        if source_ids is None:
            source_ids = [
                sid for sid, cfg in self.sources.items()
                if cfg.get("enabled", True)
            ]

        # 并发采集：国内源 + 国际源 + 投行研报
        domestic_tasks = []
        domestic_source_ids = []
        for sid in source_ids:
            method = self._get_fetch_method(sid)
            if method:
                domestic_tasks.append(self._safe_fetch(sid, method))
                domestic_source_ids.append(sid)
            else:
                logger.warning(f"未知数据源: {sid}")

        # Build concurrent tasks
        gather_tasks = list(domestic_tasks)
        intl_task_idx = None
        research_task_idx = None

        if include_international:
            intl_task_idx = len(gather_tasks)
            gather_tasks.append(
                self._safe_fetch_international(force_refresh)
            )

        if include_research and research_symbols:
            research_task_idx = len(gather_tasks)
            gather_tasks.append(
                self._safe_fetch_research(research_symbols, force_refresh)
            )

        results = await asyncio.gather(*gather_tasks)

        # 合并国内源结果
        all_items: List[StockNewsItem] = []
        source_stats: Dict[str, int] = {}
        for i, sid in enumerate(domestic_source_ids):
            items = results[i]
            source_stats[sid] = len(items)
            all_items.extend(items)

        # 合并国际财经新闻
        if intl_task_idx is not None:
            intl_items = results[intl_task_idx]
            source_stats["international"] = len(intl_items)
            all_items.extend(intl_items)

        # 合并投行研报
        if research_task_idx is not None:
            research_items = results[research_task_idx]
            source_stats["research_report"] = len(research_items)
            all_items.extend(research_items)

        # 统计各类别数量
        category_stats: Dict[str, int] = {}
        for item in all_items:
            cat = item.category or "domestic"
            category_stats[cat] = category_stats.get(cat, 0) + 1

        # 计算统一热度评分（0-100）
        _calculate_heat_scores(all_items)

        collection_time = datetime.now().isoformat()

        response = StockNewsCollectResponse(
            success=True,
            items=all_items,
            total=len(all_items),
            source_stats=source_stats,
            category_stats=category_stats,
            collection_time=collection_time,
            from_cache=False,
        )

        # 保存缓存
        if self.use_cache and self.cache_service:
            cache_data = {
                "items": [item.model_dump() for item in all_items],
                "total": len(all_items),
                "source_stats": source_stats,
                "category_stats": category_stats,
                "collection_time": collection_time,
            }
            self.cache_service.save_to_cache(cache_data, cache_key=cache_key)

        logger.info(
            f"📈 股票资讯采集完成: {len(all_items)} 条, "
            f"数据源: {source_stats}, 类别: {category_stats}"
        )
        return response

    # ------------------------------------------------------------------
    # 热榜聚类采集（新浪 + 东方财富 + 雪球 + 同花顺）
    # ------------------------------------------------------------------

    # 热榜数据源：只用这 4 个国内平台
    HOT_SOURCE_IDS = ["akshare", "sina", "xueqiu", "10jqka"]

    async def collect_hot_news(
        self,
        force_refresh: bool = False,
    ) -> Dict:
        """采集热榜数据并执行话题聚类 + 统一评分 + 历史信号。

        Returns:
            前端友好的 dict，包含 clusters 列表和元数据
        """
        cache_key = "stock_hot_aligned"

        # 缓存检查
        if not force_refresh and self.use_cache and self.cache_service:
            cached = self.cache_service.get_cached_data(cache_key=cache_key)
            if cached:
                logger.info("📦 使用热榜聚类缓存数据")
                return cached

        logger.info("🔥 开始采集热榜数据（聚类模式）...")

        # 并发采集 4 个源
        tasks = []
        task_sids = []
        for sid in self.HOT_SOURCE_IDS:
            method = self._get_fetch_method(sid)
            if method:
                tasks.append(self._safe_fetch(sid, method))
                task_sids.append(sid)

        results = await asyncio.gather(*tasks)

        # 转换为 RawItem
        from app.services.hotnews_alignment import (
            make_raw_item, align_and_score, clusters_to_api,
        )

        raw_items = []
        source_stats: Dict[str, int] = {}
        for sid, items in zip(task_sids, results):
            source_stats[sid] = len(items)
            for item in items:
                raw_items.append(make_raw_item(
                    platform_id=item.source_platform,
                    source_name=item.source_name,
                    title=item.title,
                    url=item.url,
                    hot_value=item.hot_value,
                    rank=item.rank,
                    published_time=item.published_time,
                    summary=item.summary,
                    original_id=item.id,
                    category="domestic",
                ))

        # 加载上次快照
        prev_snapshot = None
        if self.use_cache and self.cache_service:
            prev_data = self.cache_service.get_cached_data(cache_key="stock_hot_snapshot")
            if prev_data:
                prev_snapshot = prev_data

        # 执行聚类 pipeline
        collection_time = datetime.now().isoformat()
        clusters, new_snapshot = align_and_score(
            raw_items, prev_snapshot=prev_snapshot,
        )

        # 转换为 API 格式，只取前20个话题
        cluster_list = clusters_to_api(clusters[:20], collection_time=collection_time)

        result = {
            "success": True,
            "clusters": cluster_list,
            "total": len(cluster_list),
            "raw_count": len(raw_items),
            "source_stats": source_stats,
            "cross_platform_count": sum(
                1 for c in cluster_list if c.get("platform_count", 1) > 1
            ),
            "collection_time": collection_time,
            "from_cache": False,
        }

        # 保存缓存和快照
        if self.use_cache and self.cache_service:
            self.cache_service.save_to_cache(result, cache_key=cache_key)
            if new_snapshot:
                self.cache_service.save_to_cache(new_snapshot, cache_key="stock_hot_snapshot")

        logger.info(
            f"🔥 热榜聚类完成: {len(cluster_list)} 个话题, "
            f"跨平台: {result['cross_platform_count']} 个, "
            f"原始数据: {len(raw_items)} 条"
        )
        return result

    async def _safe_fetch_international(self, force_refresh: bool) -> List[StockNewsItem]:
        """安全采集国际财经新闻，异常时返回空列表"""
        try:
            return await self.intl_news_service.collect_international_news(
                force_refresh=force_refresh,
            )
        except Exception as e:
            logger.error(f"❌ 国际财经新闻采集异常: {e}")
            return []

    async def _safe_fetch_research(
        self, symbols: List[str], force_refresh: bool,
    ) -> List[StockNewsItem]:
        """安全采集投行研报并转换为 StockNewsItem，异常时返回空列表"""
        try:
            result = await self.research_service.collect_research_reports(
                symbols=symbols,
                force_refresh=force_refresh,
            )
            ratings = result.get("ratings", [])
            return self.research_service.convert_to_news_items(ratings)
        except Exception as e:
            logger.error(f"❌ 投行研报采集异常: {e}")
            return []

    async def _safe_fetch(self, source_id: str, method) -> List[StockNewsItem]:
        """安全执行采集方法，捕获异常返回空列表"""
        try:
            return await method()
        except Exception as e:
            logger.error(f"❌ 数据源 {source_id} 采集异常: {e}")
            return []


# ---------------------------------------------------------------------------
# 统一热度评分算法（0-100 跨源归一化）
# ---------------------------------------------------------------------------

def _parse_raw_heat(item: StockNewsItem) -> float:
    """将各数据源的 hot_value 原始字符串解析为数值。

    不同源的 hot_value 含义不同：
    - akshare 热股: 东方财富热度数值（如 "3856421"）
    - 10jqka: 同花顺热度数值（如 "8523"）
    - xueqiu: 涨跌幅百分比（如 "3.5%"）或回复数
    - sina/tushare: 空字符串（新闻类无热度）
    """
    raw = (item.hot_value or "").strip()
    if not raw:
        return 0.0
    try:
        cleaned = raw.replace(",", "").replace("%", "").replace("万", "0000").strip()
        return abs(float(cleaned))
    except (ValueError, TypeError):
        return 0.0


def _time_decay_factor(published_time: str) -> float:
    """基于发布时间计算衰减因子（0.3 ~ 1.0）。

    1小时内 = 1.0，6小时 ≈ 0.7，24小时 ≈ 0.3
    """
    try:
        pub_dt = datetime.fromisoformat(published_time.replace("Z", "+00:00"))
        if pub_dt.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        hours_ago = max(0, (now - pub_dt).total_seconds() / 3600)
    except (ValueError, TypeError):
        hours_ago = 12  # 解析失败给中间值

    # 指数衰减: e^(-0.05 * hours)，clamp 到 [0.3, 1.0]
    import math
    decay = math.exp(-0.05 * hours_ago)
    return max(0.3, min(1.0, decay))


def _calculate_heat_scores(items: List[StockNewsItem]) -> None:
    """为所有条目计算统一热度评分（0-100），直接修改 item.heat_score。

    算法：
    1. 排名分（40%）：同源内 rank 越小分越高，归一化到 0-100
    2. 原始热度分（40%）：同源内 min-max 归一化到 0-100
    3. 时间衰减（20%）：越新分越高

    最终 heat_score = rank_score * 0.4 + heat_norm * 0.4 + time_score * 0.2
    """
    if not items:
        return

    # 按 source_platform 分组
    by_source: Dict[str, List[StockNewsItem]] = {}
    for item in items:
        by_source.setdefault(item.source_platform, []).append(item)

    for source, group in by_source.items():
        n = len(group)

        # --- 排名分：rank 越小越好 ---
        for item in group:
            rank = item.rank or n  # 无 rank 的排最后
            # 线性映射: rank=1 → 100, rank=n → max(10, 100-n)
            if n > 1:
                rank_score = 100 - (rank - 1) * 90 / (n - 1)
            else:
                rank_score = 100.0
            rank_score = max(0, min(100, rank_score))
            item._rank_score = rank_score  # type: ignore

        # --- 原始热度分：同源 min-max 归一化 ---
        raw_heats = [_parse_raw_heat(item) for item in group]
        min_h = min(raw_heats)
        max_h = max(raw_heats)
        heat_range = max_h - min_h

        for item, raw_h in zip(group, raw_heats):
            if heat_range > 0 and raw_h > 0:
                heat_norm = ((raw_h - min_h) / heat_range) * 100
            elif raw_h > 0:
                heat_norm = 50.0  # 所有值相同且非零
            else:
                heat_norm = 0.0  # 无热度值的新闻类
            item._heat_norm = heat_norm  # type: ignore

        # --- 时间衰减分 ---
        for item in group:
            time_factor = _time_decay_factor(item.published_time)
            item._time_score = time_factor * 100  # type: ignore

        # --- 综合评分 ---
        for item in group:
            score = (
                item._rank_score * 0.4  # type: ignore
                + item._heat_norm * 0.4  # type: ignore
                + item._time_score * 0.2  # type: ignore
            )
            item.heat_score = round(max(0, min(100, score)), 1)

            # 清理临时属性
            del item._rank_score  # type: ignore
            del item._heat_norm  # type: ignore
            del item._time_score  # type: ignore

    # 按 heat_score 降序排列
    items.sort(key=lambda x: x.heat_score or 0, reverse=True)


# ---------------------------------------------------------------------------
# 全局实例
# ---------------------------------------------------------------------------

stock_news_collector = StockNewsCollector()
