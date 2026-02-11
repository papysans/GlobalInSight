#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for AdaptiveRateController.

Feature: multi-mode-platform
Property 36: 请求频率自适应控制状态机

**Validates: Requirements 9.6**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.services.adaptive_rate_controller import AdaptiveRateController


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

source_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=2, max_size=10,
)

base_cooldown_strategy = st.floats(
    min_value=0.5, max_value=10.0,
    allow_nan=False, allow_infinity=False,
)

anti_crawl_count_strategy = st.integers(min_value=1, max_value=6)


# ---------------------------------------------------------------------------
# Property 36: 请求频率自适应控制状态机
# ---------------------------------------------------------------------------


class TestProperty36AdaptiveRateControlStateMachine:
    """Property 36: 请求频率自适应控制状态机

    For any AdaptiveRateController 实例和数据源，检测到反爬信号后
    cooldown 应翻倍（不超过 60 秒上限）；连续 3 次成功后 cooldown
    应恢复为 base_cooldown。

    **Validates: Requirements 9.6**
    """

    @given(source=source_strategy, base_cd=base_cooldown_strategy)
    @settings(max_examples=100)
    def test_cooldown_doubles_on_anti_crawl(self, source, base_cd):
        """检测到反爬信号后 cooldown 翻倍"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)
        assert ctrl.get_cooldown(source) == base_cd

        ctrl.on_anti_crawl_detected(source)
        expected = min(base_cd * 2, AdaptiveRateController.MAX_COOLDOWN)
        assert ctrl.get_cooldown(source) == pytest.approx(expected, rel=1e-9)

    @given(
        source=source_strategy,
        base_cd=base_cooldown_strategy,
        n_detections=anti_crawl_count_strategy,
    )
    @settings(max_examples=100)
    def test_cooldown_capped_at_max(self, source, base_cd, n_detections):
        """连续多次反爬检测后 cooldown 不超过 MAX_COOLDOWN"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)

        for _ in range(n_detections):
            ctrl.on_anti_crawl_detected(source)

        assert ctrl.get_cooldown(source) <= AdaptiveRateController.MAX_COOLDOWN

    @given(source=source_strategy, base_cd=base_cooldown_strategy)
    @settings(max_examples=100)
    def test_three_successes_restore_base_cooldown(self, source, base_cd):
        """连续 3 次成功后 cooldown 恢复为 base_cooldown"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)

        # Trigger anti-crawl to raise cooldown
        ctrl.on_anti_crawl_detected(source)
        assert ctrl.get_cooldown(source) > base_cd or base_cd * 2 >= AdaptiveRateController.MAX_COOLDOWN

        # 3 consecutive successes
        ctrl.on_success(source)
        ctrl.on_success(source)
        ctrl.on_success(source)

        assert ctrl.get_cooldown(source) == pytest.approx(base_cd, rel=1e-9)

    @given(source=source_strategy, base_cd=base_cooldown_strategy)
    @settings(max_examples=100)
    def test_anti_crawl_resets_success_counter(self, source, base_cd):
        """反爬检测重置连续成功计数"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)

        # 2 successes, then anti-crawl
        ctrl.on_success(source)
        ctrl.on_success(source)
        ctrl.on_anti_crawl_detected(source)

        # 2 more successes should NOT restore (need 3 consecutive)
        ctrl.on_success(source)
        ctrl.on_success(source)
        expected_after_anti = min(base_cd * 2, AdaptiveRateController.MAX_COOLDOWN)
        assert ctrl.get_cooldown(source) == pytest.approx(expected_after_anti, rel=1e-9)

        # 3rd success restores
        ctrl.on_success(source)
        assert ctrl.get_cooldown(source) == pytest.approx(base_cd, rel=1e-9)

    @given(source=source_strategy, base_cd=base_cooldown_strategy)
    @settings(max_examples=100)
    def test_detect_anti_crawl_403(self, source, base_cd):
        """HTTP 403 被检测为反爬信号"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)
        assert ctrl.detect_anti_crawl(403, "Forbidden") is True

    @given(source=source_strategy, base_cd=base_cooldown_strategy)
    @settings(max_examples=100)
    def test_detect_anti_crawl_429(self, source, base_cd):
        """HTTP 429 被检测为反爬信号"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)
        assert ctrl.detect_anti_crawl(429, "Too Many Requests") is True

    @given(source=source_strategy, base_cd=base_cooldown_strategy)
    @settings(max_examples=100)
    def test_detect_anti_crawl_captcha(self, source, base_cd):
        """包含验证码关键词的响应被检测为反爬信号"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)
        assert ctrl.detect_anti_crawl(200, "请输入验证码") is True
        assert ctrl.detect_anti_crawl(200, "Please solve the CAPTCHA") is True

    @given(source=source_strategy, base_cd=base_cooldown_strategy)
    @settings(max_examples=100)
    def test_detect_anti_crawl_empty_response(self, source, base_cd):
        """空响应被检测为反爬信号"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)
        assert ctrl.detect_anti_crawl(200, "") is True
        assert ctrl.detect_anti_crawl(200, "   ") is True

    @given(source=source_strategy, base_cd=base_cooldown_strategy)
    @settings(max_examples=100)
    def test_normal_response_not_anti_crawl(self, source, base_cd):
        """正常响应不被检测为反爬信号"""
        ctrl = AdaptiveRateController(base_cooldown=base_cd)
        assert ctrl.detect_anti_crawl(200, '{"data": [1,2,3]}') is False
