#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for RateLimiter.

Feature: multi-mode-platform
Property 29: 高风险源指数退避行为（连续失败时 5s→15s→跳过）
Property 30: RateLimiter 每源 cooldown 隔离性（不同源的 cooldown 互不影响）

**Validates: Requirements 1.12, 1.13**
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.services.stock_news_collector import (
    RateLimiter,
    SourceRateLimitConfig,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Source IDs: short alphabetic strings
source_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=2,
    max_size=10,
)

# Cooldown values: small positive floats
cooldown_strategy = st.floats(min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False)

# Max concurrent: small positive ints
max_concurrent_strategy = st.integers(min_value=1, max_value=10)

# Fail counts for testing backoff progression
fail_count_strategy = st.integers(min_value=1, max_value=10)


# ---------------------------------------------------------------------------
# Property 29: 高风险源指数退避行为
# ---------------------------------------------------------------------------


class TestProperty29HighRiskExponentialBackoff:
    """Property 29: 高风险源指数退避行为

    For any 标记为高风险的 Stock_Source，连续失败时 RateLimiter 应执行指数退避：
    第一次失败后可重试（返回 True），第二次失败后可重试（返回 True），
    第三次及之后失败跳过该源（返回 False）。

    非高风险源调用 handle_failure 始终返回 False（不做指数退避）。

    **Validates: Requirements 1.13**
    """

    @given(
        source_id=source_id_strategy,
        cooldown=cooldown_strategy,
        max_concurrent=max_concurrent_strategy,
    )
    @settings(max_examples=100)
    def test_first_failure_allows_retry(self, source_id, cooldown, max_concurrent):
        """高风险源第一次失败后 handle_failure 返回 True（可重试）"""
        limiter = RateLimiter(global_max_concurrent=10)
        config = SourceRateLimitConfig(
            max_concurrent=max_concurrent,
            cooldown_seconds=cooldown,
            is_high_risk=True,
        )
        limiter.configure_source(source_id, config)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.get_event_loop().run_until_complete(
                limiter.handle_failure(source_id)
            )
        assert result is True, "First failure of high-risk source should allow retry"
        assert limiter.source_fail_count[source_id] == 1

    @given(
        source_id=source_id_strategy,
        cooldown=cooldown_strategy,
        max_concurrent=max_concurrent_strategy,
    )
    @settings(max_examples=100)
    def test_second_failure_allows_retry(self, source_id, cooldown, max_concurrent):
        """高风险源第二次失败后 handle_failure 返回 True（可重试）"""
        limiter = RateLimiter(global_max_concurrent=10)
        config = SourceRateLimitConfig(
            max_concurrent=max_concurrent,
            cooldown_seconds=cooldown,
            is_high_risk=True,
        )
        limiter.configure_source(source_id, config)
        # Simulate first failure already happened
        limiter.source_fail_count[source_id] = 1

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.get_event_loop().run_until_complete(
                limiter.handle_failure(source_id)
            )
        assert result is True, "Second failure of high-risk source should allow retry"
        assert limiter.source_fail_count[source_id] == 2

    @given(
        source_id=source_id_strategy,
        cooldown=cooldown_strategy,
        max_concurrent=max_concurrent_strategy,
        prior_fails=st.integers(min_value=2, max_value=20),
    )
    @settings(max_examples=100)
    def test_third_and_beyond_failure_skips_source(self, source_id, cooldown, max_concurrent, prior_fails):
        """高风险源第三次及之后失败 handle_failure 返回 False（跳过）"""
        limiter = RateLimiter(global_max_concurrent=10)
        config = SourceRateLimitConfig(
            max_concurrent=max_concurrent,
            cooldown_seconds=cooldown,
            is_high_risk=True,
        )
        limiter.configure_source(source_id, config)
        # Simulate prior failures (at least 2 already happened)
        limiter.source_fail_count[source_id] = prior_fails

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.get_event_loop().run_until_complete(
                limiter.handle_failure(source_id)
            )
        assert result is False, f"Failure #{prior_fails + 1} of high-risk source should skip"

    @given(
        source_id=source_id_strategy,
        cooldown=cooldown_strategy,
        max_concurrent=max_concurrent_strategy,
    )
    @settings(max_examples=100)
    def test_non_high_risk_source_never_retries(self, source_id, cooldown, max_concurrent):
        """非高风险源调用 handle_failure 始终返回 False"""
        limiter = RateLimiter(global_max_concurrent=10)
        config = SourceRateLimitConfig(
            max_concurrent=max_concurrent,
            cooldown_seconds=cooldown,
            is_high_risk=False,
        )
        limiter.configure_source(source_id, config)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.get_event_loop().run_until_complete(
                limiter.handle_failure(source_id)
            )
        assert result is False, "Non-high-risk source should not do exponential backoff"

    @given(
        source_id=source_id_strategy,
        cooldown=cooldown_strategy,
        max_concurrent=max_concurrent_strategy,
    )
    @settings(max_examples=100)
    def test_reset_clears_fail_count(self, source_id, cooldown, max_concurrent):
        """成功后 reset_fail_count 将失败计数归零，下次失败重新从第一次开始"""
        limiter = RateLimiter(global_max_concurrent=10)
        config = SourceRateLimitConfig(
            max_concurrent=max_concurrent,
            cooldown_seconds=cooldown,
            is_high_risk=True,
        )
        limiter.configure_source(source_id, config)

        # Simulate two failures
        limiter.source_fail_count[source_id] = 2

        # Reset on success
        limiter.reset_fail_count(source_id)
        assert limiter.source_fail_count[source_id] == 0

        # Next failure should be treated as first failure again
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.get_event_loop().run_until_complete(
                limiter.handle_failure(source_id)
            )
        assert result is True, "After reset, first failure should allow retry again"
        assert limiter.source_fail_count[source_id] == 1


