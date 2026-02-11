#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for InternationalNewsService.

Feature: multi-mode-platform
Property 24: 国际财经新闻中文摘要完整性
Property 28: 国际新闻源失败不影响国内数据
Property 31: AI 翻译摘要标记一致性

**Validates: Requirements 1.9, 1.5, 1.14**
"""

import asyncio
import re
from typing import List
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.schemas import StockNewsItem


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")),
    min_size=1,
    max_size=120,
).filter(lambda s: s.strip() != "")

intl_source_platforms = st.sampled_from([
    "finnhub", "newsapi", "alpha_vantage", "gdelt", "google_rss", "marketaux",
])

domestic_source_platforms = st.sampled_from([
    "akshare", "sina", "10jqka", "xueqiu", "tushare",
])

english_news_item_strategy = st.builds(
    StockNewsItem,
    id=st.from_regex(r"[a-z]+_\d+", fullmatch=True),
    title=non_empty_text,
    summary=non_empty_text,
    source_platform=intl_source_platforms,
    source_name=non_empty_text,
    url=st.from_regex(r"https?://[a-z]+\.[a-z]+/[a-z0-9]+", fullmatch=True),
    published_time=st.from_regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", fullmatch=True),
    hot_value=st.text(max_size=20),
    rank=st.one_of(st.none(), st.integers(min_value=1, max_value=500)),
    category=st.just("international"),
    original_language=st.just("en"),
    is_ai_translated=st.just(False),
)

domestic_news_item_strategy = st.builds(
    StockNewsItem,
    id=st.from_regex(r"[a-z]+_\d+", fullmatch=True),
    title=non_empty_text,
    summary=non_empty_text,
    source_platform=domestic_source_platforms,
    source_name=non_empty_text,
    url=st.from_regex(r"https?://[a-z]+\.[a-z]+/[a-z0-9]+", fullmatch=True),
    published_time=st.from_regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", fullmatch=True),
    hot_value=st.text(max_size=20),
    rank=st.one_of(st.none(), st.integers(min_value=1, max_value=500)),
    category=st.just("domestic"),
    original_language=st.just("zh"),
    is_ai_translated=st.just(False),
)


# ---------------------------------------------------------------------------
# Helper: check if string contains Chinese characters
# ---------------------------------------------------------------------------

def contains_chinese(text: str) -> bool:
    """Return True if text contains at least one CJK Unified Ideograph."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


# ---------------------------------------------------------------------------
# Property 24: 国际财经新闻中文摘要完整性
# ---------------------------------------------------------------------------


