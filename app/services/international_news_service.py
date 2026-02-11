#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国际财经新闻采集服务
聚合 Finnhub、NewsAPI、Alpha Vantage、GDELT、Google News RSS、Marketaux 等数据源
英文内容通过 LLM 批量翻译为中文摘要
"""

import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from loguru import logger

from app.config import Config
from app.schemas import StockNewsItem


# ---------------------------------------------------------------------------
# 国际数据源配置
# ---------------------------------------------------------------------------

INTERNATIONAL_SOURCES: Dict[str, Dict] = {
    "finnhub": {
        "name": "Finnhub",
        "enabled": True,
        "requires_api_key": True,
        "api_key_env": "FINNHUB_API_KEY",
    },
    "newsapi": {
        "name": "NewsAPI",
        "enabled": True,
        "requires_api_key": True,
        "api_key_env": "NEWSAPI_API_KEY",
    },
    "alpha_vantage": {
        "name": "Alpha Vantage",
        "enabled": True,
        "requires_api_key": True,
        "api_key_env": "ALPHA_VANTAGE_API_KEY",
    },
    "gdelt": {
        "name": "GDELT Project",
        "enabled": True,
        "requires_api_key": False,
    },
    "google_rss": {
        "name": "Google News RSS",
        "enabled": True,
        "requires_api_key": False,
    },
    "marketaux": {
        "name": "Marketaux",
        "enabled": True,
        "requires_api_key": True,
        "api_key_env": "MARKETAUX_API_KEY",
    },
}


class InternationalNewsService:
    """国际财经新闻采集服务，聚合多个免费/免费层 API"""

    def __init__(self, use_cache: bool = True):
        self.sources = INTERNATIONAL_SOURCES
        self.use_cache = use_cache

        if self.use_cache:
            from app.services.hot_news_cache import hot_news_cache
            self.cache_service = hot_news_cache
        else:
            self.cache_service = None

        self._http_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/html, */*",
        }

    # ------------------------------------------------------------------
    # Helper: check if API key is available
    # ------------------------------------------------------------------

    def _get_api_key(self, source_id: str) -> Optional[str]:
        """Return the API key for a source, or None if not configured."""
        key_map = {
            "finnhub": Config.FINNHUB_API_KEY,
            "newsapi": Config.NEWSAPI_API_KEY,
            "alpha_vantage": Config.ALPHA_VANTAGE_API_KEY,
            "marketaux": Config.MARKETAUX_API_KEY,
        }
        key = key_map.get(source_id, "")
        return key if key else None

    def _is_source_available(self, source_id: str) -> bool:
        """Check if a source is enabled and has required API key."""
        cfg = self.sources.get(source_id)
        if not cfg or not cfg.get("enabled", True):
            return False
        if cfg.get("requires_api_key") and not self._get_api_key(source_id):
            return False
        return True


    # ------------------------------------------------------------------
    # Finnhub
    # ------------------------------------------------------------------

    async def fetch_finnhub_news(self, category: str = "general") -> List[StockNewsItem]:
        """Finnhub 国际财经新闻采集。

        免费层 60 calls/min。
        端点: /api/v1/news?category=general
        """
        source_id = "finnhub"
        if not self._is_source_available(source_id):
            logger.info(f"ℹ️ {source_id} 未配置 API Key，跳过")
            return []

        items: List[StockNewsItem] = []
        api_key = self._get_api_key(source_id)
        max_items = Config.INTERNATIONAL_NEWS_CONFIG.get("max_items_per_source", 30)

        try:
            url = "https://finnhub.io/api/v1/news"
            params = {"category": category, "token": api_key}
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, params=params, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            if not isinstance(data, list):
                data = []

            for idx, article in enumerate(data[:max_items]):
                title = str(article.get("headline", "")).strip()
                if not title:
                    continue
                summary = str(article.get("summary", "")).strip()
                source_name = str(article.get("source", "Finnhub")).strip()
                news_url = str(article.get("url", "")).strip()
                ts = article.get("datetime", 0)
                try:
                    pub_time = datetime.fromtimestamp(int(ts)).isoformat() if ts else datetime.now().isoformat()
                except (ValueError, TypeError, OSError):
                    pub_time = datetime.now().isoformat()

                items.append(StockNewsItem(
                    id=f"finnhub_{idx}",
                    title=title,
                    summary=summary[:300] if summary else title,
                    source_platform="finnhub",
                    source_name=f"Finnhub - {source_name}",
                    url=news_url,
                    published_time=pub_time,
                    hot_value="",
                    rank=idx + 1,
                    category="international",
                    original_language="en",
                    is_ai_translated=False,
                ))
            logger.info(f"✓ Finnhub: {len(items)} 条")
        except Exception as e:
            logger.error(f"❌ Finnhub 采集失败: {e}")
        return items

    # ------------------------------------------------------------------
    # NewsAPI
    # ------------------------------------------------------------------

    async def fetch_newsapi_news(self, query: str = "stock market finance") -> List[StockNewsItem]:
        """NewsAPI 国际财经新闻采集。

        免费开发者层 100 requests/day。
        按金融/股票关键词筛选。
        """
        source_id = "newsapi"
        if not self._is_source_available(source_id):
            logger.info(f"ℹ️ {source_id} 未配置 API Key，跳过")
            return []

        items: List[StockNewsItem] = []
        api_key = self._get_api_key(source_id)
        max_items = Config.INTERNATIONAL_NEWS_CONFIG.get("max_items_per_source", 30)

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": str(min(max_items, 100)),
                "apiKey": api_key,
            }
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, params=params, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            articles = data.get("articles", [])
            for idx, article in enumerate(articles[:max_items]):
                title = str(article.get("title", "")).strip()
                if not title or title == "[Removed]":
                    continue
                description = str(article.get("description", "")).strip()
                news_url = str(article.get("url", "")).strip()
                source_obj = article.get("source", {})
                source_name = str(source_obj.get("name", "NewsAPI")).strip()
                pub_at = str(article.get("publishedAt", "")).strip()

                items.append(StockNewsItem(
                    id=f"newsapi_{idx}",
                    title=title,
                    summary=description[:300] if description else title,
                    source_platform="newsapi",
                    source_name=f"NewsAPI - {source_name}",
                    url=news_url,
                    published_time=pub_at or datetime.now().isoformat(),
                    hot_value="",
                    rank=idx + 1,
                    category="international",
                    original_language="en",
                    is_ai_translated=False,
                ))
            logger.info(f"✓ NewsAPI: {len(items)} 条")
        except Exception as e:
            logger.error(f"❌ NewsAPI 采集失败: {e}")
        return items

    # ------------------------------------------------------------------
    # Alpha Vantage
    # ------------------------------------------------------------------

    async def fetch_alpha_vantage_news(self, tickers: Optional[str] = "AAPL,MSFT,GOOGL") -> List[StockNewsItem]:
        """Alpha Vantage NEWS_SENTIMENT 端点。

        免费层 25 requests/day。提取情绪分析评分。
        """
        source_id = "alpha_vantage"
        if not self._is_source_available(source_id):
            logger.info(f"ℹ️ {source_id} 未配置 API Key，跳过")
            return []

        items: List[StockNewsItem] = []
        api_key = self._get_api_key(source_id)
        max_items = Config.INTERNATIONAL_NEWS_CONFIG.get("max_items_per_source", 30)

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "apikey": api_key,
            }
            if tickers:
                params["tickers"] = tickers

            async with httpx.AsyncClient(timeout=20.0, trust_env=False) as client:
                resp = await client.get(url, params=params, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            feed = data.get("feed", [])
            for idx, article in enumerate(feed[:max_items]):
                title = str(article.get("title", "")).strip()
                if not title:
                    continue
                summary = str(article.get("summary", "")).strip()
                news_url = str(article.get("url", "")).strip()
                source_name = str(article.get("source", "Alpha Vantage")).strip()
                pub_time = str(article.get("time_published", "")).strip()

                # Extract sentiment
                sentiment_score = article.get("overall_sentiment_score", 0)
                sentiment_label = article.get("overall_sentiment_label", "Neutral")
                sentiment = _map_av_sentiment(sentiment_label)

                items.append(StockNewsItem(
                    id=f"alpha_vantage_{idx}",
                    title=title,
                    summary=summary[:300] if summary else title,
                    source_platform="alpha_vantage",
                    source_name=f"Alpha Vantage - {source_name}",
                    url=news_url,
                    published_time=_parse_av_time(pub_time),
                    hot_value="",
                    rank=idx + 1,
                    category="international",
                    original_language="en",
                    sentiment=sentiment,
                    is_ai_translated=False,
                ))
            logger.info(f"✓ Alpha Vantage: {len(items)} 条")
        except Exception as e:
            logger.error(f"❌ Alpha Vantage 采集失败: {e}")
        return items


    # ------------------------------------------------------------------
    # GDELT
    # ------------------------------------------------------------------

    async def fetch_gdelt_news(self, theme: str = "ECON_STOCKMARKET") -> List[StockNewsItem]:
        """GDELT Project GKG/DOC API 全球金融新闻。

        完全免费，无需 API Key。按 ECON_STOCKMARKET 主题过滤。
        """
        items: List[StockNewsItem] = []
        max_items = Config.INTERNATIONAL_NEWS_CONFIG.get("max_items_per_source", 30)

        try:
            url = "https://api.gdeltproject.org/api/v2/doc/doc"
            params = {
                "query": f"theme:{theme}",
                "mode": "artlist",
                "maxrecords": str(min(max_items, 75)),
                "format": "json",
                "sort": "datedesc",
            }
            async with httpx.AsyncClient(timeout=20.0, trust_env=False) as client:
                resp = await client.get(url, params=params, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            articles = data.get("articles", [])
            for idx, article in enumerate(articles[:max_items]):
                title = str(article.get("title", "")).strip()
                if not title:
                    continue
                news_url = str(article.get("url", "")).strip()
                source_name = str(article.get("domain", "GDELT")).strip()
                seendate = str(article.get("seendate", "")).strip()

                items.append(StockNewsItem(
                    id=f"gdelt_{idx}",
                    title=title,
                    summary=title,  # GDELT artlist doesn't provide summaries
                    source_platform="gdelt",
                    source_name=f"GDELT - {source_name}",
                    url=news_url,
                    published_time=_parse_gdelt_time(seendate),
                    hot_value="",
                    rank=idx + 1,
                    category="international",
                    original_language="en",
                    is_ai_translated=False,
                ))
            logger.info(f"✓ GDELT: {len(items)} 条")
        except Exception as e:
            logger.error(f"❌ GDELT 采集失败: {e}")
        return items

    # ------------------------------------------------------------------
    # Google News RSS
    # ------------------------------------------------------------------

    async def fetch_google_news_rss(self, query: str = "stock market finance") -> List[StockNewsItem]:
        """Google News RSS feed 财经新闻。

        完全免费，无需 API Key。使用 feedparser 解析。
        """
        items: List[StockNewsItem] = []
        max_items = Config.INTERNATIONAL_NEWS_CONFIG.get("max_items_per_source", 30)

        try:
            import feedparser
            from urllib.parse import quote_plus

            encoded_query = quote_plus(query)
            rss_url = (
                f"https://news.google.com/rss/search"
                f"?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            )
            # feedparser is synchronous, wrap in thread
            feed = await asyncio.to_thread(feedparser.parse, rss_url)

            entries = feed.get("entries", [])
            for idx, entry in enumerate(entries[:max_items]):
                title = str(entry.get("title", "")).strip()
                if not title:
                    continue
                link = str(entry.get("link", "")).strip()
                summary = str(entry.get("summary", "")).strip()
                published = str(entry.get("published", "")).strip()
                source_name = str(entry.get("source", {}).get("title", "Google News")).strip() if isinstance(entry.get("source"), dict) else "Google News"

                items.append(StockNewsItem(
                    id=f"google_rss_{idx}",
                    title=title,
                    summary=summary[:300] if summary else title,
                    source_platform="google_rss",
                    source_name=f"Google RSS - {source_name}",
                    url=link,
                    published_time=_parse_rss_time(published),
                    hot_value="",
                    rank=idx + 1,
                    category="international",
                    original_language="en",
                    is_ai_translated=False,
                ))
            logger.info(f"✓ Google News RSS: {len(items)} 条")
        except Exception as e:
            logger.error(f"❌ Google News RSS 采集失败: {e}")
        return items

    # ------------------------------------------------------------------
    # Marketaux
    # ------------------------------------------------------------------

    async def fetch_marketaux_news(self, symbols: Optional[str] = None) -> List[StockNewsItem]:
        """Marketaux 金融新闻 API。

        免费层 100 requests/day。提取情绪标签。
        """
        source_id = "marketaux"
        if not self._is_source_available(source_id):
            logger.info(f"ℹ️ {source_id} 未配置 API Key，跳过")
            return []

        items: List[StockNewsItem] = []
        api_key = self._get_api_key(source_id)
        max_items = Config.INTERNATIONAL_NEWS_CONFIG.get("max_items_per_source", 30)

        try:
            url = "https://api.marketaux.com/v1/news/all"
            params = {
                "api_token": api_key,
                "language": "en",
                "filter_entities": "true",
                "limit": str(min(max_items, 50)),
            }
            if symbols:
                params["symbols"] = symbols

            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, params=params, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            articles = data.get("data", [])
            for idx, article in enumerate(articles[:max_items]):
                title = str(article.get("title", "")).strip()
                if not title:
                    continue
                description = str(article.get("description", "")).strip()
                snippet = str(article.get("snippet", "")).strip()
                news_url = str(article.get("url", "")).strip()
                source_name = str(article.get("source", "Marketaux")).strip()
                pub_at = str(article.get("published_at", "")).strip()

                # Extract sentiment from entities
                sentiment = _extract_marketaux_sentiment(article.get("entities", []))

                items.append(StockNewsItem(
                    id=f"marketaux_{idx}",
                    title=title,
                    summary=(description or snippet)[:300] if (description or snippet) else title,
                    source_platform="marketaux",
                    source_name=f"Marketaux - {source_name}",
                    url=news_url,
                    published_time=pub_at or datetime.now().isoformat(),
                    hot_value="",
                    rank=idx + 1,
                    category="international",
                    original_language="en",
                    sentiment=sentiment,
                    is_ai_translated=False,
                ))
            logger.info(f"✓ Marketaux: {len(items)} 条")
        except Exception as e:
            logger.error(f"❌ Marketaux 采集失败: {e}")
        return items


    # ------------------------------------------------------------------
    # LLM 批量翻译
    # ------------------------------------------------------------------

    async def batch_translate_to_chinese(
        self,
        news_items: List[StockNewsItem],
        max_items: int = 20,
    ) -> List[StockNewsItem]:
        """批量调用 LLM 将英文新闻翻译为中文摘要。

        - 合并为一次 LLM 调用，每批最多 max_items 条
        - 超出时分批处理
        - LLM prompt 强调"严格基于原文翻译，不添加任何原文没有的信息"
        - 翻译后标记 is_ai_translated=True
        """
        if not news_items:
            return news_items

        # Filter items that need translation (English, not yet translated)
        to_translate = [
            item for item in news_items
            if item.original_language == "en" and not item.is_ai_translated
        ]
        if not to_translate:
            return news_items

        # Process in batches
        translated_map: Dict[str, str] = {}  # id -> translated summary
        for batch_start in range(0, len(to_translate), max_items):
            batch = to_translate[batch_start:batch_start + max_items]
            batch_translations = await self._translate_batch(batch)
            translated_map.update(batch_translations)

        # Apply translations
        result = []
        for item in news_items:
            if item.id in translated_map:
                item.summary = translated_map[item.id]
                item.is_ai_translated = True
            result.append(item)

        logger.info(f"✓ 批量翻译完成: {len(translated_map)}/{len(to_translate)} 条")
        return result

    async def _translate_batch(self, batch: List[StockNewsItem]) -> Dict[str, str]:
        """Translate a single batch of news items via LLM."""
        translations: Dict[str, str] = {}
        try:
            from app.llm import get_agent_llm

            llm = get_agent_llm("translator")

            # Build prompt
            news_text_parts = []
            for i, item in enumerate(batch):
                text = item.summary if item.summary and item.summary != item.title else item.title
                news_text_parts.append(f"[{i+1}] {text}")

            news_block = "\n".join(news_text_parts)

            prompt = (
                "你是一个专业的财经新闻翻译助手。请严格基于以下英文新闻原文进行翻译，"
                "不添加任何原文没有的信息，不做任何推测或补充。\n"
                "保留所有数字、公司名称、股票代码等关键数据。\n"
                "每条新闻生成 100-200 字的中文摘要。\n\n"
                "请按照以下格式输出，每条翻译用 [序号] 开头：\n\n"
                f"{news_block}\n\n"
                "请逐条翻译，格式为：\n"
                "[1] 中文摘要...\n"
                "[2] 中文摘要...\n"
                "..."
            )

            result = await llm.ainvoke([{"role": "user", "content": prompt}])
            response_text = result.content if hasattr(result, "content") else str(result)

            # Parse response
            import re
            pattern = r"\[(\d+)\]\s*(.+?)(?=\[\d+\]|$)"
            matches = re.findall(pattern, response_text, re.DOTALL)

            for num_str, translated_text in matches:
                idx = int(num_str) - 1
                if 0 <= idx < len(batch):
                    cleaned = translated_text.strip()
                    if cleaned:
                        translations[batch[idx].id] = cleaned

        except Exception as e:
            logger.error(f"❌ LLM 批量翻译失败: {e}")
            # On failure, keep original summaries

        return translations

    # ------------------------------------------------------------------
    # 核心采集入口
    # ------------------------------------------------------------------

    async def collect_international_news(
        self,
        source_ids: Optional[List[str]] = None,
        force_refresh: bool = False,
    ) -> List[StockNewsItem]:
        """采集所有国际财经新闻源。

        Args:
            source_ids: 指定数据源列表，None 表示所有已启用的源
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            List[StockNewsItem] — 翻译后的国际新闻列表
        """
        cache_key = "intl_news_all"

        # Cache check
        if not force_refresh and self.use_cache and self.cache_service:
            cached = self.cache_service.get_cached_data(cache_key=cache_key)
            if cached:
                logger.info("📦 使用国际财经新闻缓存数据")
                return [StockNewsItem(**i) for i in cached.get("items", [])]

        logger.info("🌍 开始采集国际财经新闻...")

        # Determine sources to fetch
        if source_ids is None:
            source_ids = list(self.sources.keys())

        # Build fetch tasks
        fetch_map = {
            "finnhub": self.fetch_finnhub_news,
            "newsapi": self.fetch_newsapi_news,
            "alpha_vantage": self.fetch_alpha_vantage_news,
            "gdelt": self.fetch_gdelt_news,
            "google_rss": self.fetch_google_news_rss,
            "marketaux": self.fetch_marketaux_news,
        }

        tasks = []
        active_sources = []
        for sid in source_ids:
            method = fetch_map.get(sid)
            if method:
                tasks.append(self._safe_fetch(sid, method))
                active_sources.append(sid)

        results = await asyncio.gather(*tasks)

        # Merge results
        all_items: List[StockNewsItem] = []
        for sid, items in zip(active_sources, results):
            all_items.extend(items)

        # Deduplicate by title hash
        all_items = self._deduplicate(all_items)

        # Batch translate English content to Chinese
        try:
            batch_size = Config.INTERNATIONAL_NEWS_CONFIG.get("translate_batch_size", 20)
            all_items = await self.batch_translate_to_chinese(all_items, max_items=batch_size)
        except Exception as e:
            logger.error(f"❌ 批量翻译异常: {e}")

        # Save to cache
        if self.use_cache and self.cache_service:
            cache_data = {
                "items": [item.model_dump() for item in all_items],
                "total": len(all_items),
                "collection_time": datetime.now().isoformat(),
            }
            self.cache_service.save_to_cache(cache_data, cache_key=cache_key)

        logger.info(f"🌍 国际财经新闻采集完成: {len(all_items)} 条")
        return all_items

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _safe_fetch(self, source_id: str, method) -> List[StockNewsItem]:
        """Safely execute a fetch method, returning empty list on error."""
        try:
            return await method()
        except Exception as e:
            logger.error(f"❌ 国际数据源 {source_id} 采集异常: {e}")
            return []

    @staticmethod
    def _deduplicate(items: List[StockNewsItem]) -> List[StockNewsItem]:
        """Deduplicate items by title hash."""
        seen: set = set()
        unique: List[StockNewsItem] = []
        for item in items:
            title_hash = hashlib.md5(item.title.lower().encode()).hexdigest()
            if title_hash not in seen:
                seen.add(title_hash)
                unique.append(item)
        return unique


# ---------------------------------------------------------------------------
# Module-level helper functions
# ---------------------------------------------------------------------------

def _map_av_sentiment(label: str) -> Optional[str]:
    """Map Alpha Vantage sentiment label to our standard."""
    label_lower = (label or "").lower()
    if "bullish" in label_lower:
        return "bullish"
    elif "bearish" in label_lower:
        return "bearish"
    elif "neutral" in label_lower:
        return "neutral"
    return None


def _parse_av_time(time_str: str) -> str:
    """Parse Alpha Vantage time format (YYYYMMDDTHHmmss) to ISO 8601."""
    try:
        if "T" in time_str and len(time_str) >= 15:
            dt = datetime.strptime(time_str[:15], "%Y%m%dT%H%M%S")
            return dt.isoformat()
    except (ValueError, TypeError):
        pass
    return time_str or datetime.now().isoformat()


def _parse_gdelt_time(seendate: str) -> str:
    """Parse GDELT seendate format (YYYYMMDDTHHmmssZ) to ISO 8601."""
    try:
        if seendate and len(seendate) >= 15:
            clean = seendate.replace("Z", "")
            dt = datetime.strptime(clean[:15], "%Y%m%dT%H%M%S")
            return dt.isoformat()
    except (ValueError, TypeError):
        pass
    return seendate or datetime.now().isoformat()


def _parse_rss_time(published: str) -> str:
    """Parse RSS published time to ISO 8601."""
    if not published:
        return datetime.now().isoformat()
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(published)
        return dt.isoformat()
    except Exception:
        return published


def _extract_marketaux_sentiment(entities: list) -> Optional[str]:
    """Extract dominant sentiment from Marketaux entities."""
    if not entities:
        return None
    sentiments = []
    for entity in entities:
        score = entity.get("sentiment_score")
        if score is not None:
            try:
                sentiments.append(float(score))
            except (ValueError, TypeError):
                pass
    if not sentiments:
        return None
    avg = sum(sentiments) / len(sentiments)
    if avg > 0.15:
        return "bullish"
    elif avg < -0.15:
        return "bearish"
    return "neutral"


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

international_news_service = InternationalNewsService()