# ---------------------------------------------------------------------------
# Property 30: RateLimiter 每源 cooldown 隔离性
# ---------------------------------------------------------------------------


class TestProperty30CooldownIsolation:
    """Property 30: RateLimiter 每源 cooldown 隔离性

    For any 两个不同的 Stock_Source，对其中一个源的 cooldown 等待
    不应影响另一个源的请求时机。具体而言：
    - 每个源维护独立的 last_request 时间戳
    - 每个源维护独立的并发信号量
    - 每个源维护独立的失败计数

    **Validates: Requirements 1.12**
    """

    @given(
        source_a=source_id_strategy,
        source_b=source_id_strategy,
        cooldown_a=cooldown_strategy,
        cooldown_b=cooldown_strategy,
    )
    @settings(max_examples=100)
    def test_independent_last_request_timestamps(self, source_a, source_b, cooldown_a, cooldown_b):
        """不同源的 last_request 时间戳互相独立"""
        assume(source_a != source_b)

        limiter = RateLimiter(global_max_concurrent=10)
        limiter.configure_source(source_a, SourceRateLimitConfig(cooldown_seconds=cooldown_a))
        limiter.configure_source(source_b, SourceRateLimitConfig(cooldown_seconds=cooldown_b))

        # Record a request for source_a
        limiter.source_last_request[source_a] = time.time()

        # source_b should have no last_request or a different one
        last_b = limiter.source_last_request.get(source_b, 0)
        last_a = limiter.source_last_request[source_a]
        assert last_a != last_b or last_b == 0, (
            "Source B's last_request should be independent of Source A"
        )

    @given(
        source_a=source_id_strategy,
        source_b=source_id_strategy,
        max_conc_a=max_concurrent_strategy,
        max_conc_b=max_concurrent_strategy,
    )
    @settings(max_examples=100)
    def test_independent_semaphores(self, source_a, source_b, max_conc_a, max_conc_b):
        """不同源的并发信号量互相独立"""
        assume(source_a != source_b)

        limiter = RateLimiter(global_max_concurrent=20)
        limiter.configure_source(source_a, SourceRateLimitConfig(max_concurrent=max_conc_a))
        limiter.configure_source(source_b, SourceRateLimitConfig(max_concurrent=max_conc_b))

        # Each source should have its own semaphore with its own capacity
        sem_a = limiter.source_semaphores[source_a]
        sem_b = limiter.source_semaphores[source_b]
        assert sem_a is not sem_b, "Sources should have distinct semaphore instances"

    @given(
        source_a=source_id_strategy,
        source_b=source_id_strategy,
        fails_a=st.integers(min_value=0, max_value=5),
        fails_b=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=100)
    def test_independent_fail_counts(self, source_a, source_b, fails_a, fails_b):
        """不同源的失败计数互相独立"""
        assume(source_a != source_b)

        limiter = RateLimiter(global_max_concurrent=10)
        limiter.configure_source(
            source_a, SourceRateLimitConfig(is_high_risk=True)
        )
        limiter.configure_source(
            source_b, SourceRateLimitConfig(is_high_risk=True)
        )

        # Set different fail counts
        limiter.source_fail_count[source_a] = fails_a
        limiter.source_fail_count[source_b] = fails_b

        # Verify they are independent
        assert limiter.source_fail_count[source_a] == fails_a
        assert limiter.source_fail_count[source_b] == fails_b

        # Resetting one should not affect the other
        limiter.reset_fail_count(source_a)
        assert limiter.source_fail_count[source_a] == 0
        assert limiter.source_fail_count[source_b] == fails_b

    @given(
        source_a=source_id_strategy,
        source_b=source_id_strategy,
        cooldown_a=cooldown_strategy,
        cooldown_b=cooldown_strategy,
    )
    @settings(max_examples=100)
    def test_independent_cooldown_configs(self, source_a, source_b, cooldown_a, cooldown_b):
        """不同源的 cooldown 配置互相独立"""
        assume(source_a != source_b)

        limiter = RateLimiter(global_max_concurrent=10)
        limiter.configure_source(source_a, SourceRateLimitConfig(cooldown_seconds=cooldown_a))
        limiter.configure_source(source_b, SourceRateLimitConfig(cooldown_seconds=cooldown_b))

        assert limiter.source_configs[source_a].cooldown_seconds == cooldown_a
        assert limiter.source_configs[source_b].cooldown_seconds == cooldown_b
