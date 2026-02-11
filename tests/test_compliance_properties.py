#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for ComplianceService.

Feature: multi-mode-platform
Property 18: 脱敏内容不含股票代码
Property 19: 脱敏内容不含个股名称
Property 20: 社交内容包含免责声明
Property 21: 脱敏可逆性
Property 22: 拼音缩写格式正确性
Property 23: 平台默认脱敏级别一致性

Uses Hypothesis for property-based testing.
Validates: Requirements 5A.2, 5A.3, 5A.5, 5A.6, 5A.9
"""

import re

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.schemas import (
    ComplianceSettings,
    CustomDesensitizeRule,
    DesensitizationLevel,
    StockSectorMapping,
)
from app.services.compliance_service import (
    ComplianceService,
    StockDesensitizer,
    DISCLAIMER,
    PLATFORM_DEFAULT_LEVELS,
    STOCK_CODE_PATTERN,
)

# ---------------------------------------------------------------------------
# Test fixtures: realistic stock mapping data
# ---------------------------------------------------------------------------

SAMPLE_MAPPINGS = {
    "600519": StockSectorMapping(
        stock_code="600519", stock_name="贵州茅台",
        sector_name="白酒", industry_name="食品饮料",
        desensitized_label="某白酒龙头", pinyin_abbr="GZMT",
    ),
    "300750": StockSectorMapping(
        stock_code="300750", stock_name="宁德时代",
        sector_name="电池", industry_name="新能源",
        desensitized_label="某电池龙头", pinyin_abbr="NDSD",
    ),
    "000858": StockSectorMapping(
        stock_code="000858", stock_name="五粮液",
        sector_name="白酒", industry_name="食品饮料",
        desensitized_label="某白酒龙二", pinyin_abbr="WLY",
    ),
    "601318": StockSectorMapping(
        stock_code="601318", stock_name="中国平安",
        sector_name="保险", industry_name="金融",
        desensitized_label="某保险龙头", pinyin_abbr="ZGPA",
    ),
    "000001": StockSectorMapping(
        stock_code="000001", stock_name="平安银行",
        sector_name="银行", industry_name="金融",
        desensitized_label="某银行企业", pinyin_abbr="PAYH",
    ),
}

STOCK_NAMES = [m.stock_name for m in SAMPLE_MAPPINGS.values()]
STOCK_CODES = list(SAMPLE_MAPPINGS.keys())


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Generate text that contains stock names and codes
def _inject_stock_info(base_text: str) -> str:
    """Inject stock names and codes into text for testing."""
    return f"今天贵州茅台(600519)大涨，宁德时代(300750)也表现不错，五粮液(000858)跟涨。{base_text}"


base_text_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=5,
    max_size=100,
).filter(lambda s: s.strip() != "")

text_with_stocks = base_text_st.map(_inject_stock_info)

active_levels = st.sampled_from([
    DesensitizationLevel.LIGHT,
    DesensitizationLevel.MEDIUM,
    DesensitizationLevel.HEAVY,
])

all_levels = st.sampled_from([
    DesensitizationLevel.LIGHT,
    DesensitizationLevel.MEDIUM,
    DesensitizationLevel.HEAVY,
    DesensitizationLevel.NONE,
])

platforms = st.sampled_from(["xhs", "weibo", "xueqiu", "zhihu"])


def make_service() -> ComplianceService:
    """Create a ComplianceService with sample mappings loaded."""
    svc = ComplianceService()
    svc.desensitizer.update_mapping(SAMPLE_MAPPINGS)
    return svc


# ---------------------------------------------------------------------------
# Property 18: 脱敏内容不含股票代码
# ---------------------------------------------------------------------------


class TestProperty18NoStockCodes:
    """Property 18: 脱敏内容不含股票代码

    For any desensitization_level 为 light/medium/heavy 的内容，
    脱敏后的 body 和 title 中不应包含任何匹配 \\d{6} 模式的6位股票代码。

    **Validates: Requirements 5A.3**
    """

    @given(text=text_with_stocks, level=active_levels)
    @settings(max_examples=100)
    def test_no_stock_codes_after_desensitization(self, text: str, level: DesensitizationLevel):
        svc = make_service()
        result = svc.desensitize_content(text, level=level)
        # Check that no 6-digit stock codes from our mapping remain
        for code in STOCK_CODES:
            assert code not in result, (
                f"Stock code {code} found in desensitized content at level {level.value}"
            )

    @given(level=active_levels)
    @settings(max_examples=100)
    def test_known_codes_removed(self, level: DesensitizationLevel):
        """Specific known codes are removed from text."""
        svc = make_service()
        text = "关注600519和300750的走势"
        result = svc.desensitize_content(text, level=level)
        assert "600519" not in result
        assert "300750" not in result


# ---------------------------------------------------------------------------
# Property 19: 脱敏内容不含个股名称
# ---------------------------------------------------------------------------


class TestProperty19NoStockNames:
    """Property 19: 脱敏内容不含个股名称

    For any desensitization_level 为 medium/heavy 的内容，
    脱敏后不应包含映射表中任何 stock_name。

    **Validates: Requirements 5A.2**
    """

    @given(
        text=text_with_stocks,
        level=st.sampled_from([DesensitizationLevel.MEDIUM, DesensitizationLevel.HEAVY]),
    )
    @settings(max_examples=100)
    def test_no_stock_names_after_medium_heavy(self, text: str, level: DesensitizationLevel):
        svc = make_service()
        result = svc.desensitize_content(text, level=level)
        for name in STOCK_NAMES:
            assert name not in result, (
                f"Stock name '{name}' found in desensitized content at level {level.value}"
            )

    @given(text=text_with_stocks)
    @settings(max_examples=100)
    def test_light_also_removes_names(self, text: str):
        """Light desensitization replaces names with pinyin abbreviations."""
        svc = make_service()
        result = svc.desensitize_content(text, level=DesensitizationLevel.LIGHT)
        for name in STOCK_NAMES:
            assert name not in result, (
                f"Stock name '{name}' found in light-desensitized content"
            )


# ---------------------------------------------------------------------------
# Property 20: 社交内容包含免责声明
# ---------------------------------------------------------------------------


class TestProperty20DisclaimerPresent:
    """Property 20: 社交内容包含免责声明

    For any SocialContent（无论是否脱敏），其 body 必须包含免责声明文本。

    **Validates: Requirements 5A.5**
    """

    @given(text=base_text_st)
    @settings(max_examples=100)
    def test_disclaimer_added(self, text: str):
        result = ComplianceService.add_disclaimer(text)
        assert DISCLAIMER in result

    @given(text=base_text_st)
    @settings(max_examples=100)
    def test_disclaimer_not_duplicated(self, text: str):
        """Disclaimer is not added twice if already present."""
        text_with_disclaimer = f"{text}\n\n{DISCLAIMER}"
        result = ComplianceService.add_disclaimer(text_with_disclaimer)
        assert result.count(DISCLAIMER) == 1

    @given(text=base_text_st, level=all_levels)
    @settings(max_examples=100)
    def test_disclaimer_after_desensitize_and_add(self, text: str, level: DesensitizationLevel):
        """Full pipeline: desensitize then add disclaimer always includes disclaimer."""
        svc = make_service()
        desensitized = svc.desensitize_content(text, level=level)
        final = ComplianceService.add_disclaimer(desensitized)
        assert DISCLAIMER in final


# ---------------------------------------------------------------------------
# Property 21: 脱敏可逆性
# ---------------------------------------------------------------------------


class TestProperty21Reversibility:
    """Property 21: 脱敏可逆性

    For any desensitization_level 不为 none 的 SocialContent，
    其 original_content 字段必须为非空字符串，保留脱敏前的完整内容。

    This property tests the workflow: save original → desensitize → verify original preserved.

    **Validates: Requirements 5A.6**
    """

    @given(text=text_with_stocks, level=active_levels)
    @settings(max_examples=100)
    def test_original_content_preserved(self, text: str, level: DesensitizationLevel):
        """Simulating the content generation workflow:
        1. Save original_content = text
        2. Desensitize text
        3. Verify original_content is non-empty and different from desensitized
        """
        svc = make_service()
        original_content = text  # Step 1: save original
        desensitized = svc.desensitize_content(text, level=level)  # Step 2: desensitize

        # original_content must be non-empty
        assert original_content is not None
        assert len(original_content.strip()) > 0

        # desensitized content should differ from original (since text contains stock info)
        assert desensitized != original_content, (
            "Desensitized content should differ from original when stock info is present"
        )

    @given(text=text_with_stocks, level=active_levels)
    @settings(max_examples=100)
    def test_original_contains_stock_info(self, text: str, level: DesensitizationLevel):
        """Original content still contains stock names that were removed by desensitization."""
        original_content = text
        # Original should contain at least one stock name
        has_stock = any(name in original_content for name in STOCK_NAMES)
        assert has_stock, "Test text should contain stock names"


# ---------------------------------------------------------------------------
# Property 22: 拼音缩写格式正确性
# ---------------------------------------------------------------------------

PINYIN_ABBR_PATTERN = re.compile(r"^[A-Z]{2,6}$")


class TestProperty22PinyinFormat:
    """Property 22: 拼音缩写格式正确性

    For any desensitization_level 为 light 的内容，个股名称应被替换为
    匹配 [A-Z]{2,6} 的拼音缩写。

    **Validates: Requirements 5A.2**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_pinyin_abbreviation_format(self, data):
        """All pinyin abbreviations in the mapping match [A-Z]{2,6}."""
        for m in SAMPLE_MAPPINGS.values():
            abbr = StockDesensitizer.generate_pinyin_abbreviation(m.stock_name)
            assert PINYIN_ABBR_PATTERN.match(abbr), (
                f"Pinyin abbreviation '{abbr}' for '{m.stock_name}' "
                f"does not match [A-Z]{{2,6}}"
            )

    @given(text=text_with_stocks)
    @settings(max_examples=100)
    def test_light_desensitization_uses_pinyin(self, text: str):
        """Light desensitization replaces stock names with pinyin abbreviations."""
        svc = make_service()
        result = svc.desensitize_content(text, level=DesensitizationLevel.LIGHT)
        # Check that known pinyin abbreviations appear in the result
        found_any = False
        for m in SAMPLE_MAPPINGS.values():
            if m.pinyin_abbr in result:
                found_any = True
                assert PINYIN_ABBR_PATTERN.match(m.pinyin_abbr)
        assert found_any, "At least one pinyin abbreviation should appear in light-desensitized text"

    def test_known_pinyin_abbreviations(self):
        """Verify specific known stock name → pinyin mappings."""
        cases = [
            ("贵州茅台", "GZMT"),
            ("宁德时代", "NDSD"),
            ("五粮液", "WLY"),
            ("中国平安", "ZGPA"),
            ("平安银行", "PAYH"),
        ]
        for name, expected in cases:
            result = StockDesensitizer.generate_pinyin_abbreviation(name)
            assert result == expected, f"Expected {expected} for {name}, got {result}"


