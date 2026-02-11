#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for stock news API endpoints.

Feature: multi-mode-platform
Property 5: 股票资讯按排名排序
Property 6: 平台筛选结果一致性
Property 11: 无效参数返回 400 错误
Property 26: 资讯类别筛选一致性

**Validates: Requirements 2.1, 2.4, 1.11, 7.4**
"""

from typing import List
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings, assume

from app.schemas import StockNewsItem, StockNewsCollectResponse
from app.api.stock_endpoints import router as stock_router

# ---------------------------------------------------------------------------
# Test app — uses only the stock router to avoid importing langgraph etc.
# ---------------------------------------------------------------------------

_test_app = FastAPI()
_test_app.include_router(stock_router, prefix="/api/stock")
_client = TestClient(_test_app)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

source_platforms = st.sampled_from(["akshare", "sina", "10jqka", "xueqiu", "tushare"])
categories = st.sampled_from(["domestic", "international", "research_report"])


def make_news_item(
    idx: int,
    rank: int,
    source_platform: str = "akshare",
    category: str = "domestic",
) -> StockNewsItem:
    """Helper to build a StockNewsItem with controlled rank and source."""
    return StockNewsItem(
        id=f"{source_platform}_{idx}",
        title=f"Test news {idx}",
        summary=f"Summary for news {idx}",
        source_platform=source_platform,
        source_name=f"Source {source_platform}",
        url=f"https://example.com/{idx}",
        published_time="2026-02-10T12:00:00",
        hot_value=str(rank),
        rank=rank,
        category=category,
    )


def _mock_collect(response: StockNewsCollectResponse):
    """Return a patch context manager that mocks stock_news_collector.collect_news.

    The collector is imported locally inside the endpoint function, so we
    patch the global instance in the services module.
    """
    return patch(
        "app.services.stock_news_collector.stock_news_collector",
        **{"collect_news": AsyncMock(return_value=response)},
    )


# ---------------------------------------------------------------------------
# Property 5: 股票资讯按排名排序
# ---------------------------------------------------------------------------


class TestProperty5StockNewsSortedByRank:
    """Property 5: 股票资讯按排名排序

    For any 股票热榜返回的资讯列表，同一数据源内每个条目的 rank 值
    应小于或等于其后续条目的 rank 值。

    **Validates: Requirements 2.1**
    """

    @given(
        ranks=st.lists(
            st.integers(min_value=1, max_value=500),
            min_size=2,
            max_size=20,
        ),
        platform=source_platforms,
    )
    @settings(max_examples=100)
    def test_items_from_single_source_preserve_rank_order(
        self, ranks: List[int], platform: str
    ):
        """单一数据源返回的条目应按 rank 升序排列"""
        sorted_ranks = sorted(ranks)
        items = [
            make_news_item(idx=i, rank=r, source_platform=platform)
            for i, r in enumerate(sorted_ranks)
        ]

        mock_response = StockNewsCollectResponse(
            success=True,
            items=items,
            total=len(items),
            source_stats={platform: len(items)},
            category_stats={"domestic": len(items)},
            collection_time="2026-02-10T12:00:00",
            from_cache=False,
        )

        with _mock_collect(mock_response):
            resp = _client.get(
                "/api/stock/news",
                params={"source": platform, "limit": 200},
            )

        assert resp.status_code == 200
        result_items = resp.json()["items"]

        for i in range(len(result_items) - 1):
            r_curr = result_items[i].get("rank")
            r_next = result_items[i + 1].get("rank")
            if r_curr is not None and r_next is not None:
                assert r_curr <= r_next, (
                    f"Items not sorted by rank: rank[{i}]={r_curr} > rank[{i+1}]={r_next}"
                )

    @given(
        n_sources=st.integers(min_value=2, max_value=3),
        items_per_source=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=100)
    def test_items_from_multiple_sources_each_ranked(
        self, n_sources: int, items_per_source: int
    ):
        """多数据源合并后，每个源内部的 rank 仍保持升序"""
        platforms = ["akshare", "sina", "10jqka"][:n_sources]
        all_items: List[StockNewsItem] = []
        for plat in platforms:
            for i in range(items_per_source):
                all_items.append(
                    make_news_item(idx=i, rank=i + 1, source_platform=plat)
                )

        mock_response = StockNewsCollectResponse(
            success=True,
            items=all_items,
            total=len(all_items),
            source_stats={p: items_per_source for p in platforms},
            category_stats={"domestic": len(all_items)},
            collection_time="2026-02-10T12:00:00",
            from_cache=False,
        )

        with _mock_collect(mock_response):
            resp = _client.get("/api/stock/news", params={"limit": 200})

        assert resp.status_code == 200
        result_items = resp.json()["items"]

        by_platform: dict[str, list] = {}
        for item in result_items:
            plat = item["source_platform"]
            by_platform.setdefault(plat, []).append(item)

        for plat, plat_items in by_platform.items():
            for i in range(len(plat_items) - 1):
                r_curr = plat_items[i].get("rank")
                r_next = plat_items[i + 1].get("rank")
                if r_curr is not None and r_next is not None:
                    assert r_curr <= r_next, (
                        f"[{plat}] rank not sorted: [{i}]={r_curr} > [{i+1}]={r_next}"
                    )


# ---------------------------------------------------------------------------
# Property 6: 平台筛选结果一致性
# ---------------------------------------------------------------------------


class TestProperty6PlatformFilterConsistency:
    """Property 6: 平台筛选结果一致性

    For any 平台筛选参数 P 和股票资讯列表，筛选后返回的每条
    StockNewsItem 的 source_platform 字段应等于 P。

    **Validates: Requirements 2.4**
    """

    @given(
        target_platform=source_platforms,
        other_platform=source_platforms,
        n_target=st.integers(min_value=1, max_value=10),
        n_other=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100)
    def test_source_filter_returns_only_matching_platform(
        self,
        target_platform: str,
        other_platform: str,
        n_target: int,
        n_other: int,
    ):
        """source 参数筛选后，所有返回条目的 source_platform 应等于指定平台"""
        assume(target_platform != other_platform)

        items: List[StockNewsItem] = []
        for i in range(n_target):
            items.append(
                make_news_item(idx=i, rank=i + 1, source_platform=target_platform)
            )
        for i in range(n_other):
            items.append(
                make_news_item(
                    idx=n_target + i, rank=n_target + i + 1,
                    source_platform=other_platform,
                )
            )

        mock_response = StockNewsCollectResponse(
            success=True,
            items=items,
            total=len(items),
            source_stats={target_platform: n_target, other_platform: n_other},
            category_stats={"domestic": len(items)},
            collection_time="2026-02-10T12:00:00",
            from_cache=False,
        )

        with _mock_collect(mock_response):
            resp = _client.get(
                "/api/stock/news",
                params={"source": target_platform, "limit": 200},
            )

        assert resp.status_code == 200
        data = resp.json()

        for item in data["items"]:
            assert item["source_platform"] == target_platform, (
                f"Expected source_platform={target_platform}, "
                f"got {item['source_platform']}"
            )

        assert data["total"] == n_target, (
            f"Expected {n_target} items for platform {target_platform}, "
            f"got {data['total']}"
        )


# ---------------------------------------------------------------------------
# Property 11: 无效参数返回 400 错误
# ---------------------------------------------------------------------------


class TestProperty11InvalidParamsReturn400:
    """Property 11: 无效参数返回 400 错误

    For any 包含无效参数的 API 请求（如负数 limit、不存在的 category），
    API 应返回 HTTP 400 状态码和包含错误描述的响应体。

    **Validates: Requirements 7.4**
    """

    @given(limit=st.integers(max_value=0))
    @settings(max_examples=100)
    def test_negative_or_zero_limit_returns_400(self, limit: int):
        """limit <= 0 时应返回 400"""
        resp = _client.get("/api/stock/news", params={"limit": limit})
        assert resp.status_code == 400, (
            f"Expected 400 for limit={limit}, got {resp.status_code}"
        )
        assert "detail" in resp.json()

    @given(limit=st.integers(min_value=201, max_value=10000))
    @settings(max_examples=100)
    def test_limit_exceeding_max_returns_400(self, limit: int):
        """limit > 200 时应返回 400"""
        resp = _client.get("/api/stock/news", params={"limit": limit})
        assert resp.status_code == 400, (
            f"Expected 400 for limit={limit}, got {resp.status_code}"
        )
        assert "detail" in resp.json()

    @given(
        category=st.text(min_size=1, max_size=30).filter(
            lambda s: s.strip() not in ("domestic", "international", "research_report", "")
        ),
    )
    @settings(max_examples=100)
    def test_invalid_category_returns_400(self, category: str):
        """无效的 category 参数应返回 400"""
        resp = _client.get("/api/stock/news", params={"category": category})
        assert resp.status_code == 400, (
            f"Expected 400 for category='{category}', got {resp.status_code}"
        )
        assert "detail" in resp.json()


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
        target_category=categories,
        n_target=st.integers(min_value=1, max_value=10),
        n_other=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100)
    def test_category_filter_returns_only_matching_category(
        self,
        target_category: str,
        n_target: int,
        n_other: int,
    ):
        """category 参数筛选后，所有返回条目的 category 应等于指定类别"""
        other_categories = [
            c for c in ("domestic", "international", "research_report")
            if c != target_category
        ]
        other_category = other_categories[0]

        items: List[StockNewsItem] = []
        for i in range(n_target):
            items.append(
                make_news_item(
                    idx=i, rank=i + 1,
                    source_platform="akshare" if target_category == "domestic" else "finnhub",
                    category=target_category,
                )
            )
        for i in range(n_other):
            items.append(
                make_news_item(
                    idx=n_target + i, rank=n_target + i + 1,
                    source_platform="sina" if other_category == "domestic" else "newsapi",
                    category=other_category,
                )
            )

        mock_response = StockNewsCollectResponse(
            success=True,
            items=items,
            total=len(items),
            source_stats={"mixed": len(items)},
            category_stats={target_category: n_target, other_category: n_other},
            collection_time="2026-02-10T12:00:00",
            from_cache=False,
        )

        with _mock_collect(mock_response):
            resp = _client.get(
                "/api/stock/news",
                params={"category": target_category, "limit": 200},
            )

        assert resp.status_code == 200
        data = resp.json()

        for item in data["items"]:
            assert item["category"] == target_category, (
                f"Expected category={target_category}, got {item['category']}"
            )

        assert data["total"] == n_target, (
            f"Expected {n_target} items for category {target_category}, "
            f"got {data['total']}"
        )

    @given(target_category=categories)
    @settings(max_examples=100)
    def test_category_filter_with_empty_result(self, target_category: str):
        """当没有匹配类别的条目时，应返回空列表"""
        other_category = (
            "international" if target_category == "domestic" else "domestic"
        )

        items = [
            make_news_item(idx=0, rank=1, source_platform="akshare", category=other_category)
        ]

        mock_response = StockNewsCollectResponse(
            success=True,
            items=items,
            total=len(items),
            source_stats={"akshare": 1},
            category_stats={other_category: 1},
            collection_time="2026-02-10T12:00:00",
            from_cache=False,
        )

        with _mock_collect(mock_response):
            resp = _client.get(
                "/api/stock/news",
                params={"category": target_category, "limit": 200},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
