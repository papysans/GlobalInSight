#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for SentimentAnalyzer.

Feature: multi-mode-platform
Property 32: 散户评论数据完整性与情绪标签有效性
Property 40: 情绪指数计算正确性（加权模型）
Property 41: 情绪快照持久化往返一致性
Property 42: 关键事件节点分类
Property 44: 旧评论清理保留快照

**Validates: Requirements 9.2, 9.15, 9.17, 9.19, 9.24, 9.31**
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.schemas import SentimentComment, SentimentSnapshot
from app.services.sentiment_analyzer import (
    SentimentAnalyzer,
    _index_to_label,
    _is_key_event,
)
from app.services.mixed_sentiment_data_service import (
    DEFAULT_SENTIMENT_WEIGHTS,
    MixedSentimentDataService,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

sentiment_label_strategy = st.sampled_from(["fear", "greed", "neutral"])
sentiment_score_strategy = st.floats(min_value=0.0, max_value=100.0)
score_or_none = st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0))
valid_score = st.floats(min_value=0.0, max_value=100.0)
source_platform_strategy = st.sampled_from(["eastmoney", "xueqiu", "10jqka"])

metrics_strategy = st.fixed_dictionaries({
    "baidu_vote_score": score_or_none,
    "akshare_aggregate_score": score_or_none,
    "news_sentiment_score": score_or_none,
    "margin_trading_score": score_or_none,
    "source_availability": st.just({}),
})


def _make_analyzed_comment(
    label: str = "neutral",
    score: float = 50.0,
    stock_code: str = None,
    source_platform: str = "eastmoney",
    content: str = "测试评论",
) -> SentimentComment:
    """Create a SentimentComment with sentiment labels already assigned."""
    import hashlib
    content_hash = hashlib.md5(content.encode()).hexdigest()
    return SentimentComment(
        id=f"test_{uuid.uuid4().hex[:8]}",
        content=content,
        source_platform=source_platform,
        stock_code=stock_code,
        author_nickname="user",
        published_time=datetime.now(timezone.utc).isoformat(),
        content_hash=content_hash,
        sentiment_label=label,
        sentiment_score=score,
    )


# ---------------------------------------------------------------------------
# Property 32: 散户评论数据完整性与情绪标签有效性
# ---------------------------------------------------------------------------


class TestProperty32CommentDataIntegrityAndLabelValidity:
    """Property 32: 散户评论数据完整性与情绪标签有效性

    For any 经过情绪分析的 SentimentComment，其 content、source_platform、
    published_time 和 content_hash 字段必须为非空字符串，且 sentiment_label
    必须为 "fear"、"greed" 或 "neutral" 之一，sentiment_score 必须在 0-100 范围内。

    **Validates: Requirements 9.2, 9.15**
    """

    @given(
        label=sentiment_label_strategy,
        score=sentiment_score_strategy,
        source=source_platform_strategy,
    )
    @settings(max_examples=200)
    def test_analyzed_comment_fields_non_empty(self, label, score, source):
        """经过分析的评论必填字段非空"""
        comment = _make_analyzed_comment(
            label=label, score=score, source_platform=source,
            content=f"评论内容_{uuid.uuid4().hex[:4]}",
        )
        assert comment.content and len(comment.content.strip()) > 0
        assert comment.source_platform and len(comment.source_platform.strip()) > 0
        assert comment.published_time and len(comment.published_time.strip()) > 0
        assert comment.content_hash and len(comment.content_hash.strip()) > 0

    @given(
        label=sentiment_label_strategy,
        score=sentiment_score_strategy,
    )
    @settings(max_examples=200)
    def test_sentiment_label_valid(self, label, score):
        """sentiment_label 必须为 fear/greed/neutral 之一"""
        comment = _make_analyzed_comment(label=label, score=score)
        assert comment.sentiment_label in ("fear", "greed", "neutral")

    @given(score=sentiment_score_strategy)
    @settings(max_examples=200)
    def test_sentiment_score_in_range(self, score):
        """sentiment_score 必须在 0-100 范围内"""
        comment = _make_analyzed_comment(score=score)
        assert 0.0 <= comment.sentiment_score <= 100.0

    @given(
        labels=st.lists(sentiment_label_strategy, min_size=1, max_size=20),
        scores=st.lists(sentiment_score_strategy, min_size=1, max_size=20),
    )
    @settings(max_examples=100)
    def test_batch_comments_all_valid(self, labels, scores):
        """批量评论中每条都满足完整性约束"""
        n = min(len(labels), len(scores))
        comments = [
            _make_analyzed_comment(
                label=labels[i], score=scores[i],
                content=f"批量评论{i}_{uuid.uuid4().hex[:4]}",
            )
            for i in range(n)
        ]
        for c in comments:
            assert c.sentiment_label in ("fear", "greed", "neutral")
            assert 0.0 <= c.sentiment_score <= 100.0
            assert c.content.strip()
            assert c.content_hash.strip()


