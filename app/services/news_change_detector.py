"""
新闻变化检测器 - NewsChangeDetector

检测股票资讯是否发生重大变化，用于触发速报自动更新。

检测规则：
1. 新增高热度资讯（≥3 条热度 > 10000）
2. 单条资讯热度暴涨（≥2 倍增长）
3. 热榜 Top3 大幅变化（≥2 条新上榜）
4. 新板块异动（之前未出现的板块突然上榜）
5. 投行评级升级集中出现（≥2 条新升级）

任一规则触发即视为"重大变化"。

Requirements: 5.9
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set

from loguru import logger

from app.schemas import StockNewsItem


@dataclass
class ChangeDetectionResult:
    """变化检测结果"""
    has_significant_change: bool = False
    triggered_rules: List[str] = field(default_factory=list)
    details: Dict[str, str] = field(default_factory=dict)
    detected_at: str = ""


class NewsChangeDetector:
    """新闻变化检测器

    维护上一次检测时的快照，与当前数据对比判断是否发生重大变化。
    """

    # 检测阈值
    HIGH_HEAT_THRESHOLD = 10000       # 高热度阈值
    HIGH_HEAT_MIN_COUNT = 3           # 高热度新增条数阈值
    HEAT_SURGE_MULTIPLIER = 2.0       # 热度暴涨倍数
    TOP_N = 3                         # Top N 变化检测范围
    TOP_CHANGE_MIN_COUNT = 2          # Top N 中新上榜条数阈值
    UPGRADE_MIN_COUNT = 2             # 评级升级集中出现阈值

    def __init__(self):
        self._previous_items: Dict[str, StockNewsItem] = {}
        self._previous_top_ids: List[str] = []
        self._previous_sectors: Set[str] = set()
        self._last_detection_time: Optional[datetime] = None

    def detect_changes(
        self, current_items: List[StockNewsItem]
    ) -> ChangeDetectionResult:
        """对比当前资讯与上次快照，检测是否发生重大变化。

        首次调用时（无历史快照）不触发变化，仅保存快照。
        """
        result = ChangeDetectionResult(detected_at=datetime.now().isoformat())

        # 首次运行，保存快照后返回
        if not self._previous_items:
            self._save_snapshot(current_items)
            logger.info("NewsChangeDetector: 首次运行，已保存基线快照")
            return result

        current_map = {item.id: item for item in current_items}

        # 规则 1: 新增高热度资讯
        self._check_high_heat_new(current_map, result)

        # 规则 2: 单条资讯热度暴涨
        self._check_heat_surge(current_map, result)

        # 规则 3: 热榜 Top3 大幅变化
        self._check_top_change(current_items, result)

        # 规则 4: 新板块异动
        self._check_new_sectors(current_items, result)

        # 规则 5: 投行评级升级集中出现
        self._check_rating_upgrades(current_items, result)

        result.has_significant_change = len(result.triggered_rules) > 0

        if result.has_significant_change:
            logger.info(
                f"NewsChangeDetector: 检测到重大变化，触发规则: "
                f"{', '.join(result.triggered_rules)}"
            )

        # 更新快照
        self._save_snapshot(current_items)
        self._last_detection_time = datetime.now()

        return result

    # ------------------------------------------------------------------
    # 规则实现
    # ------------------------------------------------------------------

    def _parse_hot_value(self, hot_value: str) -> float:
        """将热度值字符串解析为数值"""
        try:
            cleaned = hot_value.replace(",", "").replace("万", "0000").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0

    def _check_high_heat_new(
        self, current_map: Dict[str, StockNewsItem], result: ChangeDetectionResult
    ):
        """规则 1: 新增高热度资讯（≥3 条热度 > 10000）"""
        new_high_heat = []
        for item_id, item in current_map.items():
            if item_id not in self._previous_items:
                heat = self._parse_hot_value(item.hot_value)
                if heat > self.HIGH_HEAT_THRESHOLD:
                    new_high_heat.append(item.title)

        if len(new_high_heat) >= self.HIGH_HEAT_MIN_COUNT:
            result.triggered_rules.append("high_heat_new")
            result.details["high_heat_new"] = (
                f"新增 {len(new_high_heat)} 条高热度资讯: "
                f"{', '.join(new_high_heat[:3])}"
            )

    def _check_heat_surge(
        self, current_map: Dict[str, StockNewsItem], result: ChangeDetectionResult
    ):
        """规则 2: 单条资讯热度暴涨（≥2 倍增长）"""
        surged = []
        for item_id, item in current_map.items():
            if item_id in self._previous_items:
                prev = self._previous_items[item_id]
                cur_heat = self._parse_hot_value(item.hot_value)
                prev_heat = self._parse_hot_value(prev.hot_value)
                if prev_heat > 0 and cur_heat >= prev_heat * self.HEAT_SURGE_MULTIPLIER:
                    surged.append(
                        f"{item.title} ({prev_heat:.0f}→{cur_heat:.0f})"
                    )

        if surged:
            result.triggered_rules.append("heat_surge")
            result.details["heat_surge"] = (
                f"{len(surged)} 条资讯热度暴涨: {', '.join(surged[:3])}"
            )

    def _check_top_change(
        self, current_items: List[StockNewsItem], result: ChangeDetectionResult
    ):
        """规则 3: 热榜 Top3 大幅变化（≥2 条新上榜）"""
        current_top_ids = [item.id for item in current_items[:self.TOP_N]]
        prev_top_set = set(self._previous_top_ids)

        new_in_top = [tid for tid in current_top_ids if tid not in prev_top_set]

        if len(new_in_top) >= self.TOP_CHANGE_MIN_COUNT:
            result.triggered_rules.append("top_change")
            new_titles = [
                item.title for item in current_items[:self.TOP_N]
                if item.id in new_in_top
            ]
            result.details["top_change"] = (
                f"Top{self.TOP_N} 中 {len(new_in_top)} 条新上榜: "
                f"{', '.join(new_titles)}"
            )

    def _check_new_sectors(
        self, current_items: List[StockNewsItem], result: ChangeDetectionResult
    ):
        """规则 4: 新板块异动（之前未出现的板块突然上榜）"""
        current_sectors: Set[str] = set()
        for item in current_items:
            if item.category and item.category != "international":
                # 从标题中提取可能的板块关键词（简化实现）
                for keyword in ["板块", "行业", "概念", "赛道"]:
                    if keyword in item.title:
                        # 取关键词前面的词作为板块名
                        idx = item.title.index(keyword)
                        sector = item.title[max(0, idx - 4):idx + len(keyword)]
                        if sector:
                            current_sectors.add(sector)

        new_sectors = current_sectors - self._previous_sectors
        if new_sectors:
            result.triggered_rules.append("new_sectors")
            result.details["new_sectors"] = (
                f"新板块异动: {', '.join(new_sectors)}"
            )

    def _check_rating_upgrades(
        self, current_items: List[StockNewsItem], result: ChangeDetectionResult
    ):
        """规则 5: 投行评级升级集中出现（≥2 条新升级）"""
        upgrades = []
        for item in current_items:
            if item.id not in self._previous_items:
                if (
                    item.analyst_rating
                    and item.analyst_rating.action in ("upgrade", "initiate")
                    and item.analyst_rating.rating_normalized == "buy"
                ):
                    upgrades.append(
                        f"{item.analyst_rating.firm}: "
                        f"{item.analyst_rating.stock_name} → {item.analyst_rating.rating}"
                    )

        if len(upgrades) >= self.UPGRADE_MIN_COUNT:
            result.triggered_rules.append("rating_upgrades")
            result.details["rating_upgrades"] = (
                f"{len(upgrades)} 条新评级升级: {', '.join(upgrades[:3])}"
            )

    # ------------------------------------------------------------------
    # 快照管理
    # ------------------------------------------------------------------

    def _save_snapshot(self, items: List[StockNewsItem]):
        """保存当前数据为快照"""
        self._previous_items = {item.id: item for item in items}
        self._previous_top_ids = [item.id for item in items[:self.TOP_N]]

        self._previous_sectors = set()
        for item in items:
            if item.category and item.category != "international":
                for keyword in ["板块", "行业", "概念", "赛道"]:
                    if keyword in item.title:
                        idx = item.title.index(keyword)
                        sector = item.title[max(0, idx - 4):idx + len(keyword)]
                        if sector:
                            self._previous_sectors.add(sector)

    def reset(self):
        """重置检测器状态"""
        self._previous_items.clear()
        self._previous_top_ids.clear()
        self._previous_sectors.clear()
        self._last_detection_time = None


# 全局实例
news_change_detector = NewsChangeDetector()
