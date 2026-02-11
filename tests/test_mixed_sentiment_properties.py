#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for MixedSentimentDataService.

Feature: multi-mode-platform
Property 45: 混合数据源权重重分配正确性
Property 46: AKShare 聚合指标归一化范围
Property 40: 情绪指数计算正确性（加权模型）

**Validates: Requirements 9.10, 9.11, 9.12, 9.13, 9.17**
"""

import math

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.services.mixed_sentiment_data_service import (
    MixedSentimentDataService,
    DEFAULT_SENTIMENT_WEIGHTS,
)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Score in valid range or None (simulating unavailable source)
score_or_none = st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0))

# Always-valid score (non-None)
valid_score = st.floats(min_value=0.0, max_value=100.0)

# Metrics dict matching collect_all_metrics() output shape
metrics_strategy = st.fixed_dictionaries({
    "baidu_vote_score": score_or_none,
    "akshare_aggregate_score": score_or_none,
    "news_sentiment_score": score_or_none,
    "margin_trading_score": score_or_none,
    "xueqiu_heat": score_or_none,
    "source_availability": st.just({}),
})

# Custom weights: positive floats for each source key, will be used as-is
weight_keys = list(DEFAULT_SENTIMENT_WEIGHTS.keys())

positive_weight = st.floats(min_value=0.01, max_value=1.0)

custom_weights_strategy = st.fixed_dictionaries({
    k: positive_weight for k in weight_keys
})


# ---------------------------------------------------------------------------
# Property 45: 混合数据源权重重分配正确性
# ---------------------------------------------------------------------------


class TestProperty45WeightRedistribution:
    """Property 45: 混合数据源权重重分配正确性

    For any partial data source availability, calculate_weighted_index()
    effective_weights must sum to 1.0 (±0.01 tolerance), and unavailable
    sources must have zero weight.

    **Validates: Requirements 9.17**
    """

    @given(comment_score=score_or_none, metrics=metrics_strategy)
    @settings(max_examples=200)
    def test_effective_weights_sum_to_one(self, comment_score, metrics):
        """effective_weights 总和应为 1.0（允许浮点误差 ±0.01）"""
        svc = MixedSentimentDataService()
        result = svc.calculate_weighted_index(comment_score, metrics)

        ew = result["effective_weights"]
        if ew:
            total = sum(ew.values())
            assert abs(total - 1.0) < 0.01, (
                f"effective_weights sum {total} deviates from 1.0 by more than 0.01"
            )

    @given(comment_score=score_or_none, metrics=metrics_strategy)
    @settings(max_examples=200)
    def test_unavailable_sources_have_zero_weight(self, comment_score, metrics):
        """不可用数据源的权重应为 0（不出现在 effective_weights 中）"""
        svc = MixedSentimentDataService()
        result = svc.calculate_weighted_index(comment_score, metrics)

        ew = result["effective_weights"]

        # Build the set of unavailable source keys
        score_map = {
            "comment_sentiment": comment_score,
            "baidu_vote": metrics.get("baidu_vote_score"),
            "akshare_aggregate": metrics.get("akshare_aggregate_score"),
            "news_sentiment": metrics.get("news_sentiment_score"),
            "margin_trading": metrics.get("margin_trading_score"),
        }

        for key, score in score_map.items():
            if score is None:
                assert key not in ew, (
                    f"Unavailable source '{key}' should not appear in effective_weights"
                )

    @given(
        comment_score=score_or_none,
        metrics=metrics_strategy,
        custom_weights=custom_weights_strategy,
    )
    @settings(max_examples=200)
    def test_custom_weights_redistribution(self, comment_score, metrics, custom_weights):
        """使用自定义权重时，重分配后 effective_weights 总和仍为 1.0"""
        svc = MixedSentimentDataService()
        result = svc.calculate_weighted_index(comment_score, metrics, custom_weights)

        ew = result["effective_weights"]
        if ew:
            total = sum(ew.values())
            assert abs(total - 1.0) < 0.01, (
                f"Custom weights: effective_weights sum {total} deviates from 1.0"
            )


# ---------------------------------------------------------------------------
# Property 46: AKShare 聚合指标归一化范围
# ---------------------------------------------------------------------------


class TestProperty46NormalizationRange:
    """Property 46: AKShare 聚合指标归一化范围

    For any non-None sub-scores returned by calculate_weighted_index(),
    values must be in the 0-100 range.

    **Validates: Requirements 9.10, 9.11, 9.12, 9.13**
    """

    @given(comment_score=score_or_none, metrics=metrics_strategy)
    @settings(max_examples=200)
    def test_sub_scores_in_range(self, comment_score, metrics):
        """所有非 None 分项得分必须在 0-100 范围内"""
        svc = MixedSentimentDataService()
        result = svc.calculate_weighted_index(comment_score, metrics)

        score_fields = [
            "comment_sentiment_score",
            "baidu_vote_score",
            "akshare_aggregate_score",
            "news_sentiment_score",
            "margin_trading_score",
        ]

        for field in score_fields:
            val = result.get(field)
            if val is not None:
                assert 0.0 <= val <= 100.0, (
                    f"{field} = {val} is outside 0-100 range"
                )

    @given(comment_score=score_or_none, metrics=metrics_strategy)
    @settings(max_examples=200)
    def test_index_value_in_range(self, comment_score, metrics):
        """综合指数 index_value 必须在 0-100 范围内"""
        svc = MixedSentimentDataService()
        result = svc.calculate_weighted_index(comment_score, metrics)

        iv = result["index_value"]
        assert 0.0 <= iv <= 100.0, (
            f"index_value {iv} is outside 0-100 range"
        )


# ---------------------------------------------------------------------------
# Property 40: 情绪指数计算正确性（加权模型）
# ---------------------------------------------------------------------------


class TestProperty40WeightedIndexCorrectness:
    """Property 40: 情绪指数计算正确性（加权模型）

    For any set of classified comments and mixed data source metrics,
    calculate_weighted_index() returns an index_value equal to the weighted
    sum of available source scores (with redistributed weights summing to 1.0),
    clamped to 0-100.

    **Validates: Requirements 9.17**
    """

    @given(comment_score=valid_score, metrics=metrics_strategy)
    @settings(max_examples=200)
    def test_index_equals_weighted_sum(self, comment_score, metrics):
        """index_value 应等于各可用数据源得分的加权求和"""
        svc = MixedSentimentDataService()
        result = svc.calculate_weighted_index(comment_score, metrics)

        ew = result["effective_weights"]
        if not ew:
            # No available sources with weight → default 50
            assert result["index_value"] == 50.0
            return

        # Manually compute expected weighted sum
        score_map = {
            "comment_sentiment": comment_score,
            "baidu_vote": metrics.get("baidu_vote_score"),
            "akshare_aggregate": metrics.get("akshare_aggregate_score"),
            "news_sentiment": metrics.get("news_sentiment_score"),
            "margin_trading": metrics.get("margin_trading_score"),
        }

        expected = 0.0
        for key, weight in ew.items():
            score = score_map.get(key)
            if score is not None:
                expected += score * weight

        expected = max(0.0, min(100.0, expected))

        assert abs(result["index_value"] - expected) < 0.01, (
            f"index_value {result['index_value']} != expected {expected}"
        )

    @given(
        scores=st.lists(valid_score, min_size=5, max_size=5),
    )
    @settings(max_examples=100)
    def test_all_sources_available_uses_default_weights(self, scores):
        """所有数据源可用时，使用默认权重（无重分配）"""
        svc = MixedSentimentDataService()

        comment_score = scores[0]
        metrics = {
            "baidu_vote_score": scores[1],
            "akshare_aggregate_score": scores[2],
            "news_sentiment_score": scores[3],
            "margin_trading_score": scores[4],
            "source_availability": {},
        }

        result = svc.calculate_weighted_index(comment_score, metrics)
        ew = result["effective_weights"]

        # When all sources available, effective weights should match defaults
        for key in DEFAULT_SENTIMENT_WEIGHTS:
            assert abs(ew[key] - DEFAULT_SENTIMENT_WEIGHTS[key]) < 0.01, (
                f"Weight for {key}: {ew[key]} != default {DEFAULT_SENTIMENT_WEIGHTS[key]}"
            )

    @given(comment_score=valid_score)
    @settings(max_examples=100)
    def test_only_comment_score_available(self, comment_score):
        """仅评论情绪分可用时，index_value 应等于 comment_score"""
        svc = MixedSentimentDataService()

        metrics = {
            "baidu_vote_score": None,
            "akshare_aggregate_score": None,
            "news_sentiment_score": None,
            "margin_trading_score": None,
            "source_availability": {},
        }

        result = svc.calculate_weighted_index(comment_score, metrics)

        # Only comment_sentiment available → its weight becomes 1.0
        assert abs(result["index_value"] - comment_score) < 0.01, (
            f"With only comment score, index should equal comment_score "
            f"({comment_score}), got {result['index_value']}"
        )