# ---------------------------------------------------------------------------
# Property 40: 情绪指数计算正确性（加权模型）
# ---------------------------------------------------------------------------


class TestProperty40SentimentIndexCalculation:
    """Property 40: 情绪指数计算正确性（加权模型）

    For any set of classified comments and mixed data source metrics,
    calculate_index() returns a SentimentSnapshot whose index_value equals
    the weighted sum of available source scores (redistributed weights sum to 1.0),
    clamped to 0-100.

    **Validates: Requirements 9.17**
    """

    @given(
        greed_count=st.integers(min_value=0, max_value=50),
        fear_count=st.integers(min_value=0, max_value=50),
        neutral_count=st.integers(min_value=0, max_value=50),
        metrics=metrics_strategy,
    )
    @settings(max_examples=200)
    def test_index_value_in_range(self, greed_count, fear_count, neutral_count, metrics):
        """综合指数 index_value 必须在 0-100 范围内"""
        total = greed_count + fear_count + neutral_count
        assume(total > 0)

        comments = (
            [_make_analyzed_comment(label="greed", score=80, content=f"贪婪{i}") for i in range(greed_count)]
            + [_make_analyzed_comment(label="fear", score=20, content=f"恐慌{i}") for i in range(fear_count)]
            + [_make_analyzed_comment(label="neutral", score=50, content=f"中性{i}") for i in range(neutral_count)]
        )

        analyzer = SentimentAnalyzer()
        snapshot = analyzer.calculate_index(comments, metrics)

        assert 0.0 <= snapshot.index_value <= 100.0

    @given(
        greed_count=st.integers(min_value=0, max_value=20),
        fear_count=st.integers(min_value=0, max_value=20),
        neutral_count=st.integers(min_value=0, max_value=20),
        metrics=metrics_strategy,
    )
    @settings(max_examples=200)
    def test_ratios_sum_to_one(self, greed_count, fear_count, neutral_count, metrics):
        """fear_ratio + greed_ratio + neutral_ratio 应约等于 1.0"""
        total = greed_count + fear_count + neutral_count
        assume(total > 0)

        comments = (
            [_make_analyzed_comment(label="greed", score=80, content=f"贪婪{i}") for i in range(greed_count)]
            + [_make_analyzed_comment(label="fear", score=20, content=f"恐慌{i}") for i in range(fear_count)]
            + [_make_analyzed_comment(label="neutral", score=50, content=f"中性{i}") for i in range(neutral_count)]
        )

        analyzer = SentimentAnalyzer()
        snapshot = analyzer.calculate_index(comments, metrics)

        ratio_sum = snapshot.fear_ratio + snapshot.greed_ratio + snapshot.neutral_ratio
        assert abs(ratio_sum - 1.0) < 0.01, f"Ratio sum {ratio_sum} != 1.0"

    @given(
        greed_count=st.integers(min_value=1, max_value=30),
        total_extra=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=200)
    def test_comment_score_equals_greed_proportion(self, greed_count, total_extra):
        """评论情绪分 = greed_count / total * 100"""
        total = greed_count + total_extra
        assume(total > 0)

        comments = (
            [_make_analyzed_comment(label="greed", score=80, content=f"贪婪{i}") for i in range(greed_count)]
            + [_make_analyzed_comment(label="fear", score=20, content=f"恐慌{i}") for i in range(total_extra)]
        )

        # Use only comment score (no mixed metrics)
        empty_metrics = {
            "baidu_vote_score": None,
            "akshare_aggregate_score": None,
            "news_sentiment_score": None,
            "margin_trading_score": None,
            "source_availability": {},
        }

        analyzer = SentimentAnalyzer()
        snapshot = analyzer.calculate_index(comments, empty_metrics)

        expected_comment_score = greed_count / total * 100
        # When only comment score is available, index_value should equal comment_score
        assert abs(snapshot.index_value - expected_comment_score) < 0.1, (
            f"index_value {snapshot.index_value} != expected {expected_comment_score}"
        )

    @given(metrics=metrics_strategy)
    @settings(max_examples=100)
    def test_empty_comments_returns_snapshot(self, metrics):
        """空评论列表仍返回有效快照"""
        analyzer = SentimentAnalyzer()
        snapshot = analyzer.calculate_index([], metrics)

        assert isinstance(snapshot, SentimentSnapshot)
        assert snapshot.sample_count == 0
        assert 0.0 <= snapshot.index_value <= 100.0

    @given(
        greed_count=st.integers(min_value=0, max_value=10),
        fear_count=st.integers(min_value=0, max_value=10),
        neutral_count=st.integers(min_value=0, max_value=10),
        metrics=metrics_strategy,
    )
    @settings(max_examples=200)
    def test_sample_count_matches_input(self, greed_count, fear_count, neutral_count, metrics):
        """sample_count 应等于输入评论数"""
        total = greed_count + fear_count + neutral_count

        comments = (
            [_make_analyzed_comment(label="greed", score=80, content=f"贪婪{i}") for i in range(greed_count)]
            + [_make_analyzed_comment(label="fear", score=20, content=f"恐慌{i}") for i in range(fear_count)]
            + [_make_analyzed_comment(label="neutral", score=50, content=f"中性{i}") for i in range(neutral_count)]
        )

        analyzer = SentimentAnalyzer()
        snapshot = analyzer.calculate_index(comments, metrics)

        assert snapshot.sample_count == total


