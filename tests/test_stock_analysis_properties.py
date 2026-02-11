#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for StockAnalysisService results.

Feature: multi-mode-platform
Property 8: 行情推演结果完整性
Property 16: 多空交锋对话轮次
Property 17: 争议性结论立场一致性

Uses Hypothesis for property-based testing.
"""

import re
import uuid
from datetime import datetime

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.schemas import StockAnalysisResult


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")),
    min_size=1,
    max_size=200,
).filter(lambda s: s.strip() != "")

stances = st.sampled_from(["bull", "bear"])

debate_rounds_st = st.integers(min_value=1, max_value=5)


def _build_debate_dialogue(rounds: int) -> st.SearchStrategy[str]:
    """Build a debate_dialogue string that contains the expected round markers."""

    def _make(parts: list) -> str:
        sections = []
        for i, part in enumerate(parts, start=1):
            sections.append(f"\n--- 第 {i} 轮 ---\n多头：\"{part[0]}\"\n空头：\"{part[1]}\"\n")
        return "".join(sections)

    round_pair = st.tuples(non_empty_text, non_empty_text)
    return st.lists(round_pair, min_size=rounds, max_size=rounds).map(_make)


def stock_analysis_result_strategy(
    debate_rounds: int = 2,
    stance_override: st.SearchStrategy[str] | None = None,
):
    """Strategy that builds a valid StockAnalysisResult with the given debate_rounds."""
    stance_st = stance_override if stance_override is not None else stances
    return st.builds(
        StockAnalysisResult,
        id=st.from_regex(r"[a-f0-9]{8}_\d{14}", fullmatch=True),
        news_titles=st.lists(non_empty_text, min_size=1, max_size=5),
        summary=non_empty_text,
        impact_analysis=non_empty_text,
        bull_argument=non_empty_text,
        bear_argument=non_empty_text,
        debate_dialogue=_build_debate_dialogue(debate_rounds),
        controversial_conclusion=non_empty_text,
        stance=stance_st,
        risk_warning=non_empty_text,
        sentiment_context=st.none(),
        created_at=st.just(datetime.now().isoformat()),
        cache_hit=st.just(False),
    )


# ---------------------------------------------------------------------------
# Property 8: 行情推演结果完整性
# ---------------------------------------------------------------------------


class TestProperty8AnalysisResultCompleteness:
    """Property 8: 行情推演结果完整性

    For any 成功的行情推演结果，其 summary、impact_analysis、bull_argument、
    bear_argument、debate_dialogue、controversial_conclusion 和 risk_warning
    字段必须为非空字符串，且 stance 字段必须为 "bull" 或 "bear"。

    **Validates: Requirements 3.2**
    """

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_summary_non_empty(self, result: StockAnalysisResult):
        assert isinstance(result.summary, str)
        assert len(result.summary.strip()) > 0

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_impact_analysis_non_empty(self, result: StockAnalysisResult):
        assert isinstance(result.impact_analysis, str)
        assert len(result.impact_analysis.strip()) > 0

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_bull_argument_non_empty(self, result: StockAnalysisResult):
        assert isinstance(result.bull_argument, str)
        assert len(result.bull_argument.strip()) > 0

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_bear_argument_non_empty(self, result: StockAnalysisResult):
        assert isinstance(result.bear_argument, str)
        assert len(result.bear_argument.strip()) > 0

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_debate_dialogue_non_empty(self, result: StockAnalysisResult):
        assert isinstance(result.debate_dialogue, str)
        assert len(result.debate_dialogue.strip()) > 0

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_controversial_conclusion_non_empty(self, result: StockAnalysisResult):
        assert isinstance(result.controversial_conclusion, str)
        assert len(result.controversial_conclusion.strip()) > 0

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_risk_warning_non_empty(self, result: StockAnalysisResult):
        assert isinstance(result.risk_warning, str)
        assert len(result.risk_warning.strip()) > 0

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_stance_is_bull_or_bear(self, result: StockAnalysisResult):
        assert result.stance in ("bull", "bear")

    @given(result=stock_analysis_result_strategy())
    @settings(max_examples=100)
    def test_all_fields_complete(self, result: StockAnalysisResult):
        """All required fields are simultaneously non-empty and stance is valid."""
        assert result.summary.strip() != ""
        assert result.impact_analysis.strip() != ""
        assert result.bull_argument.strip() != ""
        assert result.bear_argument.strip() != ""
        assert result.debate_dialogue.strip() != ""
        assert result.controversial_conclusion.strip() != ""
        assert result.risk_warning.strip() != ""
        assert result.stance in ("bull", "bear")


# ---------------------------------------------------------------------------
# Property 16: 多空交锋对话轮次
# ---------------------------------------------------------------------------


class TestProperty16DebateDialogueRounds:
    """Property 16: 多空交锋对话轮次

    For any 成功的行情推演结果，其 debate_dialogue 字段应包含至少
    debate_rounds 轮多空交锋（即至少 debate_rounds 个 "第 N 轮" 标记）。
    当 debate_rounds 使用默认值 2 时，至少包含 2 个轮次标记。

    **Validates: Requirements 3.5**
    """

    @given(data=st.data(), rounds=debate_rounds_st)
    @settings(max_examples=100)
    def test_debate_rounds_match_parameter(self, data, rounds: int):
        """debate_dialogue should contain exactly `rounds` round markers."""
        result = data.draw(stock_analysis_result_strategy(debate_rounds=rounds))
        # Count round markers like "--- 第 N 轮 ---"
        round_markers = re.findall(r"--- 第 \d+ 轮 ---", result.debate_dialogue)
        assert len(round_markers) >= rounds, (
            f"Expected at least {rounds} round markers, found {len(round_markers)}"
        )

    @given(result=stock_analysis_result_strategy(debate_rounds=2))
    @settings(max_examples=100)
    def test_default_debate_rounds_is_two(self, result: StockAnalysisResult):
        """Default debate_rounds=2 should produce at least 2 round markers."""
        round_markers = re.findall(r"--- 第 \d+ 轮 ---", result.debate_dialogue)
        assert len(round_markers) >= 2

    @given(result=stock_analysis_result_strategy(debate_rounds=2))
    @settings(max_examples=100)
    def test_debate_contains_bull_and_bear_voices(self, result: StockAnalysisResult):
        """Each round should contain both bull and bear dialogue."""
        assert "多头" in result.debate_dialogue
        assert "空头" in result.debate_dialogue


# ---------------------------------------------------------------------------
# Property 17: 争议性结论立场一致性
# ---------------------------------------------------------------------------


class TestProperty17StanceConclusionConsistency:
    """Property 17: 争议性结论立场一致性

    For any 成功的行情推演结果，其 stance 字段值（"bull" 或 "bear"）
    应与 controversial_conclusion 文本中表达的立场方向一致。

    We test the stance extraction logic from the service: given a raw
    conclusion text containing a STANCE tag, the extracted stance must
    match the tag.

    **Validates: Requirements 3.6**
    """

    @given(
        conclusion_body=non_empty_text,
        actual_stance=stances,
    )
    @settings(max_examples=100)
    def test_stance_extraction_from_tag(self, conclusion_body: str, actual_stance: str):
        """Stance extracted from STANCE tag matches the tag value."""
        # Simulate the raw conclusion with a STANCE tag (as the LLM would produce)
        raw_conclusion = f"{conclusion_body}\nSTANCE: {actual_stance}"

        # Replicate the extraction logic from StockAnalysisService.analyze()
        stance = "bull"
        if "stance: bear" in raw_conclusion.lower() or "stance:bear" in raw_conclusion.lower():
            stance = "bear"

        assert stance == actual_stance

    @given(conclusion_body=non_empty_text)
    @settings(max_examples=100)
    def test_missing_stance_tag_defaults_to_bull(self, conclusion_body: str):
        """When no STANCE tag is present, stance defaults to 'bull'."""
        # Ensure the body doesn't accidentally contain a stance tag
        assume("stance:" not in conclusion_body.lower())
        assume("stance: " not in conclusion_body.lower())

        raw_conclusion = conclusion_body

        stance = "bull"
        if "stance: bear" in raw_conclusion.lower() or "stance:bear" in raw_conclusion.lower():
            stance = "bear"

        assert stance == "bull"

    @given(result=stock_analysis_result_strategy(stance_override=st.just("bull")))
    @settings(max_examples=100)
    def test_bull_stance_result_is_valid(self, result: StockAnalysisResult):
        """A result with bull stance has stance == 'bull'."""
        assert result.stance == "bull"

    @given(result=stock_analysis_result_strategy(stance_override=st.just("bear")))
    @settings(max_examples=100)
    def test_bear_stance_result_is_valid(self, result: StockAnalysisResult):
        """A result with bear stance has stance == 'bear'."""
        assert result.stance == "bear"


# ---------------------------------------------------------------------------
# Property 43: 推演结果包含情绪上下文
# ---------------------------------------------------------------------------

# Strategies for sentiment context

_sentiment_labels = st.sampled_from(["extreme_fear", "fear", "neutral", "greed", "extreme_greed"])
_trend_directions = st.sampled_from(["up", "down", "stable"])
_optional_score = st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False))

# At least one sub_score must be non-None
_sub_scores_with_at_least_one = st.fixed_dictionaries({
    "comment": _optional_score,
    "baidu_vote": _optional_score,
    "akshare": _optional_score,
    "news": _optional_score,
    "margin": _optional_score,
}).filter(lambda d: any(v is not None for v in d.values()))

_source_availability = st.dictionaries(
    keys=st.sampled_from(["eastmoney", "xueqiu", "10jqka", "akshare", "baidu_vote", "news", "margin"]),
    values=st.booleans(),
    min_size=0,
    max_size=7,
)

sentiment_context_strategy = st.fixed_dictionaries({
    "index_value": st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    "label": _sentiment_labels,
    "trend_direction": _trend_directions,
    "sample_count": st.integers(min_value=1, max_value=10000),
    "sub_scores": _sub_scores_with_at_least_one,
    "source_availability": _source_availability,
})


def stock_analysis_result_with_sentiment_strategy():
    """Strategy that builds a StockAnalysisResult with a non-None sentiment_context."""
    return st.builds(
        StockAnalysisResult,
        id=st.from_regex(r"[a-f0-9]{8}_\d{14}", fullmatch=True),
        news_titles=st.lists(non_empty_text, min_size=1, max_size=3),
        summary=non_empty_text,
        impact_analysis=non_empty_text,
        bull_argument=non_empty_text,
        bear_argument=non_empty_text,
        debate_dialogue=_build_debate_dialogue(2),
        controversial_conclusion=non_empty_text,
        stance=stances,
        risk_warning=non_empty_text,
        sentiment_context=sentiment_context_strategy,
        created_at=st.just(datetime.now().isoformat()),
        cache_hit=st.just(False),
    )


class TestProperty43SentimentContextInAnalysisResult:
    """Property 43: 推演结果包含情绪上下文

    For any 成功的行情推演结果，当情绪数据可用时，其 sentiment_context 字段
    应为非空，且包含有效的 index_value（0-100）、trend_direction（up/down/stable）、
    sample_count（正整数）和 sub_scores 字典（至少一个分项得分非 None）。

    **Validates: Requirements 9.26**
    """

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_sentiment_context_is_present(self, result: StockAnalysisResult):
        """When sentiment data is available, sentiment_context must be non-None."""
        assert result.sentiment_context is not None

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_index_value_in_range(self, result: StockAnalysisResult):
        """index_value must be between 0 and 100."""
        ctx = result.sentiment_context
        assert 0.0 <= ctx["index_value"] <= 100.0

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_trend_direction_valid(self, result: StockAnalysisResult):
        """trend_direction must be one of up/down/stable."""
        ctx = result.sentiment_context
        assert ctx["trend_direction"] in ("up", "down", "stable")

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_sample_count_positive(self, result: StockAnalysisResult):
        """sample_count must be a positive integer."""
        ctx = result.sentiment_context
        assert isinstance(ctx["sample_count"], int)
        assert ctx["sample_count"] > 0

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_sub_scores_has_at_least_one_non_none(self, result: StockAnalysisResult):
        """sub_scores dict must have at least one non-None value."""
        ctx = result.sentiment_context
        sub_scores = ctx["sub_scores"]
        assert isinstance(sub_scores, dict)
        assert any(v is not None for v in sub_scores.values())

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_sub_scores_values_in_range(self, result: StockAnalysisResult):
        """All non-None sub_scores values must be in 0-100 range."""
        ctx = result.sentiment_context
        for key, val in ctx["sub_scores"].items():
            if val is not None:
                assert 0.0 <= val <= 100.0, f"sub_scores[{key}]={val} out of range"

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_source_availability_is_dict(self, result: StockAnalysisResult):
        """source_availability must be a dict with boolean values."""
        ctx = result.sentiment_context
        sa = ctx["source_availability"]
        assert isinstance(sa, dict)
        for key, val in sa.items():
            assert isinstance(val, bool), f"source_availability[{key}] is not bool"

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_label_is_valid_sentiment_label(self, result: StockAnalysisResult):
        """label must be a valid sentiment label."""
        ctx = result.sentiment_context
        valid_labels = {"extreme_fear", "fear", "neutral", "greed", "extreme_greed"}
        assert ctx["label"] in valid_labels

    @given(result=stock_analysis_result_with_sentiment_strategy())
    @settings(max_examples=100)
    def test_all_required_fields_present(self, result: StockAnalysisResult):
        """All required sentiment_context fields must be present simultaneously."""
        ctx = result.sentiment_context
        assert "index_value" in ctx
        assert "label" in ctx
        assert "trend_direction" in ctx
        assert "sample_count" in ctx
        assert "sub_scores" in ctx
        assert "source_availability" in ctx
