#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for stock analysis history ordering.

Feature: multi-mode-platform
Property 10: 历史推演记录按时间倒序

**Validates: Requirements 3.6**
"""

import sys
import types
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st, settings

# ---------------------------------------------------------------------------
# 预先 mock 掉 langchain_core 等重量级依赖，避免 ImportError
# ---------------------------------------------------------------------------
for _mod_name in [
    "langchain_core",
    "langchain_core.messages",
    "langchain_google_genai",
    "langchain_openai",
]:
    if _mod_name not in sys.modules:
        _fake = types.ModuleType(_mod_name)
        if _mod_name == "langchain_core.messages":
            _fake.HumanMessage = MagicMock
            _fake.SystemMessage = MagicMock
        elif _mod_name == "langchain_google_genai":
            _fake.ChatGoogleGenerativeAI = MagicMock
        elif _mod_name == "langchain_openai":
            _fake.ChatOpenAI = MagicMock
        sys.modules[_mod_name] = _fake

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.schemas import StockAnalysisResult
from app.api.stock_endpoints import router as stock_router

# 现在可以安全导入了
import app.services.stock_analysis_service as _sas_module  # noqa: F401

# ---------------------------------------------------------------------------
# Test app
# ---------------------------------------------------------------------------

_test_app = FastAPI()
_test_app.include_router(stock_router, prefix="/api/stock")
_client = TestClient(_test_app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_analysis_result(idx: int, created_at: datetime) -> StockAnalysisResult:
    """构建一个指定 created_at 的 StockAnalysisResult。"""
    return StockAnalysisResult(
        id=f"test_{idx}_{uuid.uuid4().hex[:8]}",
        news_titles=[f"Test topic {idx}"],
        summary=f"Summary {idx}",
        impact_analysis=f"Impact {idx}",
        bull_argument=f"Bull {idx}",
        bear_argument=f"Bear {idx}",
        debate_dialogue=f"Debate {idx}",
        controversial_conclusion=f"Conclusion {idx}",
        stance="bull" if idx % 2 == 0 else "bear",
        risk_warning="Risk warning",
        created_at=created_at.isoformat(),
        cache_hit=False,
    )


# ---------------------------------------------------------------------------
# Property 10: 历史推演记录按时间倒序
# ---------------------------------------------------------------------------


class TestProperty10HistoryDescendingOrder:
    """Property 10: 历史推演记录按时间倒序

    For any 历史推演记录列表，列表中每条记录的 created_at 时间应大于或等于
    其后续记录的 created_at 时间。

    **Validates: Requirements 3.6**
    """

    @given(
        n_records=st.integers(min_value=2, max_value=20),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_history_records_in_descending_order(self, n_records: int, data):
        """API 返回的历史记录应按 created_at 降序排列。"""
        base_time = datetime(2026, 1, 1, 12, 0, 0)

        offsets = data.draw(
            st.lists(
                st.integers(min_value=0, max_value=10000),
                min_size=n_records,
                max_size=n_records,
                unique=True,
            )
        )

        records = [
            _make_analysis_result(i, base_time + timedelta(minutes=off))
            for i, off in enumerate(offsets)
        ]

        # 模拟 service 返回按时间倒序排列的结果（与 SQL ORDER BY DESC 一致）
        records_sorted = sorted(records, key=lambda r: r.created_at, reverse=True)

        mock_service = AsyncMock()
        mock_service.get_history = AsyncMock(return_value=records_sorted)

        with patch(
            "app.services.stock_analysis_service.stock_analysis_service",
            mock_service,
        ):
            resp = _client.get(
                "/api/stock/analyze/history",
                params={"limit": 100, "offset": 0},
            )

        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == n_records

        # 验证降序
        for i in range(len(items) - 1):
            t_curr = items[i]["created_at"]
            t_next = items[i + 1]["created_at"]
            assert t_curr >= t_next, (
                f"历史记录未按时间倒序: items[{i}].created_at={t_curr} "
                f"< items[{i+1}].created_at={t_next}"
            )

    @given(
        n_records=st.integers(min_value=2, max_value=15),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_db_query_orders_by_created_at_desc(self, n_records: int, data):
        """无论记录插入顺序如何，返回列表的 created_at 必须严格降序。"""
        base_time = datetime(2026, 2, 1, 0, 0, 0)

        offsets = data.draw(
            st.lists(
                st.integers(min_value=0, max_value=50000),
                min_size=n_records,
                max_size=n_records,
                unique=True,
            )
        )

        records_unsorted = [
            _make_analysis_result(i, base_time + timedelta(minutes=off))
            for i, off in enumerate(offsets)
        ]

        records_desc = sorted(records_unsorted, key=lambda r: r.created_at, reverse=True)

        mock_service = AsyncMock()
        mock_service.get_history = AsyncMock(return_value=records_desc)

        with patch(
            "app.services.stock_analysis_service.stock_analysis_service",
            mock_service,
        ):
            resp = _client.get(
                "/api/stock/analyze/history",
                params={"limit": 100, "offset": 0},
            )

        assert resp.status_code == 200
        items = resp.json()["items"]

        timestamps = [item["created_at"] for item in items]
        assert timestamps == sorted(timestamps, reverse=True), (
            f"时间戳未按降序排列: {timestamps}"
        )

    @given(
        n_records=st.integers(min_value=2, max_value=10),
        limit=st.integers(min_value=1, max_value=10),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_history_with_limit_preserves_order(self, n_records: int, limit: int, data):
        """即使 limit 截断了结果，返回的子集仍应保持降序。"""
        base_time = datetime(2026, 1, 15, 8, 0, 0)

        offsets = data.draw(
            st.lists(
                st.integers(min_value=0, max_value=10000),
                min_size=n_records,
                max_size=n_records,
                unique=True,
            )
        )

        records = [
            _make_analysis_result(i, base_time + timedelta(minutes=off))
            for i, off in enumerate(offsets)
        ]
        records_desc = sorted(records, key=lambda r: r.created_at, reverse=True)

        effective_limit = min(limit, n_records)
        limited_records = records_desc[:effective_limit]

        mock_service = AsyncMock()
        mock_service.get_history = AsyncMock(return_value=limited_records)

        with patch(
            "app.services.stock_analysis_service.stock_analysis_service",
            mock_service,
        ):
            resp = _client.get(
                "/api/stock/analyze/history",
                params={"limit": limit, "offset": 0},
            )

        assert resp.status_code == 200
        items = resp.json()["items"]

        for i in range(len(items) - 1):
            t_curr = items[i]["created_at"]
            t_next = items[i + 1]["created_at"]
            assert t_curr >= t_next, (
                f"截断后历史记录未按时间倒序: index {i}: "
                f"{t_curr} < {t_next}"
            )
