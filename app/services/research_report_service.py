#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投行研报与分析师评级采集服务
支持分层优先级（Tier 1-4）和降级策略
数据源：Finnhub、Yahoo Finance、Finviz、Zacks、Benzinga、Seeking Alpha、
        TipRanks、MarketBeat、Simply Wall St、Last10K、Wisesheets
"""

import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from loguru import logger

from app.config import Config
from app.schemas import AnalystRating, ConsensusRating, StockNewsItem


# ---------------------------------------------------------------------------
# 评级标准化映射
# ---------------------------------------------------------------------------

_BUY_KEYWORDS = {
    "buy", "strong buy", "strongbuy", "outperform", "overweight",
    "positive", "accumulate", "add", "top pick", "conviction buy",
    "sector outperform", "market outperform",
}
_HOLD_KEYWORDS = {
    "hold", "neutral", "equal-weight", "equal weight", "equalweight",
    "market perform", "sector perform", "in-line", "inline",
    "peer perform", "sector weight", "mixed",
}
_SELL_KEYWORDS = {
    "sell", "strong sell", "strongsell", "underperform", "underweight",
    "negative", "reduce", "avoid", "sector underperform",
    "market underperform",
}


def normalize_rating(raw_rating: str) -> str:
    """将各平台的评级标准化为 buy/hold/sell。

    匹配逻辑：先尝试精确匹配（小写），再尝试包含匹配。
    无法识别时返回 "hold" 作为默认值。
    """
    if not raw_rating:
        return "hold"
    lower = raw_rating.strip().lower()

    # Exact match first
    if lower in _BUY_KEYWORDS:
        return "buy"
    if lower in _HOLD_KEYWORDS:
        return "hold"
    if lower in _SELL_KEYWORDS:
        return "sell"

    # Substring match
    for kw in _BUY_KEYWORDS:
        if kw in lower:
            return "buy"
    for kw in _SELL_KEYWORDS:
        if kw in lower:
            return "sell"
    for kw in _HOLD_KEYWORDS:
        if kw in lower:
            return "hold"

    # Zacks Rank: 1-2 = buy, 3 = hold, 4-5 = sell
    if lower in ("1", "2"):
        return "buy"
    if lower == "3":
        return "hold"
    if lower in ("4", "5"):
        return "sell"

    return "hold"


# ---------------------------------------------------------------------------
# 数据源分层配置
# ---------------------------------------------------------------------------

RESEARCH_SOURCE_TIERS: Dict[int, List[str]] = {
    1: ["finnhub_research", "yahoo"],
    2: ["finviz", "zacks"],
    3: [],  # Benzinga/SeekingAlpha 已移除（付费源）
    4: ["tipranks", "marketbeat", "simplywallst", "last10k", "wisesheets"],
}

RESEARCH_SOURCES: Dict[str, Dict] = {
    "finnhub_research": {
        "name": "Finnhub Research",
        "tier": 1,
        "requires_api_key": True,
        "api_key_env": "FINNHUB_API_KEY",
    },
    "yahoo": {
        "name": "Yahoo Finance",
        "tier": 1,
        "requires_api_key": False,
    },
    "finviz": {
        "name": "Finviz",
        "tier": 2,
        "requires_api_key": False,
    },
    "zacks": {
        "name": "Zacks",
        "tier": 2,
        "requires_api_key": False,
    },
    "benzinga": {
        "name": "Benzinga (已移除)",
        "tier": 3,
        "requires_api_key": True,
        "api_key_env": "BENZINGA_API_KEY",
        "enabled": False,
    },
    "seekingalpha": {
        "name": "Seeking Alpha (已移除)",
        "tier": 3,
        "requires_api_key": True,
        "api_key_env": "SEEKING_ALPHA_API_KEY",
        "enabled": False,
    },
    "tipranks": {"name": "TipRanks", "tier": 4, "requires_api_key": False},
    "marketbeat": {"name": "MarketBeat", "tier": 4, "requires_api_key": False},
    "simplywallst": {"name": "Simply Wall St", "tier": 4, "requires_api_key": False},
    "last10k": {"name": "Last10K", "tier": 4, "requires_api_key": False},
    "wisesheets": {"name": "Wisesheets", "tier": 4, "requires_api_key": False},
}



# ---------------------------------------------------------------------------
# ResearchReportService
# ---------------------------------------------------------------------------

class ResearchReportService:
    """投行研报与分析师评级采集服务，支持分层优先级和降级策略"""

    def __init__(self, use_cache: bool = True):
        self.sources = RESEARCH_SOURCES
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
    # Helper: API key availability
    # ------------------------------------------------------------------

    def _get_api_key(self, source_id: str) -> Optional[str]:
        key_map = {
            "finnhub_research": Config.FINNHUB_API_KEY,
        }
        key = key_map.get(source_id, "")
        return key if key else None

    def _is_source_available(self, source_id: str) -> bool:
        cfg = self.sources.get(source_id)
        if not cfg:
            return False
        if cfg.get("enabled") is False:
            return False
        if cfg.get("requires_api_key") and not self._get_api_key(source_id):
            return False
        return True

    # ------------------------------------------------------------------
    # Tier 1: Finnhub Research (分析师推荐趋势)
    # ------------------------------------------------------------------

    async def fetch_finnhub_recommendations(self, symbol: str) -> List[AnalystRating]:
        """Finnhub /stock/recommendation 端点。

        返回按月的 buy/hold/sell/strongBuy/strongSell 结构化计数。
        免费层 60 calls/min，需 API Key。
        """
        source_id = "finnhub_research"
        if not self._is_source_available(source_id):
            logger.info(f"ℹ️ {source_id} 未配置 API Key，跳过")
            return []

        ratings: List[AnalystRating] = []
        api_key = self._get_api_key(source_id)

        try:
            url = "https://finnhub.io/api/v1/stock/recommendation"
            params = {"symbol": symbol, "token": api_key}
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, params=params, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            if not isinstance(data, list):
                data = []

            for entry in data[:12]:  # Last 12 months max
                period = str(entry.get("period", "")).strip()
                buy = entry.get("buy", 0) + entry.get("strongBuy", 0)
                hold = entry.get("hold", 0)
                sell = entry.get("sell", 0) + entry.get("strongSell", 0)
                total = buy + hold + sell
                if total == 0:
                    continue

                # Determine dominant rating
                if buy >= hold and buy >= sell:
                    dominant = "Buy"
                elif sell >= buy and sell >= hold:
                    dominant = "Sell"
                else:
                    dominant = "Hold"

                ratings.append(AnalystRating(
                    analyst_name="Consensus",
                    firm="Finnhub Aggregated",
                    rating=dominant,
                    rating_normalized=normalize_rating(dominant),
                    date=period or datetime.now().isoformat()[:10],
                    stock_symbol=symbol,
                    stock_name=symbol,
                    summary=f"Buy: {buy}, Hold: {hold}, Sell: {sell} (Total: {total})",
                ))
            logger.info(f"✓ Finnhub Research ({symbol}): {len(ratings)} 条")
        except Exception as e:
            logger.error(f"❌ Finnhub Research 采集失败 ({symbol}): {e}")
        return ratings

    # ------------------------------------------------------------------
    # Tier 1: Yahoo Finance (yfinance)
    # ------------------------------------------------------------------

    async def fetch_yahoo_finance_ratings(self, symbol: str) -> List[AnalystRating]:
        """通过 yfinance 库采集 Yahoo Finance 分析师数据。

        完全免费，无需 API Key。
        """
        ratings: List[AnalystRating] = []
        try:
            import yfinance as yf

            ticker = await asyncio.to_thread(yf.Ticker, symbol)

            # recommendations (aggregated format: period, strongBuy, buy, hold, sell, strongSell)
            try:
                recs = await asyncio.to_thread(lambda: ticker.recommendations)
                if recs is not None and not recs.empty:
                    cols = [c.lower() for c in recs.columns]
                    if "strongbuy" in cols or "buy" in cols:
                        # New aggregated format
                        for idx, row in recs.iterrows():
                            buy = int(row.get("strongBuy", 0) or 0) + int(row.get("buy", 0) or 0)
                            hold = int(row.get("hold", 0) or 0)
                            sell = int(row.get("strongSell", 0) or 0) + int(row.get("sell", 0) or 0)
                            total = buy + hold + sell
                            if total == 0:
                                continue
                            if buy >= hold and buy >= sell:
                                dominant = "Buy"
                            elif sell >= buy and sell >= hold:
                                dominant = "Sell"
                            else:
                                dominant = "Hold"
                            period = str(row.get("period", "")).strip()
                            ratings.append(AnalystRating(
                                analyst_name="Consensus",
                                firm="Yahoo Finance",
                                rating=dominant,
                                rating_normalized=normalize_rating(dominant),
                                date=datetime.now().isoformat()[:10],
                                stock_symbol=symbol,
                                stock_name=symbol,
                                summary=f"Period {period}: Buy {buy}, Hold {hold}, Sell {sell}",
                            ))
                    else:
                        # Legacy individual analyst format
                        for idx, row in recs.tail(20).iterrows():
                            firm = str(row.get("Firm", row.get("firm", ""))).strip()
                            grade = str(row.get("To Grade", row.get("toGrade", ""))).strip()
                            action = str(row.get("Action", row.get("action", ""))).strip()
                            date_val = str(idx)[:10] if idx is not None else ""
                            if not grade:
                                continue
                            ratings.append(AnalystRating(
                                analyst_name="",
                                firm=firm or "Yahoo Finance",
                                rating=grade,
                                rating_normalized=normalize_rating(grade),
                                date=date_val or datetime.now().isoformat()[:10],
                                stock_symbol=symbol,
                                stock_name=symbol,
                                action=_map_yf_action(action),
                            ))
            except Exception as e:
                logger.debug(f"Yahoo recommendations 获取失败 ({symbol}): {e}")

            # upgrades_downgrades (individual analyst entries)
            try:
                upgrades = await asyncio.to_thread(lambda: ticker.upgrades_downgrades)
                if upgrades is not None and not upgrades.empty:
                    for idx, row in upgrades.tail(10).iterrows():
                        firm = str(row.get("Firm", "")).strip()
                        grade = str(row.get("ToGrade", "")).strip()
                        action = str(row.get("Action", "")).strip()
                        date_val = str(idx)[:10] if idx is not None else ""
                        if not grade:
                            continue
                        ratings.append(AnalystRating(
                            analyst_name="",
                            firm=firm or "Yahoo Finance",
                            rating=grade,
                            rating_normalized=normalize_rating(grade),
                            date=date_val or datetime.now().isoformat()[:10],
                            stock_symbol=symbol,
                            stock_name=symbol,
                            action=_map_yf_action(action),
                        ))
            except Exception as e:
                logger.debug(f"Yahoo upgrades_downgrades 获取失败 ({symbol}): {e}")

            # analyst price targets
            try:
                targets = await asyncio.to_thread(lambda: ticker.analyst_price_targets)
                if targets is not None and isinstance(targets, dict):
                    current = targets.get("current")
                    if current and ratings:
                        # Attach target price to the most recent rating
                        ratings[0].target_price = float(current)
                    high = targets.get("high")
                    low = targets.get("low")
                    if high and ratings:
                        ratings[0].summary = (
                            f"Target: ${current}, Range: ${low}-${high}"
                        )
            except Exception as e:
                logger.debug(f"Yahoo price targets 获取失败 ({symbol}): {e}")

            logger.info(f"✓ Yahoo Finance ({symbol}): {len(ratings)} 条")
        except Exception as e:
            logger.error(f"❌ Yahoo Finance 采集失败 ({symbol}): {e}")
        return ratings

    # ------------------------------------------------------------------
    # Tier 2: Finviz
    # ------------------------------------------------------------------

    async def fetch_finviz_ratings(self, symbol: str) -> List[AnalystRating]:
        """Finviz 免费 HTML 抓取，分析师目标价和评级概览。"""
        ratings: List[AnalystRating] = []
        try:
            url = f"https://finviz.com/quote.ashx?t={symbol}"
            headers = {
                **self._http_headers,
                "Referer": "https://finviz.com/",
            }
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                html = resp.text

            # Parse analyst ratings table from HTML
            ratings = _parse_finviz_ratings(html, symbol)
            logger.info(f"✓ Finviz ({symbol}): {len(ratings)} 条")
        except Exception as e:
            logger.debug(f"Finviz 采集失败 ({symbol}): {e}")
        return ratings

    # ------------------------------------------------------------------
    # Tier 2: Zacks
    # ------------------------------------------------------------------

    async def fetch_zacks_ratings(self, symbol: str) -> List[AnalystRating]:
        """Zacks 免费层基本评级信息（Zacks Rank 1-5）。"""
        ratings: List[AnalystRating] = []
        try:
            url = f"https://quote-feed.zacks.com/index?t={symbol}"
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            stock_data = data.get(symbol, {})
            zacks_rank = str(stock_data.get("zacks_rank", "")).strip()
            if zacks_rank:
                rank_labels = {
                    "1": "Strong Buy", "2": "Buy", "3": "Hold",
                    "4": "Sell", "5": "Strong Sell",
                }
                label = rank_labels.get(zacks_rank, f"Rank {zacks_rank}")
                ratings.append(AnalystRating(
                    analyst_name="Zacks",
                    firm="Zacks Investment Research",
                    rating=label,
                    rating_normalized=normalize_rating(zacks_rank),
                    date=datetime.now().isoformat()[:10],
                    stock_symbol=symbol,
                    stock_name=stock_data.get("company_name", symbol),
                    summary=f"Zacks Rank #{zacks_rank}: {label}",
                ))
            logger.info(f"✓ Zacks ({symbol}): {len(ratings)} 条")
        except Exception as e:
            logger.debug(f"Zacks 采集失败 ({symbol}): {e}")
        return ratings

    # ------------------------------------------------------------------
    # Tier 3: Benzinga
    # ------------------------------------------------------------------

    async def fetch_benzinga_ratings(self, symbol: str) -> List[AnalystRating]:
        """Benzinga 分析师评级 API（需付费 API Key）。"""
        source_id = "benzinga"
        if not self._is_source_available(source_id):
            logger.info(f"ℹ️ {source_id} 未配置 API Key，跳过")
            return []

        ratings: List[AnalystRating] = []
        api_key = self._get_api_key(source_id)
        try:
            url = "https://api.benzinga.com/api/v2.1/calendar/ratings"
            params = {"token": api_key, "parameters[tickers]": symbol, "pagesize": "20"}
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, params=params, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            for entry in data.get("ratings", data if isinstance(data, list) else []):
                analyst = str(entry.get("analyst", "")).strip()
                firm = str(entry.get("analyst_name", entry.get("firm", ""))).strip()
                rating_current = str(entry.get("rating_current", "")).strip()
                pt_current = entry.get("pt_current") or entry.get("adjusted_pt_current")
                pt_prior = entry.get("pt_prior") or entry.get("adjusted_pt_prior")
                action = str(entry.get("action_company", entry.get("action", ""))).strip()
                date_val = str(entry.get("date", "")).strip()

                if not rating_current:
                    continue
                ratings.append(AnalystRating(
                    analyst_name=analyst,
                    firm=firm or "Benzinga",
                    rating=rating_current,
                    rating_normalized=normalize_rating(rating_current),
                    target_price=_safe_float(pt_current),
                    previous_target=_safe_float(pt_prior),
                    date=date_val or datetime.now().isoformat()[:10],
                    stock_symbol=symbol,
                    stock_name=symbol,
                    action=_map_benzinga_action(action),
                ))
            logger.info(f"✓ Benzinga ({symbol}): {len(ratings)} 条")
        except Exception as e:
            logger.debug(f"Benzinga 采集失败 ({symbol}): {e}")
        return ratings

    # ------------------------------------------------------------------
    # Tier 3: Seeking Alpha
    # ------------------------------------------------------------------

    async def fetch_seeking_alpha_ratings(self, symbol: str) -> List[AnalystRating]:
        """Seeking Alpha 分析师文章和评级（部分免费）。"""
        source_id = "seekingalpha"
        if not self._is_source_available(source_id):
            logger.info(f"ℹ️ {source_id} 未配置 API Key，跳过")
            return []

        ratings: List[AnalystRating] = []
        try:
            url = f"https://seekingalpha.com/api/v3/symbols/{symbol}/ratings"
            headers = {
                **self._http_headers,
                "Referer": "https://seekingalpha.com/",
            }
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            for entry in data.get("data", []):
                attrs = entry.get("attributes", {})
                rating_val = str(attrs.get("rating", "")).strip()
                if not rating_val:
                    continue
                ratings.append(AnalystRating(
                    analyst_name=str(attrs.get("author", "")).strip(),
                    firm="Seeking Alpha",
                    rating=rating_val,
                    rating_normalized=normalize_rating(rating_val),
                    date=str(attrs.get("date", "")).strip() or datetime.now().isoformat()[:10],
                    stock_symbol=symbol,
                    stock_name=symbol,
                ))
            logger.info(f"✓ Seeking Alpha ({symbol}): {len(ratings)} 条")
        except Exception as e:
            logger.debug(f"Seeking Alpha 采集失败 ({symbol}): {e}")
        return ratings

    # ------------------------------------------------------------------
    # Tier 4: High-risk scraping sources (best-effort, silent fail)
    # ------------------------------------------------------------------

    async def fetch_tipranks_ratings(self, symbol: str) -> List[AnalystRating]:
        """TipRanks 分析师评级（高反爬风险，失败时静默跳过）。"""
        ratings: List[AnalystRating] = []
        try:
            url = f"https://www.tipranks.com/api/stocks/getNewsSentiments/?ticker={symbol}"
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(url, headers=self._http_headers)
                resp.raise_for_status()
                data = resp.json()

            consensus = data.get("consensus", {})
            if consensus:
                rating_val = str(consensus.get("consensus", "")).strip()
                if rating_val:
                    ratings.append(AnalystRating(
                        analyst_name="Consensus",
                        firm="TipRanks",
                        rating=rating_val,
                        rating_normalized=normalize_rating(rating_val),
                        target_price=_safe_float(consensus.get("priceTarget")),
                        date=datetime.now().isoformat()[:10],
                        stock_symbol=symbol,
                        stock_name=symbol,
                    ))
            logger.debug(f"TipRanks ({symbol}): {len(ratings)} 条")
        except Exception:
            pass  # Silent fail for Tier 4
        return ratings

    async def fetch_marketbeat_ratings(self, symbol: str) -> List[AnalystRating]:
        """MarketBeat 分析师评级（高反爬风险，失败时静默跳过）。"""
        ratings: List[AnalystRating] = []
        try:
            url = f"https://www.marketbeat.com/stocks/NYSE/{symbol}/forecast/"
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(url, headers=self._http_headers)
                resp.raise_for_status()
            # HTML parsing would go here; for now return empty on success too
            logger.debug(f"MarketBeat ({symbol}): page fetched")
        except Exception:
            pass  # Silent fail
        return ratings

    async def fetch_simply_wall_st(self, symbol: str) -> List[AnalystRating]:
        """Simply Wall St 分析师预测（高反爬风险，失败时静默跳过）。"""
        ratings: List[AnalystRating] = []
        try:
            url = f"https://simplywall.st/api/company/search?query={symbol}"
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(url, headers=self._http_headers)
                resp.raise_for_status()
            logger.debug(f"Simply Wall St ({symbol}): page fetched")
        except Exception:
            pass  # Silent fail
        return ratings

    async def fetch_last10k_summaries(self, symbol: str) -> List[AnalystRating]:
        """Last10K SEC 财报 AI 摘要（高反爬风险，失败时静默跳过）。"""
        ratings: List[AnalystRating] = []
        try:
            url = f"https://last10k.com/sec-filing/{symbol}"
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(url, headers=self._http_headers)
                resp.raise_for_status()
            logger.debug(f"Last10K ({symbol}): page fetched")
        except Exception:
            pass  # Silent fail
        return ratings

    async def fetch_wisesheets_reports(self, symbol: str) -> List[AnalystRating]:
        """Wisesheets 投行研报摘要（高反爬风险，失败时静默跳过）。"""
        ratings: List[AnalystRating] = []
        try:
            url = f"https://wisesheets.io/api/reports/{symbol}"
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                resp = await client.get(url, headers=self._http_headers)
                resp.raise_for_status()
            logger.debug(f"Wisesheets ({symbol}): page fetched")
        except Exception:
            pass  # Silent fail
        return ratings

    # ------------------------------------------------------------------
    # Fetch dispatcher
    # ------------------------------------------------------------------

    def _get_fetch_method(self, source_id: str):
        """Return the fetch method for a given source_id."""
        mapping = {
            "finnhub_research": self.fetch_finnhub_recommendations,
            "yahoo": self.fetch_yahoo_finance_ratings,
            "finviz": self.fetch_finviz_ratings,
            "zacks": self.fetch_zacks_ratings,
            "benzinga": self.fetch_benzinga_ratings,
            "seekingalpha": self.fetch_seeking_alpha_ratings,
            "tipranks": self.fetch_tipranks_ratings,
            "marketbeat": self.fetch_marketbeat_ratings,
            "simplywallst": self.fetch_simply_wall_st,
            "last10k": self.fetch_last10k_summaries,
            "wisesheets": self.fetch_wisesheets_reports,
        }
        return mapping.get(source_id)

    # ------------------------------------------------------------------
    # Core: tiered collection with degradation
    # ------------------------------------------------------------------

    async def collect_research_reports(
        self,
        symbols: Optional[List[str]] = None,
        source_ids: Optional[List[str]] = None,
        force_refresh: bool = False,
    ) -> Dict:
        """按分层优先级采集投行研报数据，支持降级策略。

        Args:
            symbols: 股票代码列表（如 ["AAPL", "MSFT"]），None 时跳过
            source_ids: 指定数据源列表，None 表示所有可用源
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            Dict with keys: ratings, tier_status, collection_time, from_cache
        """
        if not symbols:
            return {
                "ratings": [],
                "tier_status": {},
                "collection_time": datetime.now().isoformat(),
                "from_cache": False,
            }

        # Build cache key from sorted symbols
        symbols_hash = hashlib.md5("_".join(sorted(symbols)).encode()).hexdigest()[:12]
        cache_key = f"research_{symbols_hash}"

        # Cache check
        if not force_refresh and self.use_cache and self.cache_service:
            cached = self.cache_service.get_cached_data(cache_key=cache_key)
            if cached:
                logger.info("📦 使用投行研报缓存数据")
                return {
                    "ratings": [AnalystRating(**r) for r in cached.get("ratings", [])],
                    "tier_status": cached.get("tier_status", {}),
                    "collection_time": cached.get("collection_time", ""),
                    "from_cache": True,
                }

        logger.info(f"📊 开始采集投行研报: {symbols}")

        all_ratings: List[AnalystRating] = []
        tier_status: Dict[str, str] = {}

        # Process tiers sequentially (1 → 2 → 3 → 4)
        for tier_num in sorted(RESEARCH_SOURCE_TIERS.keys()):
            tier_sources = RESEARCH_SOURCE_TIERS[tier_num]

            # Filter by source_ids if specified
            if source_ids:
                tier_sources = [s for s in tier_sources if s in source_ids]
            if not tier_sources:
                tier_status[str(tier_num)] = "skipped"
                continue

            # Filter by availability
            available = [s for s in tier_sources if self._is_source_available(s)]
            if not available:
                tier_status[str(tier_num)] = "unavailable"
                continue

            # Concurrent fetch within tier, across all symbols
            tasks = []
            task_labels = []
            for sid in available:
                method = self._get_fetch_method(sid)
                if not method:
                    continue
                for sym in symbols:
                    tasks.append(self._safe_fetch(sid, method, sym, tier_num))
                    task_labels.append(f"{sid}:{sym}")

            results = await asyncio.gather(*tasks)

            tier_ratings: List[AnalystRating] = []
            for result in results:
                tier_ratings.extend(result)

            if tier_ratings:
                all_ratings.extend(tier_ratings)
                tier_status[str(tier_num)] = f"success ({len(tier_ratings)} ratings)"
            else:
                tier_status[str(tier_num)] = "empty"

        collection_time = datetime.now().isoformat()

        # Save to cache
        if self.use_cache and self.cache_service and all_ratings:
            cache_data = {
                "ratings": [r.model_dump() for r in all_ratings],
                "tier_status": tier_status,
                "collection_time": collection_time,
            }
            self.cache_service.save_to_cache(cache_data, cache_key=cache_key)

        logger.info(
            f"📊 投行研报采集完成: {len(all_ratings)} 条, "
            f"Tier 状态: {tier_status}"
        )
        return {
            "ratings": all_ratings,
            "tier_status": tier_status,
            "collection_time": collection_time,
            "from_cache": False,
        }

    async def _safe_fetch(
        self, source_id: str, method, symbol: str, tier: int,
    ) -> List[AnalystRating]:
        """Safely execute a fetch method. Tier 4 failures are silent."""
        try:
            return await method(symbol)
        except Exception as e:
            if tier >= 4:
                pass  # Silent fail for Tier 4
            else:
                logger.error(f"❌ 研报源 {source_id} ({symbol}) 采集异常: {e}")
            return []

    # ------------------------------------------------------------------
    # Consensus rating calculation
    # ------------------------------------------------------------------

    async def get_consensus_rating(self, symbol: str) -> ConsensusRating:
        """计算某只股票的共识评级。

        汇总所有来源的分析师评级，计算 buy/hold/sell 占比和平均目标价。
        """
        result = await self.collect_research_reports(symbols=[symbol])
        ratings: List[AnalystRating] = result.get("ratings", [])

        buy_count = sum(1 for r in ratings if r.rating_normalized == "buy")
        hold_count = sum(1 for r in ratings if r.rating_normalized == "hold")
        sell_count = sum(1 for r in ratings if r.rating_normalized == "sell")
        total = buy_count + hold_count + sell_count

        # Determine consensus
        if total == 0:
            consensus = "hold"
        elif buy_count >= hold_count and buy_count >= sell_count:
            consensus = "buy"
        elif sell_count >= buy_count and sell_count >= hold_count:
            consensus = "sell"
        else:
            consensus = "hold"

        # Target prices
        prices = [r.target_price for r in ratings if r.target_price and r.target_price > 0]
        avg_target = sum(prices) / len(prices) if prices else None
        high_target = max(prices) if prices else None
        low_target = min(prices) if prices else None

        return ConsensusRating(
            stock_symbol=symbol,
            stock_name=symbol,
            buy_count=buy_count,
            hold_count=hold_count,
            sell_count=sell_count,
            consensus=consensus,
            avg_target_price=round(avg_target, 2) if avg_target else None,
            high_target=round(high_target, 2) if high_target else None,
            low_target=round(low_target, 2) if low_target else None,
            total_analysts=total,
            last_updated=datetime.now().isoformat(),
        )

    # ------------------------------------------------------------------
    # Convert ratings to StockNewsItem format
    # ------------------------------------------------------------------

    def convert_to_news_items(self, ratings: List[AnalystRating]) -> List[StockNewsItem]:
        """将 AnalystRating 转换为 StockNewsItem 格式，以便在热榜中统一展示。"""
        items: List[StockNewsItem] = []
        for idx, r in enumerate(ratings):
            action_str = f" ({r.action})" if r.action else ""
            price_str = f", 目标价 ${r.target_price}" if r.target_price else ""
            title = f"{r.firm}{action_str} {r.stock_name}: {r.rating}{price_str}"

            summary_parts = [f"评级: {r.rating} → {r.rating_normalized}"]
            if r.target_price:
                summary_parts.append(f"目标价: ${r.target_price}")
            if r.previous_target:
                summary_parts.append(f"前次目标价: ${r.previous_target}")
            if r.summary:
                summary_parts.append(r.summary)
            summary = " | ".join(summary_parts)

            item_id = hashlib.md5(
                f"{r.firm}_{r.stock_symbol}_{r.date}_{r.rating}".encode()
            ).hexdigest()[:16]

            items.append(StockNewsItem(
                id=f"research_{item_id}",
                title=title,
                summary=summary[:300],
                source_platform=f"research_{r.firm.lower().replace(' ', '_')[:20]}",
                source_name=r.firm,
                url="",
                published_time=r.date or datetime.now().isoformat(),
                hot_value="",
                rank=idx + 1,
                category="research_report",
                analyst_rating=r,
            ))
        return items


# ---------------------------------------------------------------------------
# Module-level helper functions
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    """Safely convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None