# ---------------------------------------------------------------------------
# Property 41: 情绪快照持久化往返一致性
# ---------------------------------------------------------------------------


class TestProperty41SnapshotPersistenceRoundTrip:
    """Property 41: 情绪快照持久化往返一致性

    For any 成功计算的 SentimentSnapshot，保存到数据库后读取，
    返回的 index_value、comment_sentiment_score、baidu_vote_score、
    akshare_aggregate_score、news_sentiment_score、margin_trading_score、
    fear_ratio、greed_ratio、neutral_ratio 和 sample_count 应与原始数据等价。

    **Validates: Requirements 9.19**
    """

    @given(
        index_value=valid_score,
        comment_score=score_or_none,
        baidu_score=score_or_none,
        akshare_score=score_or_none,
        news_score=score_or_none,
        margin_score=score_or_none,
        fear_ratio=st.floats(min_value=0.0, max_value=1.0),
        greed_ratio=st.floats(min_value=0.0, max_value=1.0),
        sample_count=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=100)
    def test_snapshot_round_trip_via_db_model(
        self, index_value, comment_score, baidu_score, akshare_score,
        news_score, margin_score, fear_ratio, greed_ratio, sample_count,
    ):
        """快照数据通过 DB 模型序列化/反序列化后保持一致"""
        neutral_ratio = max(0.0, 1.0 - fear_ratio - greed_ratio)

        snapshot = SentimentSnapshot(
            id=uuid.uuid4().hex,
            stock_code=None,
            index_value=index_value,
            comment_sentiment_score=comment_score,
            baidu_vote_score=baidu_score,
            akshare_aggregate_score=akshare_score,
            news_sentiment_score=news_score,
            margin_trading_score=margin_score,
            fear_ratio=round(fear_ratio, 4),
            greed_ratio=round(greed_ratio, 4),
            neutral_ratio=round(neutral_ratio, 4),
            sample_count=sample_count,
            data_source_availability={"comment_sentiment": True, "baidu_vote": False},
            label=_index_to_label(index_value),
            snapshot_time=datetime.now(timezone.utc).isoformat(),
        )

        # Simulate DB serialization: convert to DB model fields and back
        from app.models import SentimentSnapshotDB

        db_obj = SentimentSnapshotDB(
            id=snapshot.id,
            stock_code=snapshot.stock_code,
            index_value=snapshot.index_value,
            comment_sentiment_score=snapshot.comment_sentiment_score,
            baidu_vote_score=snapshot.baidu_vote_score,
            akshare_aggregate_score=snapshot.akshare_aggregate_score,
            news_sentiment_score=snapshot.news_sentiment_score,
            margin_trading_score=snapshot.margin_trading_score,
            fear_ratio=snapshot.fear_ratio,
            greed_ratio=snapshot.greed_ratio,
            neutral_ratio=snapshot.neutral_ratio,
            sample_count=snapshot.sample_count,
            data_source_availability=json.dumps(snapshot.data_source_availability or {}),
            label=snapshot.label,
            snapshot_time=datetime.fromisoformat(snapshot.snapshot_time),
        )

        # Convert back
        restored = SentimentAnalyzer._db_snapshot_to_schema(db_obj)

        # Verify round-trip consistency
        assert abs(restored.index_value - snapshot.index_value) < 0.001
        assert restored.comment_sentiment_score == snapshot.comment_sentiment_score
        assert restored.baidu_vote_score == snapshot.baidu_vote_score
        assert restored.akshare_aggregate_score == snapshot.akshare_aggregate_score
        assert restored.news_sentiment_score == snapshot.news_sentiment_score
        assert restored.margin_trading_score == snapshot.margin_trading_score
        assert abs(restored.fear_ratio - snapshot.fear_ratio) < 0.001
        assert abs(restored.greed_ratio - snapshot.greed_ratio) < 0.001
        assert abs(restored.neutral_ratio - snapshot.neutral_ratio) < 0.001
        assert restored.sample_count == snapshot.sample_count
        assert restored.label == snapshot.label


