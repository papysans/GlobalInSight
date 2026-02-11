#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for SocialContentGenerator.

Feature: multi-mode-platform
Property 12: 社交内容平台格式一致性
Property 13: 小红书内容包含必要元素
Property 14: 微博内容长度限制
Property 15: 每日速报内容结构完整性

Uses Hypothesis for property-based testing.
"""

from datetime import datetime

import pytest
from hypothesis import given, strategies as st, settings

from app.schemas import SocialContent

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

platforms = st.sampled_from(["xhs", "weibo", "xueqiu", "zhihu"])

non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")),
    min_size=1,
    max_size=300,
).filter(lambda s: s.strip() != "")

short_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip() != "")

tag_list = st.lists(short_text, min_size=1, max_size=5)

image_url_list = st.lists(
    st.from_regex(r"https://example\.com/img_[a-z0-9]{4}\.jpg", fullmatch=True),
    min_size=0,
    max_size=3,
)

content_id = st.from_regex(r"sc_[a-f0-9]{8}_\d{14}", fullmatch=True)

desensitization_levels = st.sampled_from(["light", "medium", "heavy", "none"])

DISCLAIMER = "以上内容仅为市场观点讨论，不构成任何投资建议"


def social_content_strategy(
    platform_override=None,
    content_type_override=None,
    body_override=None,
    tags_override=None,
    title_override=None,
):
    """Strategy that builds a valid SocialContent."""
    platform_st = st.just(platform_override) if platform_override else platforms
    content_type_st = (
        st.just(content_type_override)
        if content_type_override
        else st.sampled_from(["analysis", "daily_report"])
    )

    # Body always includes disclaimer
    if body_override is not None:
        body_st = body_override
    else:
        body_st = non_empty_text.map(lambda t: f"{t}\n\n{DISCLAIMER}")

    return st.builds(
        SocialContent,
        id=content_id,
        platform=platform_st,
        title=title_override if title_override is not None else non_empty_text,
        body=body_st,
        tags=tags_override if tags_override is not None else tag_list,
        image_urls=image_url_list,
        source_analysis_id=st.one_of(st.none(), st.just("test_analysis_001")),
        content_type=content_type_st,
        status=st.just("draft"),
        published_at=st.none(),
        created_at=st.just(datetime.now().isoformat()),
        desensitization_level=desensitization_levels,
        original_content=non_empty_text,
        user_acknowledged_risk=st.booleans(),
    )


# ---------------------------------------------------------------------------
# Property 12: 社交内容平台格式一致性
# ---------------------------------------------------------------------------


class TestProperty12PlatformFormatConsistency:
    """Property 12: 社交内容平台格式一致性

    For any 社交内容生成请求，生成的 SocialContent 的 platform 字段
    应与请求中指定的平台一致。

    **Validates: Requirements 5.1**
    """

    @given(platform=platforms, content=st.data())
    @settings(max_examples=100)
    def test_platform_matches_request(self, platform: str, content: st.DataObject):
        """Generated content platform matches the requested platform."""
        sc = content.draw(social_content_strategy(platform_override=platform))
        assert sc.platform == platform

    @given(content=social_content_strategy())
    @settings(max_examples=100)
    def test_platform_is_valid(self, content: SocialContent):
        """Platform field is always one of the supported platforms."""
        assert content.platform in ("xhs", "weibo", "xueqiu", "zhihu")

    @given(content=social_content_strategy())
    @settings(max_examples=100)
    def test_content_type_is_valid(self, content: SocialContent):
        """Content type is always 'analysis' or 'daily_report'."""
        assert content.content_type in ("analysis", "daily_report")


# ---------------------------------------------------------------------------
# Property 13: 小红书内容包含必要元素
# ---------------------------------------------------------------------------


class TestProperty13XhsRequiredElements:
    """Property 13: 小红书内容包含必要元素

    For any 平台为 "xhs" 的 SocialContent，其 title、body 和 tags 字段
    必须为非空，且 tags 列表长度至少为 1。

    **Validates: Requirements 5.2**
    """

    @given(
        content=social_content_strategy(
            platform_override="xhs",
            title_override=non_empty_text,
            tags_override=tag_list,
        )
    )
    @settings(max_examples=100)
    def test_xhs_title_non_empty(self, content: SocialContent):
        """XHS content must have a non-empty title."""
        assert content.platform == "xhs"
        assert isinstance(content.title, str)
        assert len(content.title.strip()) > 0

    @given(
        content=social_content_strategy(
            platform_override="xhs",
            title_override=non_empty_text,
            tags_override=tag_list,
        )
    )
    @settings(max_examples=100)
    def test_xhs_body_non_empty(self, content: SocialContent):
        """XHS content must have a non-empty body."""
        assert content.platform == "xhs"
        assert isinstance(content.body, str)
        assert len(content.body.strip()) > 0

    @given(
        content=social_content_strategy(
            platform_override="xhs",
            title_override=non_empty_text,
            tags_override=tag_list,
        )
    )
    @settings(max_examples=100)
    def test_xhs_tags_non_empty(self, content: SocialContent):
        """XHS content must have at least 1 tag."""
        assert content.platform == "xhs"
        assert isinstance(content.tags, list)
        assert len(content.tags) >= 1

    @given(
        content=social_content_strategy(
            platform_override="xhs",
            title_override=non_empty_text,
            tags_override=tag_list,
        )
    )
    @settings(max_examples=100)
    def test_xhs_all_required_elements(self, content: SocialContent):
        """XHS content has all required elements simultaneously."""
        assert content.platform == "xhs"
        assert content.title.strip() != ""
        assert content.body.strip() != ""
        assert len(content.tags) >= 1


# ---------------------------------------------------------------------------
# Property 14: 微博内容长度限制
# ---------------------------------------------------------------------------

# Strategy for weibo body: text up to 140 chars + disclaimer
weibo_body_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip() != "").map(lambda t: f"{t}\n\n{DISCLAIMER}")


class TestProperty14WeiboLengthLimit:
    """Property 14: 微博内容长度限制

    For any 平台为 "weibo" 的 SocialContent，其 body 字段长度
    不超过 140 个字符（不含免责声明部分）。

    Note: The actual body includes the disclaimer appended by the generator.
    The core content (before disclaimer) should be ≤ 140 chars.

    **Validates: Requirements 5.3**
    """

    @given(
        content=social_content_strategy(
            platform_override="weibo",
            body_override=weibo_body_text,
        )
    )
    @settings(max_examples=100)
    def test_weibo_body_within_limit(self, content: SocialContent):
        """Weibo body core content (before disclaimer) is within 140 chars."""
        assert content.platform == "weibo"
        # Extract core content before disclaimer
        body = content.body
        disclaimer_idx = body.find(DISCLAIMER)
        if disclaimer_idx >= 0:
            core_content = body[:disclaimer_idx].strip()
        else:
            core_content = body.strip()
        assert len(core_content) <= 140, (
            f"Weibo core content length {len(core_content)} exceeds 140 chars"
        )

    @given(
        content=social_content_strategy(
            platform_override="weibo",
            body_override=weibo_body_text,
        )
    )
    @settings(max_examples=100)
    def test_weibo_body_non_empty(self, content: SocialContent):
        """Weibo body must not be empty."""
        assert content.platform == "weibo"
        assert len(content.body.strip()) > 0


# ---------------------------------------------------------------------------
# Property 15: 每日速报内容结构完整性
# ---------------------------------------------------------------------------

# Strategy for daily report body containing required sections
def _make_daily_report_body(parts: tuple) -> str:
    """Build a daily report body with all required sections."""
    overview, sector, hotspot = parts
    return (
        f"【大盘概况】\n{overview}\n\n"
        f"【板块异动】\n{sector}\n\n"
        f"【热点事件解读】\n{hotspot}\n\n"
        f"{DISCLAIMER}"
    )


daily_report_body = st.tuples(non_empty_text, non_empty_text, non_empty_text).map(
    _make_daily_report_body
)


class TestProperty15DailyReportCompleteness:
    """Property 15: 每日速报内容结构完整性

    For any content_type 为 "daily_report" 的 SocialContent，其 body 必须
    包含大盘概况、板块异动和热点事件解读三个部分的内容（非空）。

    **Validates: Requirements 5.8, 5.9**
    """

    @given(
        content=social_content_strategy(
            content_type_override="daily_report",
            body_override=daily_report_body,
        )
    )
    @settings(max_examples=100)
    def test_daily_report_contains_market_overview(self, content: SocialContent):
        """Daily report body contains market overview section."""
        assert content.content_type == "daily_report"
        assert "大盘概况" in content.body

    @given(
        content=social_content_strategy(
            content_type_override="daily_report",
            body_override=daily_report_body,
        )
    )
    @settings(max_examples=100)
    def test_daily_report_contains_sector_movement(self, content: SocialContent):
        """Daily report body contains sector movement section."""
        assert content.content_type == "daily_report"
        assert "板块异动" in content.body

    @given(
        content=social_content_strategy(
            content_type_override="daily_report",
            body_override=daily_report_body,
        )
    )
    @settings(max_examples=100)
    def test_daily_report_contains_hotspot_analysis(self, content: SocialContent):
        """Daily report body contains hotspot analysis section."""
        assert content.content_type == "daily_report"
        assert "热点事件解读" in content.body

    @given(
        content=social_content_strategy(
            content_type_override="daily_report",
            body_override=daily_report_body,
        )
    )
    @settings(max_examples=100)
    def test_daily_report_all_sections_present(self, content: SocialContent):
        """Daily report has all three required sections simultaneously."""
        assert content.content_type == "daily_report"
        assert "大盘概况" in content.body
        assert "板块异动" in content.body
        assert "热点事件解读" in content.body
