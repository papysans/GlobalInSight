"""
Mixed Sentiment Data Service.

Collects aggregate sentiment indicators from AKShare (Baidu vote, news sentiment,
margin trading, Xueqiu heat, etc.) and computes a weighted composite sentiment index.

All AKShare calls are wrapped with asyncio.to_thread() to avoid blocking the event loop.

Requirements: 9.10, 9.11, 9.12, 9.13, 9.14, 9.17
"""

import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Default weight configuration for the composite sentiment index
DEFAULT_SENTIMENT_WEIGHTS: Dict[str, float] = {
    "comment_sentiment": 0.40,   # LLM-analyzed retail comment sentiment
    "baidu_vote": 0.20,          # Baidu stock vote bullish ratio
    "akshare_aggregate": 0.15,   # AKShare comment metrics (千股千评 + popularity)
    "news_sentiment": 0.15,      # News sentiment index
    "margin_trading": 0.10,      # Margin trading signal
}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


class MixedSentimentDataService:
    """Collects aggregate sentiment metrics via AKShare and computes weighted index."""

    def __init__(self):
        self.weights: Dict[str, float] = DEFAULT_SENTIMENT_WEIGHTS.copy()

    # ------------------------------------------------------------------
    # Individual data source fetchers
    # ------------------------------------------------------------------

    async def fetch_akshare_comment_metrics(self, stock_code: str = None) -> Optional[Dict]:
        """Fetch AKShare comment metrics (千股千评, popularity ranking).

        Calls:
        - stock_comment_em()
        - stock_comment_detail_scrd_focus_em()
        - stock_hot_rank_em()
        - stock_hot_keyword_em()

        Returns a dict with 'score' normalized to 0-100, or None on failure.
        """
        try:
            import akshare as ak

            scores = []

            # 千股千评 comprehensive score
            try:
                df = await asyncio.to_thread(ak.stock_comment_em)
                if df is not None and not df.empty:
                    if stock_code:
                        mask = df.iloc[:, 0].astype(str).str.contains(stock_code)
                        filtered = df[mask]
                        if not filtered.empty:
                            # Use comprehensive score column (typically column index 4 or named)
                            for col in filtered.columns:
                                if "综合" in str(col) or "得分" in str(col):
                                    val = filtered[col].iloc[0]
                                    if val is not None:
                                        scores.append(float(val))
                                    break
                    else:
                        # Market-wide: average of top entries
                        for col in df.columns:
                            if "综合" in str(col) or "得分" in str(col):
                                avg = df[col].head(50).mean()
                                if avg is not None:
                                    scores.append(float(avg))
                                break
            except Exception as e:
                logger.debug(f"stock_comment_em failed: {e}")

            # Popularity ranking
            try:
                df_hot = await asyncio.to_thread(ak.stock_hot_rank_em)
                if df_hot is not None and not df_hot.empty:
                    if stock_code:
                        mask = df_hot.iloc[:, 0].astype(str).str.contains(stock_code)
                        filtered = df_hot[mask]
                        if not filtered.empty:
                            # Rank-based score: higher rank = higher score
                            total = len(df_hot)
                            rank_idx = filtered.index[0]
                            rank_score = (1 - rank_idx / max(total, 1)) * 100
                            scores.append(_clamp(rank_score))
                    else:
                        scores.append(50.0)  # Neutral for market-wide
            except Exception as e:
                logger.debug(f"stock_hot_rank_em failed: {e}")

            if not scores:
                return None

            final_score = _clamp(sum(scores) / len(scores))
            return {"score": final_score}

        except Exception as e:
            logger.warning(f"fetch_akshare_comment_metrics failed: {e}")
            return None

    async def fetch_baidu_vote(self, stock_code: str) -> Optional[Dict]:
        """Fetch Baidu stock vote data.

        Calls: stock_zh_vote_baidu(stock_code)
        Returns: {bullish_ratio, bearish_ratio, score} where score = bullish_ratio * 100
        """
        try:
            import akshare as ak

            df = await asyncio.to_thread(ak.stock_zh_vote_baidu, symbol=stock_code)
            if df is None or df.empty:
                return None

            # The dataframe typically has columns for bullish/bearish percentages
            bullish = None
            bearish = None
            for col in df.columns:
                col_str = str(col)
                if "看涨" in col_str or "bullish" in col_str.lower():
                    bullish = float(df[col].iloc[-1])
                elif "看跌" in col_str or "bearish" in col_str.lower():
                    bearish = float(df[col].iloc[-1])

            if bullish is None:
                # Try numeric approach: first numeric column as bullish ratio
                numeric_cols = df.select_dtypes(include=["number"]).columns
                if len(numeric_cols) >= 1:
                    bullish = float(df[numeric_cols[0]].iloc[-1])
                if len(numeric_cols) >= 2:
                    bearish = float(df[numeric_cols[1]].iloc[-1])

            if bullish is None:
                return None

            # If bullish is already a percentage (0-100), use directly
            # If it's a ratio (0-1), multiply by 100
            if bullish <= 1.0:
                score = _clamp(bullish * 100)
            else:
                score = _clamp(bullish)

            return {
                "bullish_ratio": bullish,
                "bearish_ratio": bearish,
                "score": score,
            }

        except Exception as e:
            logger.warning(f"fetch_baidu_vote failed for {stock_code}: {e}")
            return None

    async def fetch_news_sentiment_index(self) -> Optional[Dict]:
        """Fetch news sentiment index from AKShare.

        Calls: index_news_sentiment_scope()
        Returns: {score} normalized to 0-100
        """
        try:
            import akshare as ak

            df = await asyncio.to_thread(ak.index_news_sentiment_scope)
            if df is None or df.empty:
                return None

            # Use the latest value from the sentiment index
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) == 0:
                return None

            latest_val = float(df[numeric_cols[-1]].iloc[-1])

            # Normalize: the raw index varies; map to 0-100
            # Typical range is around -1 to 1 or 0 to 100 depending on version
            if -10 <= latest_val <= 10:
                # Likely a -1 to 1 or similar small range
                score = _clamp((latest_val + 1) / 2 * 100) if latest_val <= 1 else _clamp(latest_val)
            elif 0 <= latest_val <= 100:
                score = _clamp(latest_val)
            else:
                # Arbitrary normalization for unknown ranges
                score = _clamp(latest_val, 0, 100)

            return {"score": score}

        except Exception as e:
            logger.warning(f"fetch_news_sentiment_index failed: {e}")
            return None

    async def fetch_margin_trading_data(self, stock_code: str = None) -> Optional[Dict]:
        """Fetch margin trading data.

        Calls: stock_margin_detail_szse() / stock_margin_detail_sse()
        Returns: {score} normalized to 0-100 based on net margin buying change rate.
        """
        try:
            import akshare as ak

            df = None
            # Try SZSE first, then SSE
            try:
                df = await asyncio.to_thread(ak.stock_margin_detail_szse)
            except Exception:
                pass

            if df is None or df.empty:
                try:
                    df = await asyncio.to_thread(ak.stock_margin_detail_sse)
                except Exception:
                    pass

            if df is None or df.empty:
                return None

            if stock_code:
                mask = df.iloc[:, 0].astype(str).str.contains(stock_code)
                df = df[mask]
                if df.empty:
                    return None

            # Look for margin buying columns
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) == 0:
                return None

            # Use the first numeric column as a proxy for margin buying amount
            latest = float(df[numeric_cols[0]].iloc[-1])

            # Normalize: positive net buying → higher score, negative → lower
            # Simple sigmoid-like normalization
            if latest > 0:
                score = _clamp(50 + min(latest / 1e8, 1) * 50)
            else:
                score = _clamp(50 + max(latest / 1e8, -1) * 50)

            return {"score": score}

        except Exception as e:
            logger.warning(f"fetch_margin_trading_data failed: {e}")
            return None

    async def fetch_xueqiu_heat_data(self, stock_code: str = None) -> Optional[Dict]:
        """Fetch Xueqiu platform heat data via AKShare.

        Calls: stock_hot_follow_xq(), stock_hot_tweet_xq()
        Returns heat data as supplementary input for AKShare aggregate score.
        """
        try:
            import akshare as ak

            follow_score = None
            tweet_score = None

            try:
                df_follow = await asyncio.to_thread(ak.stock_hot_follow_xq)
                if df_follow is not None and not df_follow.empty:
                    if stock_code:
                        mask = df_follow.iloc[:, 0].astype(str).str.contains(stock_code)
                        filtered = df_follow[mask]
                        if not filtered.empty:
                            total = len(df_follow)
                            rank_idx = filtered.index[0]
                            follow_score = _clamp((1 - rank_idx / max(total, 1)) * 100)
                    else:
                        follow_score = 50.0
            except Exception as e:
                logger.debug(f"stock_hot_follow_xq failed: {e}")

            try:
                df_tweet = await asyncio.to_thread(ak.stock_hot_tweet_xq)
                if df_tweet is not None and not df_tweet.empty:
                    if stock_code:
                        mask = df_tweet.iloc[:, 0].astype(str).str.contains(stock_code)
                        filtered = df_tweet[mask]
                        if not filtered.empty:
                            total = len(df_tweet)
                            rank_idx = filtered.index[0]
                            tweet_score = _clamp((1 - rank_idx / max(total, 1)) * 100)
                    else:
                        tweet_score = 50.0
            except Exception as e:
                logger.debug(f"stock_hot_tweet_xq failed: {e}")

            scores = [s for s in [follow_score, tweet_score] if s is not None]
            if not scores:
                return None

            return {"score": _clamp(sum(scores) / len(scores))}

        except Exception as e:
            logger.warning(f"fetch_xueqiu_heat_data failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Aggregate collection
    # ------------------------------------------------------------------

    async def collect_all_metrics(self, stock_code: str = None) -> Dict:
        """Concurrently collect all aggregate sentiment metrics.

        Each source is independently try/excepted; failure returns None for that source.

        Returns:
            {
                'baidu_vote_score': float | None,
                'akshare_aggregate_score': float | None,
                'news_sentiment_score': float | None,
                'margin_trading_score': float | None,
                'xueqiu_heat': float | None,
                'source_availability': {source_id: bool}
            }
        """
        results: Dict = {
            "baidu_vote_score": None,
            "akshare_aggregate_score": None,
            "news_sentiment_score": None,
            "margin_trading_score": None,
            "xueqiu_heat": None,
            "source_availability": {},
        }

        # Build tasks
        tasks = {}

        if stock_code:
            tasks["baidu_vote"] = self.fetch_baidu_vote(stock_code)
        tasks["akshare_aggregate"] = self.fetch_akshare_comment_metrics(stock_code)
        tasks["news_sentiment"] = self.fetch_news_sentiment_index()
        tasks["margin_trading"] = self.fetch_margin_trading_data(stock_code)
        tasks["xueqiu_heat"] = self.fetch_xueqiu_heat_data(stock_code)

        # Run concurrently
        task_keys = list(tasks.keys())
        task_coros = list(tasks.values())

        gathered = await asyncio.gather(*task_coros, return_exceptions=True)

        for key, result in zip(task_keys, gathered):
            if isinstance(result, Exception):
                logger.warning(f"collect_all_metrics: {key} raised {result}")
                results["source_availability"][key] = False
                continue

            if result is not None and isinstance(result, dict):
                score = result.get("score")
                if score is not None:
                    score = _clamp(float(score))

                if key == "baidu_vote":
                    results["baidu_vote_score"] = score
                elif key == "akshare_aggregate":
                    results["akshare_aggregate_score"] = score
                elif key == "news_sentiment":
                    results["news_sentiment_score"] = score
                elif key == "margin_trading":
                    results["margin_trading_score"] = score
                elif key == "xueqiu_heat":
                    results["xueqiu_heat"] = score

                results["source_availability"][key] = True
            else:
                results["source_availability"][key] = False

        return results

    # ------------------------------------------------------------------
    # Weighted index calculation
    # ------------------------------------------------------------------

    def calculate_weighted_index(
        self,
        comment_score: Optional[float],
        metrics: Dict,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """Calculate composite sentiment index using weighted model.

        Args:
            comment_score: Comment sentiment score from LLM analysis (0-100), or None.
            metrics: Output of collect_all_metrics().
            custom_weights: Optional user-defined weights overriding defaults.

        Returns:
            {
                'index_value': float,           # Composite index (0-100)
                'comment_sentiment_score': float | None,
                'baidu_vote_score': float | None,
                'akshare_aggregate_score': float | None,
                'news_sentiment_score': float | None,
                'margin_trading_score': float | None,
                'effective_weights': dict,       # Actual weights after redistribution
                'source_availability': dict,
            }
        """
        weights = custom_weights if custom_weights is not None else self.weights

        # Map source keys to their scores
        score_map: Dict[str, Optional[float]] = {
            "comment_sentiment": comment_score,
            "baidu_vote": metrics.get("baidu_vote_score"),
            "akshare_aggregate": metrics.get("akshare_aggregate_score"),
            "news_sentiment": metrics.get("news_sentiment_score"),
            "margin_trading": metrics.get("margin_trading_score"),
        }

        # Collect available sources
        available_scores: Dict[str, float] = {}
        total_available_weight = 0.0

        for key, score in score_map.items():
            if score is not None:
                available_scores[key] = float(score)
                total_available_weight += weights.get(key, 0.0)

        # Weight redistribution: scale available weights so they sum to 1.0
        effective_weights: Dict[str, float] = {}
        if available_scores and total_available_weight > 0:
            scale = 1.0 / total_available_weight
            effective_weights = {k: weights.get(k, 0.0) * scale for k in available_scores}
        elif available_scores:
            # All available sources have zero weight — distribute equally
            equal_w = 1.0 / len(available_scores)
            effective_weights = {k: equal_w for k in available_scores}

        # Weighted sum
        if effective_weights:
            index_value = sum(
                available_scores[k] * effective_weights[k]
                for k in available_scores
            )
        else:
            index_value = 50.0  # Default neutral when no data available

        return {
            "index_value": _clamp(index_value),
            "comment_sentiment_score": comment_score,
            "baidu_vote_score": metrics.get("baidu_vote_score"),
            "akshare_aggregate_score": metrics.get("akshare_aggregate_score"),
            "news_sentiment_score": metrics.get("news_sentiment_score"),
            "margin_trading_score": metrics.get("margin_trading_score"),
            "effective_weights": effective_weights,
            "source_availability": metrics.get("source_availability", {}),
        }

    # ------------------------------------------------------------------
    # Weight management
    # ------------------------------------------------------------------

    def update_weights(self, new_weights: Dict[str, float]):
        """Update weight configuration (called from settings page)."""
        self.weights.update(new_weights)