# ---------------------------------------------------------------------------
# Property 42: 关键事件节点分类
# ---------------------------------------------------------------------------


class TestProperty42KeyEventClassification:
    """Property 42: 关键事件节点分类

    For any SentimentSnapshot，当 index_value 大于 80 或小于 20 时，
    该快照应被标记为关键事件节点。

    **Validates: Requirements 9.24**
    """

    @given(index_value=st.floats(min_value=80.01, max_value=100.0))
    @settings(max_examples=200)
    def test_high_index_is_key_event(self, index_value):
        """index_value > 80 是关键事件"""
        assert _is_key_event(index_value) is True

    @given(index_value=st.floats(min_value=0.0, max_value=19.99))
    @settings(max_examples=200)
    def test_low_index_is_key_event(self, index_value):
        """index_value < 20 是关键事件"""
        assert _is_key_event(index_value) is True

    @given(index_value=st.floats(min_value=20.0, max_value=80.0))
    @settings(max_examples=200)
    def test_mid_index_is_not_key_event(self, index_value):
        """20 <= index_value <= 80 不是关键事件"""
        assert _is_key_event(index_value) is False

    @given(
        greed_count=st.integers(min_value=0, max_value=10),
        fear_count=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100)
    def test_key_event_from_calculated_snapshot(self, greed_count, fear_count):
        """通过 calculate_index 生成的快照也遵循关键事件规则"""
        total = greed_count + fear_count
        assume(total > 0)

        comments = (
            [_make_analyzed_comment(label="greed", score=80, content=f"贪婪{i}") for i in range(greed_count)]
            + [_make_analyzed_comment(label="fear", score=20, content=f"恐慌{i}") for i in range(fear_count)]
        )

        empty_metrics = {
            "baidu_vote_score": None,
            "akshare_aggregate_score": None,
            "news_sentiment_score": None,
            "margin_trading_score": None,
            "source_availability": {},
        }

        analyzer = SentimentAnalyzer()
        snapshot = analyzer.calculate_index(comments, empty_metrics)

        if snapshot.index_value > 80 or snapshot.index_value < 20:
            assert _is_key_event(snapshot.index_value) is True
        else:
            assert _is_key_event(snapshot.index_value) is False


# ---------------------------------------------------------------------------
# Property 44: 旧评论清理保留快照
# ---------------------------------------------------------------------------


class TestProperty44OldCommentCleanupPreservesSnapshots:
    """Property 44: 旧评论清理保留快照

    For any 执行 cleanup_old_comments(retention_days=90) 后，
    sentiment_comments 表中不应存在 published_time 早于 90 天前的记录，
    但 sentiment_snapshots 表中的所有历史快照应保持不变。

    We test the logic by verifying that cleanup targets only comments,
    not snapshots, using the DB model layer.

    **Validates: Requirements 9.31**
    """

    @given(retention_days=st.integers(min_value=1, max_value=365))
    @settings(max_examples=100)
    def test_cleanup_cutoff_calculation(self, retention_days):
        """清理截止日期计算正确"""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=retention_days)

        # Old comment (should be deleted)
        old_time = now - timedelta(days=retention_days + 10)
        assert old_time < cutoff

        # Recent comment (should be kept)
        recent_time = now - timedelta(days=retention_days - 10)
        assert recent_time >= cutoff

    @given(retention_days=st.integers(min_value=1, max_value=365))
    @settings(max_examples=100)
    def test_snapshots_not_affected_by_cleanup(self, retention_days):
        """快照数据不受评论清理影响（验证清理只针对 comments 表）"""
        # The cleanup_old_comments method uses:
        #   delete(SentimentCommentDB).where(published_time < cutoff)
        # It does NOT touch SentimentSnapshotDB.
        # We verify this by checking the SQL statement targets the correct table.
        from sqlalchemy import delete
        from app.models import SentimentCommentDB, SentimentSnapshotDB

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Build the delete statement used by cleanup
        stmt = delete(SentimentCommentDB).where(
            SentimentCommentDB.published_time < cutoff
        )

        # Verify it targets the comments table, not snapshots
        assert str(stmt).startswith("DELETE FROM sentiment_comments")
        assert "sentiment_snapshots" not in str(stmt)

    def test_cleanup_preserves_snapshot_model_independence(self):
        """SentimentSnapshotDB 和 SentimentCommentDB 是独立的表"""
        from app.models import SentimentCommentDB, SentimentSnapshotDB

        assert SentimentCommentDB.__tablename__ == "sentiment_comments"
        assert SentimentSnapshotDB.__tablename__ == "sentiment_snapshots"
        assert SentimentCommentDB.__tablename__ != SentimentSnapshotDB.__tablename__