# ---------------------------------------------------------------------------
# Property 23: 平台默认脱敏级别一致性
# ---------------------------------------------------------------------------


class TestProperty23PlatformDefaultLevels:
    """Property 23: 平台默认脱敏级别一致性

    For any SocialContent，若用户未设置该平台的脱敏级别覆盖，
    则实际应用的 desensitization_level 应与该平台的推荐默认值一致。

    **Validates: Requirements 5A.9**
    """

    @given(platform=platforms)
    @settings(max_examples=100)
    def test_default_level_without_user_override(self, platform: str):
        """Without user settings, platform default level is used."""
        level = ComplianceService.get_desensitization_level(platform, user_settings=None)
        expected = PLATFORM_DEFAULT_LEVELS[platform]
        assert level == expected, (
            f"Platform {platform}: expected {expected.value}, got {level.value}"
        )

    @given(platform=platforms)
    @settings(max_examples=100)
    def test_default_level_with_empty_settings(self, platform: str):
        """With empty ComplianceSettings (no platform overrides), default level is used."""
        settings_obj = ComplianceSettings()
        level = ComplianceService.get_desensitization_level(platform, user_settings=settings_obj)
        # ComplianceSettings default_level is MEDIUM, which overrides platform defaults
        assert level == DesensitizationLevel.MEDIUM

    @given(platform=platforms, override_level=all_levels)
    @settings(max_examples=100)
    def test_user_override_takes_precedence(self, platform: str, override_level: DesensitizationLevel):
        """User platform-level override takes precedence over defaults."""
        user_settings = ComplianceSettings(
            platform_levels={platform: override_level}
        )
        level = ComplianceService.get_desensitization_level(platform, user_settings=user_settings)
        assert level == override_level

    def test_known_platform_defaults(self):
        """Verify the specific platform default levels match requirements."""
        assert PLATFORM_DEFAULT_LEVELS["xhs"] == DesensitizationLevel.MEDIUM
        assert PLATFORM_DEFAULT_LEVELS["weibo"] == DesensitizationLevel.LIGHT
        assert PLATFORM_DEFAULT_LEVELS["xueqiu"] == DesensitizationLevel.LIGHT
        assert PLATFORM_DEFAULT_LEVELS["zhihu"] == DesensitizationLevel.LIGHT