class TestProperty24InternationalNewsChineSummary:
    """Property 24: 国际财经新闻中文摘要完整性

    For any category 为 "international" 且 original_language 为 "en" 的
    StockNewsItem，经过 batch_translate_to_chinese 后，其 summary 字段
    必须为非空的中文文本（包含至少一个中文字符）。

    **Validates: Requirements 1.9**
    """

    @given(items=st.lists(english_news_item_strategy, min_size=1, max_size=5))
    @settings(max_examples=100, deadline=None)
    def test_translated_summaries_contain_chinese(self, items: List[StockNewsItem]):
        """翻译后的国际新闻摘要应包含中文字符"""
        from app.services.international_news_service import InternationalNewsService

        service = InternationalNewsService(use_cache=False)

        # Build a mock LLM response that returns Chinese translations
        # keyed by the item indices
        def build_mock_response(batch):
            parts = []
            for i, item in enumerate(batch):
                parts.append(f"[{i+1}] 这是关于{item.title[:10]}的中文翻译摘要")
            return "\n".join(parts)

        mock_result = MagicMock()

        async def mock_translate_batch(batch):
            response_text = build_mock_response(batch)
            translations = {}
            pattern = r"\[(\d+)\]\s*(.+?)(?=\[\d+\]|$)"
            matches = re.findall(pattern, response_text, re.DOTALL)
            for num_str, translated_text in matches:
                idx = int(num_str) - 1
                if 0 <= idx < len(batch):
                    cleaned = translated_text.strip()
                    if cleaned:
                        translations[batch[idx].id] = cleaned
            return translations

        service._translate_batch = mock_translate_batch

        result = asyncio.get_event_loop().run_until_complete(
            service.batch_translate_to_chinese(items)
        )

        for item in result:
            if item.original_language == "en" and item.category == "international":
                assert item.summary.strip() != "", (
                    f"Item {item.id} summary should be non-empty after translation"
                )
                assert contains_chinese(item.summary), (
                    f"Item {item.id} summary should contain Chinese characters "
                    f"after translation, got: {item.summary[:50]}"
                )

    @given(items=st.lists(english_news_item_strategy, min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_translation_failure_preserves_original_summary(self, items: List[StockNewsItem]):
        """翻译失败时应保留原始英文摘要（非空）"""
        from app.services.international_news_service import InternationalNewsService

        service = InternationalNewsService(use_cache=False)

        # Mock _translate_batch to return empty (simulating failure)
        async def mock_translate_batch_fail(batch):
            return {}

        service._translate_batch = mock_translate_batch_fail

        result = asyncio.get_event_loop().run_until_complete(
            service.batch_translate_to_chinese(items)
        )

        for original, translated in zip(items, result):
            # On failure, summary should remain the original non-empty text
            assert translated.summary.strip() != "", (
                f"Item {translated.id} summary should remain non-empty even on translation failure"
            )
            assert translated.summary == original.summary, (
                "On translation failure, summary should be preserved as-is"
            )


# ---------------------------------------------------------------------------
# Property 28: 国际新闻源失败不影响国内数据
# ---------------------------------------------------------------------------


class TestProperty28InternationalFailureIsolation:
    """Property 28: 国际新闻源失败不影响国内数据

    For any 国际财经数据源全部请求失败的情况，Stock_Crawler 仍应返回
    非空的国内数据源采集结果（若国内源可用）。

    **Validates: Requirements 1.5**
    """

    @given(domestic_items=st.lists(domestic_news_item_strategy, min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_domestic_data_unaffected_by_intl_failure(self, domestic_items: List[StockNewsItem]):
        """国际源全部失败时，国内数据仍正常返回"""
        from app.services.international_news_service import InternationalNewsService

        service = InternationalNewsService(use_cache=False)

        # All international fetch methods raise exceptions
        async def failing_fetch():
            raise ConnectionError("Simulated international source failure")

        service.fetch_finnhub_news = failing_fetch
        service.fetch_newsapi_news = failing_fetch
        service.fetch_alpha_vantage_news = failing_fetch
        service.fetch_gdelt_news = failing_fetch
        service.fetch_google_news_rss = failing_fetch
        service.fetch_marketaux_news = failing_fetch

        # _safe_fetch wraps exceptions and returns empty list
        result = asyncio.get_event_loop().run_until_complete(
            service.collect_international_news(force_refresh=True)
        )

        # International service returns empty list on total failure (not an error)
        assert isinstance(result, list), "Result should be a list even when all sources fail"

        # Now verify domestic collector is independent
        from app.services.stock_news_collector import StockNewsCollector

        collector = StockNewsCollector(use_cache=False)

        # Mock domestic source to return our test items
        async def mock_domestic_fetch():
            return domestic_items

        collector.fetch_akshare_news = mock_domestic_fetch
        collector.fetch_sina_news = AsyncMock(return_value=[])
        collector.fetch_10jqka_news = AsyncMock(return_value=[])
        collector.fetch_xueqiu_news = AsyncMock(return_value=[])
        collector.fetch_tushare_news = AsyncMock(return_value=[])

        domestic_result = asyncio.get_event_loop().run_until_complete(
            collector.collect_news(source_ids=["akshare"], force_refresh=True)
        )

        assert domestic_result.success is True, "Domestic collection should succeed"
        assert len(domestic_result.items) == len(domestic_items), (
            "Domestic items should be returned regardless of international failures"
        )
        for item in domestic_result.items:
            assert item.category == "domestic"

    @given(data=st.data())
    @settings(max_examples=100)
    def test_safe_fetch_returns_empty_on_exception(self, data):
        """_safe_fetch 在异常时返回空列表，不传播异常"""
        from app.services.international_news_service import InternationalNewsService

        service = InternationalNewsService(use_cache=False)

        source_id = data.draw(intl_source_platforms)

        async def always_fail():
            raise RuntimeError("Simulated failure")

        result = asyncio.get_event_loop().run_until_complete(
            service._safe_fetch(source_id, always_fail)
        )

        assert result == [], (
            f"_safe_fetch should return empty list on exception for {source_id}"
        )


# ---------------------------------------------------------------------------
# Property 31: AI 翻译摘要标记一致性
# ---------------------------------------------------------------------------


class TestProperty31AITranslationMarkerConsistency:
    """Property 31: AI 翻译摘要标记一致性

    For any category 为 "international" 且 original_language 为 "en" 且
    经过 LLM 翻译的 StockNewsItem，其 is_ai_translated 字段必须为 True。

    **Validates: Requirements 1.14**
    """

    @given(items=st.lists(english_news_item_strategy, min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_translated_items_marked_as_ai_translated(self, items: List[StockNewsItem]):
        """成功翻译的条目 is_ai_translated 应为 True"""
        from app.services.international_news_service import InternationalNewsService

        service = InternationalNewsService(use_cache=False)

        # Mock _translate_batch to return Chinese translations for all items
        async def mock_translate_batch(batch):
            translations = {}
            for i, item in enumerate(batch):
                translations[item.id] = f"这是第{i+1}条新闻的中文翻译"
            return translations

        service._translate_batch = mock_translate_batch

        result = asyncio.get_event_loop().run_until_complete(
            service.batch_translate_to_chinese(items)
        )

        for item in result:
            if item.original_language == "en" and item.category == "international":
                assert item.is_ai_translated is True, (
                    f"Item {item.id} should have is_ai_translated=True after translation"
                )

    @given(items=st.lists(english_news_item_strategy, min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_untranslated_items_remain_unmarked(self, items: List[StockNewsItem]):
        """翻译失败的条目 is_ai_translated 应保持 False"""
        from app.services.international_news_service import InternationalNewsService

        service = InternationalNewsService(use_cache=False)

        # Mock _translate_batch to return empty (translation failure)
        async def mock_translate_batch_fail(batch):
            return {}

        service._translate_batch = mock_translate_batch_fail

        result = asyncio.get_event_loop().run_until_complete(
            service.batch_translate_to_chinese(items)
        )

        for item in result:
            assert item.is_ai_translated is False, (
                f"Item {item.id} should have is_ai_translated=False when translation fails"
            )

    @given(items=st.lists(english_news_item_strategy, min_size=2, max_size=5))
    @settings(max_examples=100)
    def test_partial_translation_marks_only_translated(self, items: List[StockNewsItem]):
        """部分翻译成功时，仅成功的条目标记为 is_ai_translated=True"""
        assume(len(items) >= 2)

        from app.services.international_news_service import InternationalNewsService

        service = InternationalNewsService(use_cache=False)

        # Only translate the first item, skip the rest
        first_id = items[0].id

        async def mock_translate_batch_partial(batch):
            translations = {}
            for item in batch:
                if item.id == first_id:
                    translations[item.id] = "仅第一条被翻译的中文摘要"
            return translations

        service._translate_batch = mock_translate_batch_partial

        result = asyncio.get_event_loop().run_until_complete(
            service.batch_translate_to_chinese(items)
        )

        for item in result:
            if item.id == first_id:
                assert item.is_ai_translated is True, (
                    "Successfully translated item should be marked"
                )
            else:
                assert item.is_ai_translated is False, (
                    "Non-translated item should remain unmarked"
                )
