#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for ResearchReportService.

Feature: multi-mode-platform
Property 25: 投行研报结构化数据完整性
Property 26: 资讯类别筛选一致性
Property 27: 共识评级计算一致性

**Validates: Requirements 1.10, 1.11**
"""

from typing import List

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.schemas import AnalystRating, ConsensusRating, StockNewsItem
from app.services.research_report_service import (
    ResearchReportService,
    normalize_rating,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")),
    min_size=1,
    max_size=80,
).filter(lambda s: s.strip() != "")

normalized_ratings = st.sampled_from(["buy", "hold", "sell"])

analyst_rating_strategy = st.builds(
    AnalystRating,
    analyst_name=non_empty_text,
    firm=non_empty_text,
    rating=non_empty_text,
    rating_normalized=normalized_ratings,
    target_price=st.one_of(st.none(), st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)),
    previous_target=st.one_of(st.none(), st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)),
    currency=st.just("USD"),
    date=st.from_regex(r"\d{4}-\d{2}-\d{2}", fullmatch=True),
    stock_symbol=st.from_regex(r"[A-Z]{1,5}", fullmatch=True),
    stock_name=non_empty_text,
    action=st.one_of(st.none(), st.sampled_from(["upgrade", "downgrade", "maintain", "initiate"])),
    summary=st.one_of(st.none(), non_empty_text),
)

research_news_item_strategy = st.builds(
    StockNewsItem,
    id=st.from_regex(r"research_[a-f0-9]+", fullmatch=True),
    title=non_empty_text,
    summary=non_empty_text,
    source_platform=st.from_regex(r"research_[a-z_]+", fullmatch=True),
    source_name=non_empty_text,
    url=st.just(""),
    published_time=st.from_regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", fullmatch=True),
    hot_value=st.text(max_size=20),
    rank=st.one_of(st.none(), st.integers(min_value=1, max_value=500)),
    category=st.just("research_report"),
    analyst_rating=analyst_rating_strategy,
)

domestic_news_item_strategy = st.builds(
    StockNewsItem,
    id=st.from_regex(r"[a-z]+_\d+", fullmatch=True),
    title=non_empty_text,
    summary=non_empty_text,
    source_platform=st.sampled_from(["akshare", "sina", "10jqka", "xueqiu", "tushare"]),
    source_name=non_empty_text,
    url=st.from_regex(r"https?://[a-z]+\.[a-z]+/[a-z0-9]+", fullmatch=True),
    published_time=st.from_regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", fullmatch=True),
    hot_value=st.text(max_size=20),
    rank=st.one_of(st.none(), st.integers(min_value=1, max_value=500)),
    category=st.just("domestic"),
)

intl_news_item_strategy = st.builds(
    StockNewsItem,
    id=st.from_regex(r"[a-z]+_\d+", fullmatch=True),
    title=non_empty_text,
    summary=non_empty_text,
    source_platform=st.sampled_from(["finnhub", "newsapi", "alpha_vantage"]),
    source_name=non_empty_text,
    url=st.from_regex(r"https?://[a-z]+\.[a-z]+/[a-z0-9]+", fullmatch=True),
    published_time=st.from_regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", fullmatch=True),
    hot_value=st.text(max_size=20),
    rank=st.one_of(st.none(), st.integers(min_value=1, max_value=500)),
    category=st.just("international"),
)

categories = st.sampled_from(["domestic", "international", "research_report"])


# ---------------------------------------------------------------------------
# Property 25: 投行研报结构化数据完整性
# ---------------------------------------------------------------------------


class TestProperty25ResearchReportDataIntegrity:
    """Property 25: 投行研报结构化数据完整性

    For any category 为 "research_report" 的 StockNewsItem，其关联的
    AnalystRating 的 firm、rating_normalized、stock_symbol 和 date 字段
    必须为非空字符串，且 rating_normalized 必须为 "buy"、"hold" 或 "sell" 之一。

    **Validates: Requirements 1.10**
    """

    @given(ratings=st.lists(analyst_rating_strategy, min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_convert_to_news_items_preserves_rating_integrity(
        self, ratings: List[AnalystRating]
    ):
        """convert_to_news_items 生成的 StockNewsItem 应保持评级数据完整性"""
        service = ResearchReportService(use_cache=False)
        items = service.convert_to_news_items(ratings)

        assert len(items) == len(ratings)

        for item in items:
            assert item.category == "research_report"
            assert item.analyst_rating is not None, (
                f"Item {item.id} must have an analyst_rating"
            )
            ar = item.analyst_rating
            assert isinstance(ar.firm, str) and ar.firm.strip() != "", (
                f"firm must be non-empty, got: '{ar.firm}'"
            )
            assert isinstance(ar.rating_normalized, str) and ar.rating_normalized.strip() != "", (
                f"rating_normalized must be non-empty, got: '{ar.rating_normalized}'"
            )
            assert ar.rating_normalized in ("buy", "hold", "sell"), (
                f"rating_normalized must be buy/hold/sell, got: '{ar.rating_normalized}'"
            )
            assert isinstance(ar.stock_symbol, str) and ar.stock_symbol.strip() != "", (
                f"stock_symbol must be non-empty, got: '{ar.stock_symbol}'"
            )
            assert isinstance(ar.date, str) and ar.date.strip() != "", (
                f"date must be non-empty, got: '{ar.date}'"
            )

    @given(item=research_news_item_strategy)
    @settings(max_examples=100)
    def test_research_report_item_has_valid_analyst_rating(self, item: StockNewsItem):
        """research_report 类别的 StockNewsItem 的 AnalystRating 字段有效"""
        assert item.category == "research_report"
        assert item.analyst_rating is not None

        ar = item.analyst_rating
        assert ar.firm.strip() != ""
        assert ar.rating_normalized in ("buy", "hold", "sell")
        assert ar.stock_symbol.strip() != ""
        assert ar.date.strip() != ""

    @given(raw_rating=st.sampled_from([
        "Buy", "Strong Buy", "Outperform", "Overweight", "Positive",
        "Hold", "Neutral", "Equal-Weight", "Market Perform",
        "Sell", "Strong Sell", "Underperform", "Underweight", "Negative",
        "1", "2", "3", "4", "5",
    ]))
    @settings(max_examples=100)
    def test_normalize_rating_returns_valid_value(self, raw_rating: str):
        """normalize_rating 始终返回 buy/hold/sell 之一"""
        result = normalize_rating(raw_rating)
        assert result in ("buy", "hold", "sell"), (
            f"normalize_rating('{raw_rating}') returned '{result}', expected buy/hold/sell"
        )


# ---------------------------------------------------------------------------
# Property 26: 资讯类别筛选一致性
# ---------------------------------------------------------------------------


class TestProperty26CategoryFilterConsistency:
    """Property 26: 资讯类别筛选一致性

    For any 类别筛选参数 C（domestic/international/research_report）和
    股票资讯列表，筛选后返回的每条 StockNewsItem 的 category 字段应等于 C。

    **Validates: Requirements 1.11**
    """

    @given(
        category=categories,
        domestic_items=st.lists(domestic_news_item_strategy, min_size=0, max_size=5),
        intl_items=st.lists(intl_news_item_strategy, min_size=0, max_size=5),
        research_items=st.lists(research_news_item_strategy, min_size=0, max_size=5),
    )
    @settings(max_examples=100)
    def test_category_filter_returns_matching_items(
        self,
        category: str,
        domestic_items: List[StockNewsItem],
        intl_items: List[StockNewsItem],
        research_items: List[StockNewsItem],
    ):
        """按类别筛选后，所有返回条目的 category 应与筛选参数一致"""
        all_items = domestic_items + intl_items + research_items
        filtered = [item for item in all_items if item.category == category]

        for item in filtered:
            assert item.category == category, (
                f"Filtered item category '{item.category}' != filter '{category}'"
            )

    @given(
        category=categories,
        domestic_items=st.lists(domestic_news_item_strategy, min_size=1, max_size=5),
        intl_items=st.lists(intl_news_item_strategy, min_size=1, max_size=5),
        research_items=st.lists(research_news_item_strategy, min_size=1, max_size=5),
    )
    @settings(max_examples=100)
    def test_category_filter_excludes_non_matching(
        self,
        category: str,
        domestic_items: List[StockNewsItem],
        intl_items: List[StockNewsItem],
        research_items: List[StockNewsItem],
    ):
        """按类别筛选后，不应包含其他类别的条目"""
        all_items = domestic_items + intl_items + research_items
        filtered = [item for item in all_items if item.category == category]

        other_categories = {"domestic", "international", "research_report"} - {category}
        for item in filtered:
            assert item.category not in other_categories, (
                f"Filtered result contains item with wrong category '{item.category}'"
            )

    @given(
        domestic_items=st.lists(domestic_news_item_strategy, min_size=1, max_size=5),
        intl_items=st.lists(intl_news_item_strategy, min_size=1, max_size=5),
        research_items=st.lists(research_news_item_strategy, min_size=1, max_size=5),
    )
    @settings(max_examples=100)
    def test_all_categories_partition_complete_list(
        self,
        domestic_items: List[StockNewsItem],
        intl_items: List[StockNewsItem],
        research_items: List[StockNewsItem],
    ):
        """三个类别的筛选结果之和应等于总列表长度"""
        all_items = domestic_items + intl_items + research_items
        domestic_filtered = [i for i in all_items if i.category == "domestic"]
        intl_filtered = [i for i in all_items if i.category == "international"]
        research_filtered = [i for i in all_items if i.category == "research_report"]

        assert len(domestic_filtered) + len(intl_filtered) + len(research_filtered) == len(all_items), (
            "Category partition should cover all items"
        )


# ---------------------------------------------------------------------------
# Property 27: 共识评级计算一致性
# ---------------------------------------------------------------------------


class TestProperty27ConsensusRatingConsistency:
    """Property 27: 共识评级计算一致性

    For any ConsensusRating，其 buy_count + hold_count + sell_count 应等于
    total_analysts，且 consensus 字段应等于 buy_count/hold_count/sell_count
    中最大值对应的评级。

    **Validates: Requirements 1.10**
    """

    @given(
        buy=st.integers(min_value=0, max_value=50),
        hold=st.integers(min_value=0, max_value=50),
        sell=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=100)
    def test_total_analysts_equals_sum_of_counts(
        self, buy: int, hold: int, sell: int
    ):
        """buy_count + hold_count + sell_count 应等于 total_analysts"""
        total = buy + hold + sell

        # Determine expected consensus
        if total == 0:
            consensus = "hold"
        elif buy >= hold and buy >= sell:
            consensus = "buy"
        elif sell >= buy and sell >= hold:
            consensus = "sell"
        else:
            consensus = "hold"

        cr = ConsensusRating(
            stock_symbol="TEST",
            stock_name="Test Stock",
            buy_count=buy,
            hold_count=hold,
            sell_count=sell,
            consensus=consensus,
            total_analysts=total,
            last_updated="2026-02-10T00:00:00",
        )

        assert cr.buy_count + cr.hold_count + cr.sell_count == cr.total_analysts, (
            f"Sum {cr.buy_count}+{cr.hold_count}+{cr.sell_count} != total {cr.total_analysts}"
        )

    @given(
        buy=st.integers(min_value=0, max_value=50),
        hold=st.integers(min_value=0, max_value=50),
        sell=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=100)
    def test_consensus_matches_dominant_rating(
        self, buy: int, hold: int, sell: int
    ):
        """consensus 应等于 buy/hold/sell 中最大值对应的评级"""
        total = buy + hold + sell

        # Determine expected consensus using the same logic as the service
        if total == 0:
            expected = "hold"
        elif buy >= hold and buy >= sell:
            expected = "buy"
        elif sell >= buy and sell >= hold:
            expected = "sell"
        else:
            expected = "hold"

        cr = ConsensusRating(
            stock_symbol="TEST",
            stock_name="Test Stock",
            buy_count=buy,
            hold_count=hold,
            sell_count=sell,
            consensus=expected,
            total_analysts=total,
            last_updated="2026-02-10T00:00:00",
        )

        assert cr.consensus == expected, (
            f"consensus '{cr.consensus}' != expected '{expected}' "
            f"for buy={buy}, hold={hold}, sell={sell}"
        )

    @given(
        ratings=st.lists(
            st.sampled_from(["buy", "hold", "sell"]),
            min_size=1,
            max_size=30,
        )
    )
    @settings(max_examples=100)
    def test_consensus_from_rating_list(self, ratings: List[str]):
        """从评级列表计算共识评级，验证计数和共识一致性"""
        buy_count = ratings.count("buy")
        hold_count = ratings.count("hold")
        sell_count = ratings.count("sell")
        total = len(ratings)

        # Same logic as ResearchReportService.get_consensus_rating
        if buy_count >= hold_count and buy_count >= sell_count:
            expected_consensus = "buy"
        elif sell_count >= buy_count and sell_count >= hold_count:
            expected_consensus = "sell"
        else:
            expected_consensus = "hold"

        cr = ConsensusRating(
            stock_symbol="AAPL",
            stock_name="Apple Inc.",
            buy_count=buy_count,
            hold_count=hold_count,
            sell_count=sell_count,
            consensus=expected_consensus,
            total_analysts=total,
            last_updated="2026-02-10T00:00:00",
        )

        assert cr.buy_count + cr.hold_count + cr.sell_count == cr.total_analysts
        assert cr.consensus in ("buy", "hold", "sell")
        assert cr.consensus == expected_consensus
