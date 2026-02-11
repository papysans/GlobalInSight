#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for CookiePoolManager.

Feature: multi-mode-platform
Property 37: Cookie 池轮换与失效排除

**Validates: Requirements 9.7**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.services.cookie_pool_manager import CookiePoolManager


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

source_strategy = st.sampled_from(["eastmoney", "xueqiu", "10jqka"])

cookie_dict_strategy = st.fixed_dictionaries({
    "session_id": st.text(min_size=5, max_size=20),
    "token": st.text(min_size=5, max_size=30),
})

cookie_list_strategy = st.lists(cookie_dict_strategy, min_size=1, max_size=10, unique_by=lambda c: (c["session_id"], c["token"]))


# ---------------------------------------------------------------------------
# Property 37: Cookie 池轮换与失效排除
# ---------------------------------------------------------------------------


class TestProperty37CookiePoolRotationAndExclusion:
    """Property 37: Cookie 池轮换与失效排除

    For any CookiePoolManager 实例，当某组 Cookie 被标记为失效后，
    后续调用 get_cookie() 不应返回该失效 Cookie。

    **Validates: Requirements 9.7**
    """

    @given(source=source_strategy, cookies=cookie_list_strategy)
    @settings(max_examples=100)
    def test_invalid_cookie_excluded(self, source, cookies):
        """标记为失效的 Cookie 不应被 get_cookie() 返回"""
        assume(len(cookies) >= 2)

        manager = CookiePoolManager()
        manager.add_cookies(source, cookies)

        # Mark the first cookie as invalid
        manager.mark_invalid(source, 0)
        invalid_cookie = cookies[0]

        # Sample multiple times
        for _ in range(50):
            result = manager.get_cookie(source)
            assert result is not None, "Should still have valid cookies"
            assert result != invalid_cookie, (
                "Invalid cookie should not be returned"
            )

    @given(source=source_strategy, cookies=cookie_list_strategy)
    @settings(max_examples=100)
    def test_all_invalid_returns_none(self, source, cookies):
        """所有 Cookie 失效时 get_cookie() 返回 None"""
        manager = CookiePoolManager()
        manager.add_cookies(source, cookies)

        for i in range(len(cookies)):
            manager.mark_invalid(source, i)

        result = manager.get_cookie(source)
        assert result is None, "Should return None when all cookies are invalid"

    @given(source=source_strategy, cookies=cookie_list_strategy)
    @settings(max_examples=100)
    def test_get_cookie_returns_from_pool(self, source, cookies):
        """get_cookie() 返回的 Cookie 必须来自配置池"""
        manager = CookiePoolManager()
        manager.add_cookies(source, cookies)

        result = manager.get_cookie(source)
        assert result in cookies, "Returned cookie must be from the pool"

    @given(source=source_strategy, cookies=cookie_list_strategy)
    @settings(max_examples=100)
    def test_valid_count_decreases_on_invalidation(self, source, cookies):
        """每标记一个 Cookie 失效，valid_count 减少 1"""
        manager = CookiePoolManager()
        manager.add_cookies(source, cookies)

        initial = manager.valid_count(source)
        manager.mark_invalid(source, 0)
        assert manager.valid_count(source) == initial - 1

    def test_unknown_source_returns_none(self):
        """未配置的数据源 get_cookie() 返回 None"""
        manager = CookiePoolManager()
        assert manager.get_cookie("unknown") is None

    @given(
        source_a=st.just("eastmoney"),
        source_b=st.just("xueqiu"),
        cookies_a=cookie_list_strategy,
        cookies_b=cookie_list_strategy,
    )
    @settings(max_examples=100)
    def test_sources_are_independent(self, source_a, source_b, cookies_a, cookies_b):
        """不同数据源的 Cookie 池互相独立"""
        manager = CookiePoolManager()
        manager.add_cookies(source_a, cookies_a)
        manager.add_cookies(source_b, cookies_b)

        # Invalidate all cookies for source_a
        for i in range(len(cookies_a)):
            manager.mark_invalid(source_a, i)

        assert manager.get_cookie(source_a) is None
        # source_b should be unaffected
        result_b = manager.get_cookie(source_b)
        assert result_b is not None
        assert result_b in cookies_b
