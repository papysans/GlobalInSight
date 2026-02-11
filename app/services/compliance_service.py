#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规脱敏服务 - ComplianceService

提供四级脱敏策略（轻度/中度/重度/不脱敏），个股板块映射表构建，
免责声明附加，合规检查等功能。

Requirements: 5A.1, 5A.2, 5A.3, 5A.4, 5A.5, 5A.8, 5A.9
"""

import asyncio
import json
import logging
import os
import re
import time
from typing import Dict, List, Optional

from pypinyin import lazy_pinyin, Style

from app.schemas import (
    ComplianceCheckResult,
    ComplianceSettings,
    CustomDesensitizeRule,
    DesensitizationLevel,
    StockSectorMapping,
)

logger = logging.getLogger(__name__)

# 免责声明文本
DISCLAIMER = "以上内容仅为市场观点讨论，不构成任何投资建议"

# 各平台推荐的默认脱敏级别
PLATFORM_DEFAULT_LEVELS: Dict[str, DesensitizationLevel] = {
    "xhs": DesensitizationLevel.MEDIUM,
    "weibo": DesensitizationLevel.LIGHT,
    "xueqiu": DesensitizationLevel.LIGHT,
    "zhihu": DesensitizationLevel.LIGHT,
}

# 6位股票代码正则（使用前后断言兼容中文环境）
STOCK_CODE_PATTERN = re.compile(r"(?<!\d)\d{6}(?!\d)")


class StockDesensitizer:
    """个股信息脱敏处理器，支持多级脱敏策略"""

    def __init__(self, mapping: Optional[Dict[str, StockSectorMapping]] = None):
        self.mapping: Dict[str, StockSectorMapping] = mapping or {}
        # 构建 stock_name -> StockSectorMapping 的反向索引
        self._name_index: Dict[str, StockSectorMapping] = {}
        self._rebuild_name_index()

    def _rebuild_name_index(self):
        """重建名称索引"""
        self._name_index = {}
        for m in self.mapping.values():
            self._name_index[m.stock_name] = m

    def update_mapping(self, mapping: Dict[str, StockSectorMapping]):
        """更新映射表"""
        self.mapping = mapping
        self._rebuild_name_index()

    # ------------------------------------------------------------------
    # 拼音缩写
    # ------------------------------------------------------------------

    @staticmethod
    def generate_pinyin_abbreviation(stock_name: str) -> str:
        """将股票名称转换为拼音首字母大写缩写。

        例如: "贵州茅台" → "GZMT", "宁德时代" → "NDSD"
        仅取中文字符的拼音首字母，忽略非中文字符。
        """
        try:
            initials = lazy_pinyin(stock_name, style=Style.FIRST_LETTER)
            abbr = "".join(c.upper() for c in initials if c.isalpha())
            return abbr if abbr else stock_name
        except Exception:
            logger.warning(f"拼音转换失败: {stock_name}，回退到原始名称")
            return stock_name

    # ------------------------------------------------------------------
    # 名称替换方法
    # ------------------------------------------------------------------

    def _sorted_names(self) -> List[str]:
        """按名称长度降序排列，确保长名称优先匹配"""
        return sorted(self._name_index.keys(), key=len, reverse=True)

    def replace_stock_names_light(self, text: str) -> str:
        """轻度脱敏：将个股名称替换为拼音缩写"""
        for name in self._sorted_names():
            if name in text:
                m = self._name_index[name]
                abbr = m.pinyin_abbr if m.pinyin_abbr else self.generate_pinyin_abbreviation(name)
                if not re.match(r"^[A-Z]{2,6}$", abbr):
                    # 拼音转换失败，回退到中度脱敏
                    logger.warning(f"拼音缩写格式异常: {name} → {abbr}，回退到行业描述")
                    abbr = m.desensitized_label if m.desensitized_label else "某上市公司"
                text = text.replace(name, abbr)
        return text

    def replace_stock_names_medium(self, text: str) -> str:
        """中度脱敏：将个股名称替换为行业描述（如"某白酒龙头"）"""
        for name in self._sorted_names():
            if name in text:
                m = self._name_index[name]
                label = m.desensitized_label if m.desensitized_label else "某上市公司"
                text = text.replace(name, label)
        return text

    def replace_stock_names_heavy(self, text: str) -> str:
        """重度脱敏：将个股名称替换为纯行业板块（如"白酒板块"）"""
        for name in self._sorted_names():
            if name in text:
                m = self._name_index[name]
                sector = f"{m.sector_name}板块" if m.sector_name else "某板块"
                text = text.replace(name, sector)
        return text

    def replace_stock_codes(self, text: str) -> str:
        """替换6位股票代码为行业描述或移除"""
        def _replace_code(match):
            code = match.group(0)
            if code in self.mapping:
                m = self.mapping[code]
                return m.desensitized_label if m.desensitized_label else "某上市公司"
            return "某股票"
        return STOCK_CODE_PATTERN.sub(_replace_code, text)

    @staticmethod
    def apply_custom_rules(text: str, rules: List[CustomDesensitizeRule]) -> str:
        """应用自定义脱敏规则"""
        for rule in rules:
            if rule.pattern and rule.pattern in text:
                text = text.replace(rule.pattern, rule.replacement)
        return text


class ComplianceService:
    """合规脱敏服务

    提供个股板块映射表构建、多级脱敏、免责声明、合规检查等功能。
    """

    CACHE_PATH = "cache/stock_sector_mapping.json"

    def __init__(self):
        self.desensitizer = StockDesensitizer()
        self._mapping_loaded = False
        self._last_refresh: float = 0
        self._refresh_interval = 86400  # 24小时刷新一次

    # ------------------------------------------------------------------
    # 映射表构建与冷启动
    # ------------------------------------------------------------------

    async def initialize_mapping(self):
        """应用启动时调用，处理冷启动逻辑。

        策略：
        1. 优先加载本地缓存（毫秒级）
        2. 有缓存时后台异步刷新（不阻塞）
        3. 无缓存时同步构建
        4. 构建失败时使用空映射 + 通用回退描述
        """
        cached = self._load_cached_mapping()
        if cached:
            self.desensitizer.update_mapping(cached)
            self._mapping_loaded = True
            logger.info(f"从缓存加载映射表: {len(cached)} 条记录")
            # 后台异步刷新
            asyncio.create_task(self._background_refresh_mapping())
            return

        # 无缓存，同步构建
        try:
            mapping = await self.build_stock_sector_mapping()
            self.desensitizer.update_mapping(mapping)
            self._mapping_loaded = True
            self._save_mapping_cache(mapping)
            logger.info(f"同步构建映射表完成: {len(mapping)} 条记录")
        except Exception as e:
            logger.warning(f"映射表构建失败，使用空映射: {e}")
            self.desensitizer.update_mapping({})
            self._mapping_loaded = True

    async def build_stock_sector_mapping(self) -> Dict[str, StockSectorMapping]:
        """通过 AKShare 获取板块数据，构建个股到板块/行业的映射表。

        使用 asyncio.to_thread() 包装所有 AKShare 同步调用。
        """
        try:
            import akshare as ak
        except ImportError:
            logger.error("akshare 未安装，无法构建映射表")
            return {}

        mapping: Dict[str, StockSectorMapping] = {}

        try:
            # 1. 获取行业板块列表
            boards_df = await asyncio.to_thread(ak.stock_board_industry_name_em)
            if boards_df is None or boards_df.empty:
                logger.warning("AKShare 行业板块列表为空")
                return {}

            board_names = boards_df["板块名称"].tolist()

            # 2. 尝试获取市值数据用于排名
            market_cap_data: Dict[str, float] = {}
            try:
                spot_df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
                if spot_df is not None and not spot_df.empty:
                    for _, row in spot_df.iterrows():
                        code = str(row.get("代码", ""))
                        cap = row.get("总市值", 0)
                        if code and cap:
                            market_cap_data[code] = float(cap)
            except Exception as e:
                logger.warning(f"获取市值数据失败，将使用默认排名: {e}")

            # 3. 逐板块获取成分股
            for board_name in board_names:
                try:
                    cons_df = await asyncio.to_thread(
                        ak.stock_board_industry_cons_em, symbol=board_name
                    )
                    if cons_df is None or cons_df.empty:
                        continue

                    # 收集板块内成分股及市值
                    stocks_in_board = []
                    for _, row in cons_df.iterrows():
                        code = str(row.get("代码", ""))
                        name = str(row.get("名称", ""))
                        if code and name:
                            cap = market_cap_data.get(code, 0)
                            stocks_in_board.append((code, name, cap))

                    # 按市值降序排列
                    stocks_in_board.sort(key=lambda x: x[2], reverse=True)

                    # 4. 生成映射
                    for rank, (code, name, _) in enumerate(stocks_in_board, 1):
                        if code in mapping:
                            continue  # 一只股票只保留第一个板块

                        # 生成 desensitized_label
                        if rank == 1:
                            label = f"某{board_name}龙头"
                        elif rank == 2:
                            label = f"某{board_name}龙二"
                        elif rank <= 5:
                            label = f"某{board_name}头部企业"
                        else:
                            label = f"某{board_name}企业"

                        # 生成拼音缩写
                        pinyin_abbr = StockDesensitizer.generate_pinyin_abbreviation(name)

                        mapping[code] = StockSectorMapping(
                            stock_code=code,
                            stock_name=name,
                            sector_name=board_name,
                            industry_name=board_name,
                            desensitized_label=label,
                            pinyin_abbr=pinyin_abbr,
                        )

                except Exception as e:
                    logger.debug(f"获取板块 {board_name} 成分股失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"构建映射表失败: {e}")
            raise

        self._last_refresh = time.time()
        return mapping

    async def _background_refresh_mapping(self):
        """后台异步刷新映射表，不影响当前服务"""
        try:
            new_mapping = await self.build_stock_sector_mapping()
            if new_mapping:
                self.desensitizer.update_mapping(new_mapping)
                self._save_mapping_cache(new_mapping)
                logger.info(f"后台刷新映射表完成: {len(new_mapping)} 条记录")
        except Exception as e:
            logger.debug(f"后台刷新映射表失败（不影响服务）: {e}")

    def _load_cached_mapping(self) -> Optional[Dict[str, StockSectorMapping]]:
        """从本地 JSON 缓存加载映射表"""
        try:
            if not os.path.exists(self.CACHE_PATH):
                return None
            with open(self.CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            mapping = {}
            for code, item in data.items():
                mapping[code] = StockSectorMapping(**item)
            return mapping
        except Exception as e:
            logger.warning(f"加载映射表缓存失败: {e}")
            return None

    def _save_mapping_cache(self, mapping: Dict[str, StockSectorMapping]):
        """保存映射表到本地 JSON 缓存"""
        try:
            os.makedirs(os.path.dirname(self.CACHE_PATH), exist_ok=True)
            data = {code: m.model_dump() for code, m in mapping.items()}
            with open(self.CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存映射表缓存失败: {e}")

    # ------------------------------------------------------------------
    # 脱敏级别获取
    # ------------------------------------------------------------------

    @staticmethod
    def get_desensitization_level(
        platform: str,
        user_settings: Optional[ComplianceSettings] = None,
    ) -> DesensitizationLevel:
        """获取指定平台的脱敏级别。

        优先使用用户设置的平台级别覆盖，否则使用 PLATFORM_DEFAULT_LEVELS 推荐默认值。
        """
        if user_settings and platform in user_settings.platform_levels:
            return user_settings.platform_levels[platform]
        if user_settings and user_settings.default_level:
            return user_settings.default_level
        return PLATFORM_DEFAULT_LEVELS.get(platform, DesensitizationLevel.MEDIUM)

    # ------------------------------------------------------------------
    # 脱敏处理
    # ------------------------------------------------------------------

    def desensitize_content(
        self,
        text: str,
        level: DesensitizationLevel = DesensitizationLevel.MEDIUM,
        custom_rules: Optional[List[CustomDesensitizeRule]] = None,
    ) -> str:
        """对文本执行脱敏处理。

        根据 level 选择不同策略：
        - LIGHT: 拼音缩写替换 → 替换股票代码 → 应用自定义规则
        - MEDIUM: 行业描述替换 → 替换股票代码 → 应用自定义规则
        - HEAVY: 纯行业板块替换 → 替换股票代码 → 应用自定义规则
        - NONE: 不做任何脱敏处理
        """
        if level == DesensitizationLevel.NONE:
            return text

        if level == DesensitizationLevel.LIGHT:
            text = self.desensitizer.replace_stock_names_light(text)
        elif level == DesensitizationLevel.MEDIUM:
            text = self.desensitizer.replace_stock_names_medium(text)
        elif level == DesensitizationLevel.HEAVY:
            text = self.desensitizer.replace_stock_names_heavy(text)

        text = self.desensitizer.replace_stock_codes(text)

        if custom_rules:
            text = StockDesensitizer.apply_custom_rules(text, custom_rules)

        return text

    # ------------------------------------------------------------------
    # 免责声明
    # ------------------------------------------------------------------

    @staticmethod
    def add_disclaimer(content: str) -> str:
        """强制附带免责声明。如果已包含则不重复添加。"""
        if DISCLAIMER not in content:
            content = f"{content}\n\n{DISCLAIMER}"
        return content

    # ------------------------------------------------------------------
    # 合规检查
    # ------------------------------------------------------------------

    def check_compliance(self, content: str) -> ComplianceCheckResult:
        """检查内容是否包含未脱敏的个股信息。

        仅生成警告信息供用户参考，不拦截发布操作。
        """
        violations: List[str] = []
        warnings: List[str] = []

        # 检查是否包含6位股票代码
        codes_found = STOCK_CODE_PATTERN.findall(content)
        if codes_found:
            violations.append(f"内容包含股票代码: {', '.join(set(codes_found))}")

        # 检查是否包含映射表中的个股名称
        for name in self.desensitizer._name_index:
            if name in content:
                violations.append(f"内容包含个股名称: {name}")

        # 检查免责声明
        if DISCLAIMER not in content:
            warnings.append("内容缺少免责声明")

        return ComplianceCheckResult(
            is_compliant=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # 审计日志
    # ------------------------------------------------------------------

    @staticmethod
    def log_publish_audit(content_id: str, platform: str,
                          desensitization_level: str,
                          user_acknowledged_risk: bool):
        """记录发布操作审计日志"""
        level = logging.WARNING if desensitization_level == "none" else logging.INFO
        logger.log(
            level,
            f"发布审计: content_id={content_id}, platform={platform}, "
            f"level={desensitization_level}, risk_ack={user_acknowledged_risk}",
        )


# 全局单例
compliance_service = ComplianceService()
