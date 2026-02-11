"""
Sentiment Analyzer Service.

Integrates SentimentCrawler and MixedSentimentDataService to perform
end-to-end sentiment analysis: comment collection → LLM classification →
mixed-source weighted index calculation → snapshot persistence.

Requirements: 9.15, 9.16, 9.17, 9.18, 9.19, 9.20, 9.31
"""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import SentimentCommentDB, SentimentSnapshotDB
from app.schemas import SentimentComment, SentimentContext, SentimentSnapshot
from app.services.mixed_sentiment_data_service import MixedSentimentDataService
from app.services.sentiment_crawler import SentimentCrawler

logger = logging.getLogger(__name__)

# Sentiment label thresholds
_LABEL_THRESHOLDS = [
    (20, "extreme_fear"),
    (40, "fear"),
    (60, "neutral"),
    (80, "greed"),
    (101, "extreme_greed"),
]


def _index_to_label(index_value: float) -> str:
    """Map a 0-100 index value to a sentiment label."""
    for threshold, label in _LABEL_THRESHOLDS:
        if index_value < threshold:
            return label
    return "extreme_greed"


def _is_key_event(index_value: float) -> bool:
    """A snapshot is a key event when index > 80 or < 20."""
    return index_value > 80 or index_value < 20


class SentimentAnalyzer:
    """Sentiment analysis and composite index calculation service.

    Orchestrates:
    1. Comment collection via SentimentCrawler
    2. LLM-based sentiment classification (batch)
    3. Aggregate metric collection via MixedSentimentDataService
    4. Weighted composite index calculation
    5. Snapshot and comment persistence
    """

    BATCH_SIZE = 50  # Max comments per LLM call

    def __init__(
        self,
        crawler: Optional[SentimentCrawler] = None,
        mixed_data_service: Optional[MixedSentimentDataService] = None,
    ):
        self.crawler = crawler or SentimentCrawler()
        self.mixed_data_service = mixed_data_service or MixedSentimentDataService()

    # ------------------------------------------------------------------
    # LLM batch analysis
    # ------------------------------------------------------------------

    async def analyze_batch(
        self, comments: List[SentimentComment]
    ) -> List[SentimentComment]:
        """Batch-classify comments via LLM.

        Splits into batches of BATCH_SIZE, calls LLM for each batch,
        and updates sentiment_label + sentiment_score on each comment.
        Returns the updated comment list.
        """
        if not comments:
            return comments

        all_analyzed: List[SentimentComment] = []

        for i in range(0, len(comments), self.BATCH_SIZE):
            batch = comments[i : i + self.BATCH_SIZE]
            analyzed = await self._analyze_single_batch(batch)
            all_analyzed.extend(analyzed)

        return all_analyzed

    async def _analyze_single_batch(
        self, batch: List[SentimentComment]
    ) -> List[SentimentComment]:
        """Analyze a single batch of comments via LLM."""
        try:
            from app.llm import get_agent_llm

            llm = get_agent_llm("analyst")

            # Build prompt
            comment_lines = []
            for idx, c in enumerate(batch):
                comment_lines.append(f"[{idx}] {c.content}")

            prompt = (
                "你是一个专业的股票市场情绪分析师。请对以下散户评论进行情绪分类。\n"
                "对每条评论，判断其情绪倾向并给出分数：\n"
                "- fear（恐慌）：表达担忧、恐惧、看空、割肉等负面情绪，分数 0-33\n"
                "- neutral（中性）：客观讨论、提问、无明显情绪倾向，分数 34-66\n"
                "- greed（贪婪）：表达乐观、看多、追涨、暴富等正面情绪，分数 67-100\n\n"
                "评论列表：\n"
                + "\n".join(comment_lines)
                + "\n\n请以 JSON 数组格式返回结果：\n"
                '[{"index": 0, "label": "fear|neutral|greed", "score": 0-100}, ...]'
            )

            from langchain_core.messages import HumanMessage

            result = await llm.ainvoke([HumanMessage(content=prompt)])
            content = result.content if hasattr(result, "content") else str(result)

            # Parse JSON from LLM response
            parsed = self._parse_llm_response(content, len(batch))

            # Apply labels to comments
            for entry in parsed:
                idx = entry.get("index", -1)
                if 0 <= idx < len(batch):
                    label = entry.get("label", "neutral")
                    if label not in ("fear", "greed", "neutral"):
                        label = "neutral"
                    score = entry.get("score", 50)
                    score = max(0, min(100, float(score)))

                    batch[idx] = batch[idx].model_copy(
                        update={"sentiment_label": label, "sentiment_score": score}
                    )

            # Fill any unclassified comments with neutral
            for idx, c in enumerate(batch):
                if c.sentiment_label is None:
                    batch[idx] = c.model_copy(
                        update={"sentiment_label": "neutral", "sentiment_score": 50.0}
                    )

            return batch

        except Exception as exc:
            logger.error(f"LLM sentiment analysis failed: {exc}")
            # On failure, mark all as neutral
            return [
                c.model_copy(
                    update={"sentiment_label": "neutral", "sentiment_score": 50.0}
                )
                if c.sentiment_label is None
                else c
                for c in batch
            ]

    @staticmethod
    def _parse_llm_response(content: str, expected_count: int) -> List[Dict]:
        """Extract JSON array from LLM response text."""
        import re

        # Try to find JSON array in the response
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: try parsing the entire content
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

        logger.warning("Failed to parse LLM sentiment response")
        return []

    # ------------------------------------------------------------------
    # Index calculation
    # ------------------------------------------------------------------

    def calculate_index(
        self,
        comments: List[SentimentComment],
        mixed_metrics: Optional[Dict] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> SentimentSnapshot:
        """Calculate composite sentiment index from comments + mixed metrics.

        1. Compute comment sentiment score: greed_count / total * 100
        2. Call mixed_data_service.calculate_weighted_index() for weighted merge
        3. Build SentimentSnapshot with all sub-scores
        """
        # Count sentiment labels
        total = len(comments)
        fear_count = sum(1 for c in comments if c.sentiment_label == "fear")
        greed_count = sum(1 for c in comments if c.sentiment_label == "greed")
        neutral_count = sum(1 for c in comments if c.sentiment_label == "neutral")

        # Comment sentiment score: greed proportion * 100
        comment_score = (greed_count / total * 100) if total > 0 else None

        # Ratios
        fear_ratio = fear_count / total if total > 0 else 0.0
        greed_ratio = greed_count / total if total > 0 else 0.0
        neutral_ratio = neutral_count / total if total > 0 else 0.0

        # Use mixed data service for weighted calculation
        if mixed_metrics is None:
            mixed_metrics = {
                "baidu_vote_score": None,
                "akshare_aggregate_score": None,
                "news_sentiment_score": None,
                "margin_trading_score": None,
                "source_availability": {},
            }

        weighted = self.mixed_data_service.calculate_weighted_index(
            comment_score, mixed_metrics, custom_weights
        )

        index_value = weighted["index_value"]
        label = _index_to_label(index_value)

        # Determine stock_code from comments (all should share the same)
        stock_code = None
        if comments:
            stock_code = comments[0].stock_code

        now_iso = datetime.now(timezone.utc).isoformat()

        return SentimentSnapshot(
            id=uuid.uuid4().hex,
            stock_code=stock_code,
            index_value=index_value,
            comment_sentiment_score=weighted.get("comment_sentiment_score"),
            baidu_vote_score=weighted.get("baidu_vote_score"),
            akshare_aggregate_score=weighted.get("akshare_aggregate_score"),
            news_sentiment_score=weighted.get("news_sentiment_score"),
            margin_trading_score=weighted.get("margin_trading_score"),
            fear_ratio=round(fear_ratio, 4),
            greed_ratio=round(greed_ratio, 4),
            neutral_ratio=round(neutral_ratio, 4),
            sample_count=total,
            data_source_availability=weighted.get("source_availability"),
            label=label,
            snapshot_time=now_iso,
        )

    # ------------------------------------------------------------------
    # Database queries
    # ------------------------------------------------------------------

    async def get_latest_index(
        self, stock_code: Optional[str] = None
    ) -> Optional[SentimentSnapshot]:
        """Get the most recent sentiment snapshot from the database.

        stock_code=None returns the overall market index.
        """
        async with async_session_factory() as session:
            if stock_code:
                stmt = (
                    select(SentimentSnapshotDB)
                    .where(SentimentSnapshotDB.stock_code == stock_code)
                    .order_by(SentimentSnapshotDB.snapshot_time.desc())
                    .limit(1)
                )
            else:
                stmt = (
                    select(SentimentSnapshotDB)
                    .where(SentimentSnapshotDB.stock_code.is_(None))
                    .order_by(SentimentSnapshotDB.snapshot_time.desc())
                    .limit(1)
                )

            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return self._db_snapshot_to_schema(row)

    async def get_index_history(
        self, stock_code: Optional[str] = None, days: int = 30
    ) -> List[SentimentSnapshot]:
        """Get sentiment snapshot history for time-series charts.

        Returns snapshots within the last *days* days, ordered by time ascending.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        async with async_session_factory() as session:
            if stock_code:
                stmt = (
                    select(SentimentSnapshotDB)
                    .where(
                        SentimentSnapshotDB.stock_code == stock_code,
                        SentimentSnapshotDB.snapshot_time >= cutoff,
                    )
                    .order_by(SentimentSnapshotDB.snapshot_time.asc())
                )
            else:
                stmt = (
                    select(SentimentSnapshotDB)
                    .where(
                        SentimentSnapshotDB.stock_code.is_(None),
                        SentimentSnapshotDB.snapshot_time >= cutoff,
                    )
                    .order_by(SentimentSnapshotDB.snapshot_time.asc())
                )

            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [self._db_snapshot_to_schema(r) for r in rows]

    # ------------------------------------------------------------------
    # Sentiment context (for stock analysis integration)
    # ------------------------------------------------------------------

    async def get_sentiment_context(
        self, stock_code: Optional[str] = None
    ) -> Optional[SentimentContext]:
        """Get sentiment context for stock analysis integration.

        Returns None if no snapshot data is available (graceful degradation).
        """
        try:
            latest = await self.get_latest_index(stock_code)
            if latest is None:
                return None

            # Determine trend direction from recent snapshots
            history = await self.get_index_history(stock_code, days=7)
            trend_direction = self._compute_trend(history)

            sub_scores = {
                "comment": latest.comment_sentiment_score,
                "baidu_vote": latest.baidu_vote_score,
                "akshare": latest.akshare_aggregate_score,
                "news": latest.news_sentiment_score,
                "margin": latest.margin_trading_score,
            }

            return SentimentContext(
                index_value=latest.index_value,
                label=latest.label,
                trend_direction=trend_direction,
                sample_count=latest.sample_count,
                sub_scores=sub_scores,
                source_availability=latest.data_source_availability or {},
            )
        except Exception as exc:
            logger.error(f"get_sentiment_context failed: {exc}")
            return None

    @staticmethod
    def _compute_trend(history: List[SentimentSnapshot]) -> str:
        """Compute trend direction from the last 3 snapshots."""
        if len(history) < 2:
            return "stable"

        recent = history[-3:] if len(history) >= 3 else history
        first_val = recent[0].index_value
        last_val = recent[-1].index_value
        diff = last_val - first_val

        if diff > 3:
            return "up"
        elif diff < -3:
            return "down"
        return "stable"

    # ------------------------------------------------------------------
    # Full analysis cycle
    # ------------------------------------------------------------------

    async def run_analysis_cycle(
        self,
        stock_code: Optional[str] = None,
        time_window_hours: int = 24,
    ) -> Optional[SentimentSnapshot]:
        """Execute a full sentiment analysis cycle.

        1. Collect comments via crawler
        2. LLM batch sentiment analysis
        3. Collect aggregate metrics via mixed data service
        4. Calculate weighted composite index
        5. Persist snapshot (with sub-scores and source availability)
        6. Persist comments
        """
        try:
            # Step 1: Collect comments
            comments = await self.crawler.collect_comments(
                stock_code=stock_code, time_window_hours=time_window_hours
            )
            logger.info(f"Collected {len(comments)} comments for stock={stock_code}")

            # Step 2: LLM analysis
            if comments:
                comments = await self.analyze_batch(comments)

            # Step 3: Collect aggregate metrics
            mixed_metrics = await self.mixed_data_service.collect_all_metrics(
                stock_code=stock_code
            )

            # Step 4: Calculate index
            snapshot = self.calculate_index(comments, mixed_metrics)

            # Step 5: Persist snapshot
            await self._persist_snapshot(snapshot)

            # Step 6: Persist comments
            if comments:
                await self._persist_comments(comments)

            logger.info(
                f"Analysis cycle complete: index={snapshot.index_value:.1f} "
                f"label={snapshot.label} samples={snapshot.sample_count}"
            )
            return snapshot

        except Exception as exc:
            logger.error(f"Analysis cycle failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def cleanup_old_comments(self, retention_days: int = 90) -> int:
        """Delete comments older than retention_days.

        Only deletes from sentiment_comments table.
        sentiment_snapshots are preserved permanently.

        Returns the number of deleted rows.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        async with async_session_factory() as session:
            stmt = delete(SentimentCommentDB).where(
                SentimentCommentDB.published_time < cutoff
            )
            result = await session.execute(stmt)
            await session.commit()
            deleted = result.rowcount
            logger.info(f"Cleaned up {deleted} comments older than {retention_days} days")
            return deleted

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    async def _persist_snapshot(self, snapshot: SentimentSnapshot) -> None:
        """Save a SentimentSnapshot to the database."""
        async with async_session_factory() as session:
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
                data_source_availability=json.dumps(
                    snapshot.data_source_availability or {}
                ),
                label=snapshot.label,
                snapshot_time=datetime.fromisoformat(snapshot.snapshot_time),
            )
            session.add(db_obj)
            await session.commit()

    async def _persist_comments(self, comments: List[SentimentComment]) -> None:
        """Save comments to the database, skipping duplicates."""
        async with async_session_factory() as session:
            for c in comments:
                try:
                    pub_time = datetime.fromisoformat(c.published_time)
                except (ValueError, TypeError):
                    pub_time = datetime.now(timezone.utc)

                db_obj = SentimentCommentDB(
                    id=c.id,
                    content=c.content,
                    source_platform=c.source_platform,
                    stock_code=c.stock_code,
                    author_nickname=c.author_nickname,
                    published_time=pub_time,
                    content_hash=c.content_hash,
                    sentiment_label=c.sentiment_label,
                    sentiment_score=c.sentiment_score,
                )
                await session.merge(db_obj)  # merge to handle duplicates

            await session.commit()

    @staticmethod
    def _db_snapshot_to_schema(row: SentimentSnapshotDB) -> SentimentSnapshot:
        """Convert a DB row to a SentimentSnapshot schema object."""
        # Parse data_source_availability from JSON text
        dsa = None
        if row.data_source_availability:
            try:
                dsa = json.loads(row.data_source_availability)
            except (json.JSONDecodeError, TypeError):
                dsa = None

        snapshot_time = ""
        if row.snapshot_time:
            if hasattr(row.snapshot_time, "isoformat"):
                snapshot_time = row.snapshot_time.isoformat()
            else:
                snapshot_time = str(row.snapshot_time)

        return SentimentSnapshot(
            id=row.id,
            stock_code=row.stock_code,
            index_value=row.index_value,
            comment_sentiment_score=row.comment_sentiment_score,
            baidu_vote_score=row.baidu_vote_score,
            akshare_aggregate_score=row.akshare_aggregate_score,
            news_sentiment_score=row.news_sentiment_score,
            margin_trading_score=row.margin_trading_score,
            fear_ratio=row.fear_ratio or 0.0,
            greed_ratio=row.greed_ratio or 0.0,
            neutral_ratio=row.neutral_ratio or 0.0,
            sample_count=row.sample_count or 0,
            data_source_availability=dsa,
            label=row.label or "neutral",
            snapshot_time=snapshot_time,
        )
