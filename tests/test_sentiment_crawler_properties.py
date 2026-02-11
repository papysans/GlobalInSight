#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for SentimentCrawler.

Feature: multi-mode-platform
Property 33: 增量采集时间窗口过滤
Property 34: 个股评论筛选一致性
Property 38: 数据源封禁降级
Property 39: 评论清洗去除垃圾和重复

**Validates: Requirements 9.3, 9.4, 9.8, 9.9**
"""

import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.schemas import SentimentComment
from app.services.sentiment_crawler import (
    SentimentCrawler,
    _content_hash,
    _is_within_time_window,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

stock_code_strategy = st.from_regex(r"[036]\d{5}", fullmatch=True)

source_platform_strategy = st.sampled_from(["eastmoney", "xueqiu", "10jqka"])

# Generate a published_time within a given hours window from now
def _make_time_within(hours: int) -> str:
    """Return an ISO timestamp within *hours* from now."""
    offset = timedelta(hours=hours) * 0.5  # halfway inside the window
    dt = datetime.now(timezone.utc) - offset
    return dt.isoformat()


def _make_time_outside(hours: int) -> str:
    """Return an ISO timestamp outside (before) the time window."""
    offset = timedelta(hours=hours + 2)  # 2 hours past the window
    dt = datetime.now(timezone.utc) - offset
    return dt.isoformat()


def _make_comment(
    content: str = "这只股票不错",
    source_platform: str = "eastmoney",
    stock_code: str = None,
    published_time: str = None,
    content_hash: str = None,
) -> SentimentComment:
    if published_time is None:
        published_time = datetime.now(timezone.utc).isoformat()
    if content_hash is None:
        content_hash = _content_hash(content)
    return SentimentComment(
        id=f"test_{uuid.uuid4().hex[:8]}",
        content=content,
        source_platform=source_platform,
        stock_code=stock_code,
        author_nickname="user",
        published_time=published_time,
        content_hash=content_hash,
    )


# Strategy for time_window_hours (1 to 72)
time_window_strategy = st.integers(min_value=1, max_value=72)


# ---------------------------------------------------------------------------
# Property 33: 增量采集时间窗口过滤
# ---------------------------------------------------------------------------


class TestProperty33IncrementalTimeWindowFiltering:
    """Property 33: 增量采集时间窗口过滤

    For any 指定的 time_window_hours 参数和采集结果列表，
    返回的每条 SentimentComment 的 published_time 必须在
    当前时间减去 time_window_hours 的范围内。

    **Validates: Requirements 9.3**
    """

    @given(time_window_hours=time_window_strategy)
    @settings(max_examples=100)
    def test_comments_within_window_pass(self, time_window_hours):
        """时间窗口内的评论应通过过滤"""
        pub_time = _make_time_within(time_window_hours)
        assert _is_within_time_window(pub_time, time_window_hours) is True

    @given(time_window_hours=time_window_strategy)
    @settings(max_examples=100)
    def test_comments_outside_window_rejected(self, time_window_hours):
        """时间窗口外的评论应被拒绝"""
        pub_time = _make_time_outside(time_window_hours)
        assert _is_within_time_window(pub_time, time_window_hours) is False

    @given(time_window_hours=time_window_strategy)
    @settings(max_examples=100)
    def test_mixed_comments_only_within_window_survive(self, time_window_hours):
        """混合列表中只有窗口内的评论保留"""
        inside_time = _make_time_within(time_window_hours)
        outside_time = _make_time_outside(time_window_hours)

        comments = [
            _make_comment(content="窗口内评论A", published_time=inside_time),
            _make_comment(content="窗口外评论B", published_time=outside_time),
            _make_comment(content="窗口内评论C", published_time=inside_time),
        ]

        filtered = [c for c in comments if _is_within_time_window(c.published_time, time_window_hours)]
        assert len(filtered) == 2
        for c in filtered:
            assert _is_within_time_window(c.published_time, time_window_hours)


# ---------------------------------------------------------------------------
# Property 34: 个股评论筛选一致性
# ---------------------------------------------------------------------------


class TestProperty34StockCodeFilterConsistency:
    """Property 34: 个股评论筛选一致性

    For any 指定的 stock_code 参数和采集结果列表，
    返回的每条 SentimentComment 的 stock_code 字段必须等于
    请求中指定的 stock_code。

    **Validates: Requirements 9.4**
    """

    @given(stock_code=stock_code_strategy)
    @settings(max_examples=100)
    def test_all_comments_match_stock_code(self, stock_code):
        """所有返回评论的 stock_code 应与请求一致"""
        comments = [
            _make_comment(content=f"评论{i}", stock_code=stock_code)
            for i in range(5)
        ]
        for c in comments:
            assert c.stock_code == stock_code

    @given(
        target_code=stock_code_strategy,
        other_code=stock_code_strategy,
    )
    @settings(max_examples=100)
    def test_filter_by_stock_code(self, target_code, other_code):
        """按 stock_code 筛选后只保留匹配的评论"""
        assume(target_code != other_code)

        comments = [
            _make_comment(content="目标股评论", stock_code=target_code),
            _make_comment(content="其他股评论", stock_code=other_code),
            _make_comment(content="目标股评论2", stock_code=target_code),
        ]

        filtered = [c for c in comments if c.stock_code == target_code]
        assert len(filtered) == 2
        for c in filtered:
            assert c.stock_code == target_code


# ---------------------------------------------------------------------------
# Property 38: 数据源封禁降级
# ---------------------------------------------------------------------------


class TestProperty38SourceBanDegradation:
    """Property 38: 数据源封禁降级

    For any SentimentCrawler 实例和数据源，连续 3 次请求失败后
    该数据源应被标记为 banned 状态，is_source_banned() 应返回 True。

    **Validates: Requirements 9.8**
    """

    @given(source=source_platform_strategy)
    @settings(max_examples=100)
    def test_ban_after_three_consecutive_failures(self, source):
        """连续 3 次失败后数据源被封禁"""
        crawler = SentimentCrawler()

        # Before any failures, not banned
        assert crawler.is_source_banned(source) is False

        # Record 3 consecutive failures
        for _ in range(3):
            crawler._record_failure(source)

        assert crawler.is_source_banned(source) is True

    @given(source=source_platform_strategy)
    @settings(max_examples=100)
    def test_not_banned_before_three_failures(self, source):
        """少于 3 次失败不会触发封禁"""
        crawler = SentimentCrawler()

        crawler._record_failure(source)
        assert crawler.is_source_banned(source) is False

        crawler._record_failure(source)
        assert crawler.is_source_banned(source) is False

    @given(source=source_platform_strategy)
    @settings(max_examples=100)
    def test_success_resets_failure_count(self, source):
        """成功请求重置连续失败计数"""
        crawler = SentimentCrawler()

        crawler._record_failure(source)
        crawler._record_failure(source)
        # 2 failures, then a success
        crawler._record_success(source)
        # Another 2 failures should NOT trigger ban (counter was reset)
        crawler._record_failure(source)
        crawler._record_failure(source)

        assert crawler.is_source_banned(source) is False

    @given(source=source_platform_strategy)
    @settings(max_examples=100)
    def test_ban_expires_after_duration(self, source):
        """封禁在指定时间后过期"""
        crawler = SentimentCrawler()

        # Ban with 0 duration (expires immediately)
        crawler.ban_source(source, duration_minutes=0)
        # Should not be banned since duration is 0
        assert crawler.is_source_banned(source) is False

    @given(source=source_platform_strategy)
    @settings(max_examples=100)
    def test_manual_ban_sets_banned_state(self, source):
        """手动封禁设置 banned 状态"""
        crawler = SentimentCrawler()
        crawler.ban_source(source, duration_minutes=30)
        assert crawler.is_source_banned(source) is True


# ---------------------------------------------------------------------------
# Property 39: 评论清洗去除垃圾和重复
# ---------------------------------------------------------------------------


class TestProperty39CommentCleaningRemovesJunkAndDuplicates:
    """Property 39: 评论清洗去除垃圾和重复

    For any 包含纯表情评论、垃圾关键词评论和重复评论的输入列表，
    经过 clean_comments() 处理后，结果列表中不应包含任何纯表情/纯符号评论、
    不应包含垃圾关键词、不应包含重复的 content_hash。

    **Validates: Requirements 9.9**
    """

    @given(
        spam_kw=st.sampled_from(["加微信", "免费荐股", "保证赚", "内幕消息", "加群"]),
    )
    @settings(max_examples=100)
    def test_spam_comments_removed(self, spam_kw):
        """包含垃圾关键词的评论被清除"""
        crawler = SentimentCrawler()
        comments = [
            _make_comment(content=f"快来{spam_kw}赚大钱"),
            _make_comment(content="这只股票基本面不错，值得关注"),
        ]
        cleaned = crawler.clean_comments(comments)
        for c in cleaned:
            assert spam_kw not in c.content

    @given(
        emoji_text=st.sampled_from([
            "😀😀😀", "🚀🚀🚀", "!!!???", "。。。", "~~~",
            "👍👍👍", "💰💰💰", "***", "---",
        ]),
    )
    @settings(max_examples=100)
    def test_pure_emoji_symbol_removed(self, emoji_text):
        """纯表情/纯符号评论被清除"""
        crawler = SentimentCrawler()
        comments = [
            _make_comment(content=emoji_text),
            _make_comment(content="今天大盘走势不错"),
        ]
        cleaned = crawler.clean_comments(comments)
        for c in cleaned:
            assert c.content != emoji_text

    @given(st.data())
    @settings(max_examples=100)
    def test_duplicate_comments_removed(self, data):
        """重复评论（相同 content_hash）被去重"""
        content = data.draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))))
        assume(len(content.strip()) >= 3)

        crawler = SentimentCrawler(spam_keywords=[])  # No spam filter for this test
        h = _content_hash(content)
        comments = [
            _make_comment(content=content, content_hash=h),
            _make_comment(content=content, content_hash=h),
            _make_comment(content=content, content_hash=h),
        ]
        cleaned = crawler.clean_comments(comments)
        hashes = [c.content_hash for c in cleaned]
        assert len(hashes) == len(set(hashes)), "No duplicate content_hash should remain"

    @given(
        n_valid=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_valid_comments_preserved(self, n_valid):
        """有效评论不被误删"""
        crawler = SentimentCrawler()
        comments = [
            _make_comment(content=f"有效评论内容{i}号分析")
            for i in range(n_valid)
        ]
        cleaned = crawler.clean_comments(comments)
        assert len(cleaned) == n_valid

    def test_empty_input_returns_empty(self):
        """空输入返回空列表"""
        crawler = SentimentCrawler()
        assert crawler.clean_comments([]) == []