def _map_yf_action(action: str) -> Optional[str]:
    """Map yfinance action string to standard action."""
    lower = (action or "").lower().strip()
    if "up" in lower:
        return "upgrade"
    if "down" in lower:
        return "downgrade"
    if "init" in lower or "new" in lower:
        return "initiate"
    if "main" in lower or "reit" in lower:
        return "maintain"
    return lower if lower else None


def _map_benzinga_action(action: str) -> Optional[str]:
    """Map Benzinga action to standard action."""
    lower = (action or "").lower().strip()
    if "upgrade" in lower:
        return "upgrade"
    if "downgrade" in lower:
        return "downgrade"
    if "initiat" in lower:
        return "initiate"
    if "maintain" in lower or "reiterat" in lower:
        return "maintain"
    return lower if lower else None


def _parse_finviz_ratings(html: str, symbol: str) -> List[AnalystRating]:
    """Parse analyst ratings from Finviz HTML page.

    Looks for the analyst ratings table rows. Returns empty list
    if parsing fails (best-effort).
    """
    ratings: List[AnalystRating] = []
    try:
        import re
        # Finviz analyst table rows pattern (simplified)
        # Each row: Date | Action | Analyst | Rating | Price Target
        pattern = (
            r'<td[^>]*>(\w{3}-\d{1,2}-\d{2,4})</td>'
            r'\s*<td[^>]*>([^<]*)</td>'
            r'\s*<td[^>]*>([^<]*)</td>'
            r'\s*<td[^>]*>([^<]*)</td>'
            r'\s*<td[^>]*>\$?([\d,.]*)</td>'
        )
        matches = re.findall(pattern, html)
        for date_str, action, firm, rating_val, price in matches[:20]:
            if not rating_val.strip():
                continue
            ratings.append(AnalystRating(
                analyst_name="",
                firm=firm.strip(),
                rating=rating_val.strip(),
                rating_normalized=normalize_rating(rating_val.strip()),
                target_price=_safe_float(price.replace(",", "")),
                date=date_str.strip(),
                stock_symbol=symbol,
                stock_name=symbol,
                action=_map_benzinga_action(action.strip()),
            ))
    except Exception:
        pass  # Best-effort parsing
    return ratings


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

research_report_service = ResearchReportService()
