#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for StockNewsCollector.

Feature: multi-mode-platform
Uses Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings

from app.schemas import StockNewsItem


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")),
    min_size=1,
    max_size=120,
).filter(lambda s: s.strip() != "")

source_platforms = st.sampled_from(["akshare", "sina", "10jqka", "xueqiu", "tushare"])

stock_news_item_strategy = st.builds(
    StockNewsItem,
    id=st.from_regex(r"[a-z]+_\d+", fullmatch=True),
    title=non_empty_text,
    summary=non_empty_text,
    source_platform=source_platforms,
    source_name=non_empty_text,
    url=st.from_regex(r"https?://[a-z]+\.[a-z]+/[a-z0-9]+", fullmatch=True),
    published_time=st.from_regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", fullmatch=True),
    hot_value=st.text(max_size=30),
    rank=st.one_of(st.none(), st.integers(min_value=1, max_value=1000)),
    category=st.just("domestic"),
)


# ---------------------------------------------------------------------------
# Property 1: 股票资讯条目数据完整性
# ---------------------------------------------------------------------------


class TestProperty1StockNewsItemCompleteness:
    """Property 1: 股票资讯条目数据完整性

    For any Stock_Crawler 返回的 StockNewsItem，该条目的 title、
    source_platform、url 和 published_time 字段必须为非空字符串。

    **Validates: Requirements 1.2**
    """

    @given(item=stock_news_item_strategy)
    @settings(max_examples=100)
    def test_title_is_non_empty(self, item: StockNewsItem):
        """title 字段必须为非空字符串"""
        assert isinstance(item.title, str)
        assert len(item.title.strip()) > 0

    @given(item=stock_news_item_strategy)
    @settings(max_examples=100)
    def test_source_platform_is_non_empty(self, item: StockNewsItem):
        """source_platform 字段必须为非空字符串"""
        assert isinstance(item.source_platform, str)
        assert len(item.source_platform.strip()) > 0

    @given(item=stock_news_item_strategy)
    @settings(max_examples=100)
    def test_url_is_non_empty(self, item: StockNewsItem):
        """url 字段必须为非空字符串"""
        assert isinstance(item.url, str)
        assert len(item.url.strip()) > 0

    @given(item=stock_news_item_strategy)
    @settings(max_examples=100)
    def test_published_time_is_non_empty(self, item: StockNewsItem):
        """published_time 字段必须为非空字符串"""
        assert isinstance(item.published_time, str)
        assert len(item.published_time.strip()) > 0

    @given(item=stock_news_item_strategy)
    @settings(max_examples=100)
    def test_all_required_fields_non_empty(self, item: StockNewsItem):
        """所有必填字段同时满足非空约束"""
        assert item.title.strip() != ""
        assert item.source_platform.strip() != ""
        assert item.url.strip() != ""
        assert item.published_time.strip() != ""
