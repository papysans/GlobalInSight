#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for ProxyPoolManager.

Feature: multi-mode-platform
Property 35: 代理池轮换与排除

**Validates: Requirements 9.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.services.proxy_pool_manager import ProxyPoolManager


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

proxy_url_strategy = st.from_regex(
    r"(http|socks5)://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}",
    fullmatch=True,
)

proxy_list_strategy = st.lists(proxy_url_strategy, min_size=1, max_size=20, unique=True)


# ---------------------------------------------------------------------------
# Property 35: 代理池轮换与排除
# ---------------------------------------------------------------------------


class TestProperty35ProxyPoolRotationAndExclusion:
    """Property 35: 代理池轮换与排除

    For any ProxyPoolManager 实例，当某个代理被标记为失败后，
    后续调用 get_random_proxy() 不应返回该失败代理；
    当所有代理均失败时，get_random_proxy() 应返回 None。

    **Validates: Requirements 9.5**
    """

    @given(proxies=proxy_list_strategy)
    @settings(max_examples=100)
    def test_failed_proxy_excluded_from_selection(self, proxies):
        """标记为失败的代理不应被 get_random_proxy() 返回"""
        manager = ProxyPoolManager(proxies=proxies)
        assume(len(proxies) >= 2)

        # Mark the first proxy as failed
        failed = proxies[0]
        manager.mark_failed(failed)

        # Sample multiple times — failed proxy should never appear
        for _ in range(50):
            result = manager.get_random_proxy()
            assert result != failed, (
                f"Failed proxy {failed} should not be returned"
            )

    @given(proxies=proxy_list_strategy)
    @settings(max_examples=100)
    def test_all_proxies_failed_returns_none(self, proxies):
        """所有代理均失败时 get_random_proxy() 返回 None"""
        manager = ProxyPoolManager(proxies=proxies)

        for p in proxies:
            manager.mark_failed(p)

        result = manager.get_random_proxy()
        assert result is None, (
            "Should return None when all proxies have failed"
        )

    @given(proxies=proxy_list_strategy)
    @settings(max_examples=100)
    def test_get_random_proxy_returns_configured_proxy(self, proxies):
        """get_random_proxy() 返回的代理必须来自配置列表"""
        manager = ProxyPoolManager(proxies=proxies)

        result = manager.get_random_proxy()
        assert result in proxies, (
            f"Returned proxy {result} not in configured list"
        )

    @given(proxies=proxy_list_strategy)
    @settings(max_examples=100)
    def test_reset_failed_restores_all_proxies(self, proxies):
        """reset_failed() 后所有代理重新可用"""
        manager = ProxyPoolManager(proxies=proxies)

        # Fail all
        for p in proxies:
            manager.mark_failed(p)
        assert manager.get_random_proxy() is None

        # Reset
        manager.reset_failed()
        result = manager.get_random_proxy()
        assert result is not None, "After reset, proxies should be available"
        assert result in proxies

    def test_empty_proxy_list_returns_none(self):
        """空代理列表时 get_random_proxy() 返回 None"""
        manager = ProxyPoolManager(proxies=[])
        assert manager.get_random_proxy() is None

    @given(proxies=proxy_list_strategy)
    @settings(max_examples=100)
    def test_available_count_decreases_on_failure(self, proxies):
        """每标记一个代理失败，available_count 减少 1"""
        manager = ProxyPoolManager(proxies=proxies)
        initial = manager.available_count

        manager.mark_failed(proxies[0])
        assert manager.available_count == initial - 1
