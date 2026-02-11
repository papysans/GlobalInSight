"""
Sentiment Crawler Service for collecting retail investor comments.

Integrates ProxyPoolManager, CookiePoolManager, and AdaptiveRateController
to crawl comments from Eastmoney (东方财富股吧), Xueqiu (雪球), and
10jqka (同花顺) with anti-crawl resilience.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9
"""

import asyncio
import hashlib
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx
from loguru import logger

from app.schemas import SentimentComment, SentimentSourceStatus
from app.services.proxy_pool_manager import ProxyPoolManager
from app.services.cookie_pool_manager import CookiePoolManager
from app.services.adaptive_rate_controller import AdaptiveRateController


# Default spam keywords blacklist
DEFAULT_SPAM_KEYWORDS: List[str] = [
    "加微信", "加群", "免费荐股", "保证赚", "稳赚不赔",
    "内幕消息", "私募", "代操盘", "开户优惠", "低佣金",
    "点击链接", "扫码", "VX:", "wx:", "Q群",
]

# Regex for pure emoji / pure symbol comments (no meaningful text)
_PURE_EMOJI_SYMBOL_RE = re.compile(
    r"^[\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
    r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
    r"\U00002702-\U000027B0\U000024C2-\U0001F251"
    r"\U0000FE00-\U0000FE0F\U0000200D"
    r"!@#$%^&*()_+=\-\[\]{};':\"\\|,.<>/?~`"
    r"！@#￥%……&*（）——+=\-【】{}；'：""\\|，。《》？～·"
    r"\u3000-\u303F\uFF00-\uFFEF]+$"
)

# User-Agent rotation pool
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]


def _content_hash(text: str) -> str:
    """Generate MD5 hash for comment content deduplication."""
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_within_time_window(published_time: str, time_window_hours: int) -> bool:
    """Check if a published_time string falls within the time window."""
    try:
        if published_time.endswith("Z"):
            published_time = published_time.replace("Z", "+00:00")
        pub_dt = datetime.fromisoformat(published_time)
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        return pub_dt >= cutoff
    except (ValueError, TypeError):
        return False


class SentimentCrawler:
    """Retail investor sentiment comment crawler service.

    Collects comments from Eastmoney, Xueqiu, and 10jqka with:
    - Proxy pool rotation (ProxyPoolManager)
    - Cookie pool rotation (CookiePoolManager)
    - Adaptive rate control (AdaptiveRateController)
    - Source ban/degradation on repeated failures
    - Incremental collection (time window filtering)
    - Comment cleaning (emoji/symbol removal, spam filtering, dedup)
    """

    # Ban duration in minutes when a source hits consecutive failures
    BAN_DURATION_MINUTES = 30
    # Number of consecutive failures before banning a source
    MAX_CONSECUTIVE_FAILURES = 3

    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        spam_keywords: Optional[List[str]] = None,
        base_cooldown: float = 2.0,
    ):
        self.proxy_pool = ProxyPoolManager(proxies=proxies)
        self.cookie_pool = CookiePoolManager()
        self.rate_controller = AdaptiveRateController(base_cooldown=base_cooldown)

        # Source ban tracking
        self.source_ban_until: Dict[str, float] = {}
        self.source_fail_count: Dict[str, int] = {}

        # Source success/total tracking for status reporting
        self.source_success_count: Dict[str, int] = {}
        self.source_total_count: Dict[str, int] = {}
        self.source_last_collected: Dict[str, str] = {}
        self.source_last_comment_count: Dict[str, int] = {}

        # Spam keywords
        self.spam_keywords: List[str] = list(spam_keywords) if spam_keywords else list(DEFAULT_SPAM_KEYWORDS)

        # Source ID to fetch method mapping
        self._source_fetchers = {
            "eastmoney": self.fetch_eastmoney_comments,
            "xueqiu": self.fetch_xueqiu_comments,
            "10jqka": self.fetch_10jqka_comments,
        }

    # ------------------------------------------------------------------
    # Ban / degradation logic
    # ------------------------------------------------------------------

    def is_source_banned(self, source: str) -> bool:
        """Check if a source is currently banned (degraded)."""
        ban_until = self.source_ban_until.get(source, 0)
        return time.time() < ban_until

    def ban_source(self, source: str, duration_minutes: int = 30) -> None:
        """Ban a source for *duration_minutes*."""
        self.source_ban_until[source] = time.time() + duration_minutes * 60
        logger.warning(f"Source '{source}' banned for {duration_minutes} minutes")

    def _record_failure(self, source: str) -> None:
        """Record a failure for a source. Ban after MAX_CONSECUTIVE_FAILURES."""
        self.source_fail_count[source] = self.source_fail_count.get(source, 0) + 1
        self.source_total_count[source] = self.source_total_count.get(source, 0) + 1
        if self.source_fail_count[source] >= self.MAX_CONSECUTIVE_FAILURES:
            self.ban_source(source, self.BAN_DURATION_MINUTES)

    def _record_success(self, source: str) -> None:
        """Record a success, resetting the consecutive failure counter."""
        self.source_fail_count[source] = 0
        self.source_success_count[source] = self.source_success_count.get(source, 0) + 1
        self.source_total_count[source] = self.source_total_count.get(source, 0) + 1

    # ------------------------------------------------------------------
    # HTTP helper
    # ------------------------------------------------------------------

    async def _http_get(self, url: str, source: str, headers: Optional[Dict] = None,
                        params: Optional[Dict] = None, timeout: float = 15.0) -> Optional[httpx.Response]:
        """Perform an HTTP GET with proxy rotation, rate control, and anti-crawl detection."""
        cooldown = self.rate_controller.get_cooldown(source)
        await asyncio.sleep(cooldown)

        proxy = self.proxy_pool.get_random_proxy()
        ua_index = hash(source) % len(_USER_AGENTS)
        default_headers = {
            "User-Agent": _USER_AGENTS[ua_index],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if headers:
            default_headers.update(headers)

        # Merge cookie from pool if available
        cookie_dict = self.cookie_pool.get_cookie(source)
        if cookie_dict:
            cookie_str = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
            default_headers["Cookie"] = cookie_str

        try:
            transport = None
            if proxy:
                transport = httpx.AsyncHTTPTransport(proxy=proxy)

            async with httpx.AsyncClient(
                transport=transport,
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url, headers=default_headers, params=params)

                body_text = resp.text or ""
                if self.rate_controller.detect_anti_crawl(resp.status_code, body_text):
                    self.rate_controller.on_anti_crawl_detected(source)
                    if proxy:
                        self.proxy_pool.mark_failed(proxy)
                    self._record_failure(source)
                    logger.warning(f"Anti-crawl detected for '{source}' (status={resp.status_code})")
                    return None

                self.rate_controller.on_success(source)
                self._record_success(source)
                return resp

        except (httpx.HTTPError, httpx.TimeoutException, Exception) as exc:
            logger.error(f"HTTP error for '{source}': {exc}")
            if proxy:
                self.proxy_pool.mark_failed(proxy)
            self._record_failure(source)
            return None

    # ------------------------------------------------------------------
    # Eastmoney (东方财富股吧) crawler
    # ------------------------------------------------------------------

    async def fetch_eastmoney_comments(
        self,
        stock_code: Optional[str] = None,
        time_window_hours: int = 24,
    ) -> List[SentimentComment]:
        """Fetch comments from Eastmoney Guba (东方财富股吧).

        Uses HTTP scraping of the Guba post list API.
        stock_code=None fetches the general discussion board.
        """
        source = "eastmoney"
        comments: List[SentimentComment] = []

        # Eastmoney Guba API endpoint
        board_code = stock_code if stock_code else "zssh000001"  # Default: Shanghai Composite
        url = f"https://guba.eastmoney.com/interface/GetData"
        params = {
            "path": "newtopic/api",
            "type": "1",
            "code": board_code,
            "ps": "30",  # page size
            "p": "1",
        }

        try:
            resp = await self._http_get(url, source, params=params)
            if resp is None:
                return comments

            # Try to parse JSON response
            try:
                data = resp.json()
            except Exception:
                # Fallback: try to extract from HTML
                data = None

            if data and isinstance(data, dict):
                items = data.get("data", {}).get("list", []) if isinstance(data.get("data"), dict) else []
                for item in items:
                    pub_time = item.get("post_publish_time", "") or item.get("publish_time", "")
                    if not pub_time:
                        continue
                    if not _is_within_time_window(pub_time, time_window_hours):
                        continue

                    content = item.get("post_title", "") or item.get("post_content", "") or ""
                    if not content.strip():
                        continue

                    comments.append(SentimentComment(
                        id=f"em_{item.get('post_id', uuid.uuid4().hex[:8])}",
                        content=content.strip(),
                        source_platform=source,
                        stock_code=stock_code,
                        author_nickname=item.get("post_user", {}).get("user_nickname", "") if isinstance(item.get("post_user"), dict) else "",
                        published_time=pub_time,
                        content_hash=_content_hash(content),
                    ))

        except Exception as exc:
            logger.error(f"Eastmoney crawl error: {exc}")
            self._record_failure(source)

        self.source_last_collected[source] = _now_iso()
        self.source_last_comment_count[source] = len(comments)
        return comments

    # ------------------------------------------------------------------
    # Xueqiu (雪球) crawler
    # ------------------------------------------------------------------

    async def fetch_xueqiu_comments(
        self,
        stock_code: Optional[str] = None,
        time_window_hours: int = 24,
    ) -> List[SentimentComment]:
        """Fetch comments from Xueqiu (雪球社区).

        Requires Cookie + User-Agent rotation. Anti-crawl is strict.
        """
        source = "xueqiu"
        comments: List[SentimentComment] = []

        # Xueqiu API for stock timeline / general timeline
        if stock_code:
            symbol = f"SH{stock_code}" if stock_code.startswith("6") else f"SZ{stock_code}"
            url = f"https://xueqiu.com/query/v1/symbol/search/status.json"
            params = {"symbol": symbol, "count": "30", "comment": "0", "page": "1"}
        else:
            url = "https://xueqiu.com/statuses/hot/listV2.json"
            params = {"since_id": "-1", "max_id": "-1", "size": "30"}

        headers = {
            "Referer": "https://xueqiu.com/",
            "Origin": "https://xueqiu.com",
        }

        try:
            resp = await self._http_get(url, source, headers=headers, params=params)
            if resp is None:
                return comments

            try:
                data = resp.json()
            except Exception:
                data = None

            if data and isinstance(data, dict):
                items = data.get("list", []) or data.get("statuses", [])
                if not isinstance(items, list):
                    items = []

                for item in items:
                    # Xueqiu timestamps are in milliseconds
                    created_at = item.get("created_at", 0)
                    if isinstance(created_at, (int, float)) and created_at > 0:
                        pub_dt = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
                        pub_time = pub_dt.isoformat()
                    else:
                        pub_time = item.get("timeBefore", "")
                        if not pub_time:
                            continue

                    if not _is_within_time_window(pub_time, time_window_hours):
                        continue

                    # Extract text content (strip HTML tags)
                    text = item.get("text", "") or item.get("description", "") or ""
                    text = re.sub(r"<[^>]+>", "", text).strip()
                    if not text:
                        continue

                    user_info = item.get("user", {}) or {}
                    comments.append(SentimentComment(
                        id=f"xq_{item.get('id', uuid.uuid4().hex[:8])}",
                        content=text,
                        source_platform=source,
                        stock_code=stock_code,
                        author_nickname=user_info.get("screen_name", ""),
                        published_time=pub_time,
                        content_hash=_content_hash(text),
                    ))

        except Exception as exc:
            logger.error(f"Xueqiu crawl error: {exc}")
            self._record_failure(source)

        self.source_last_collected[source] = _now_iso()
        self.source_last_comment_count[source] = len(comments)
        return comments

    # ------------------------------------------------------------------
    # 10jqka (同花顺) crawler
    # ------------------------------------------------------------------

    async def fetch_10jqka_comments(
        self,
        stock_code: Optional[str] = None,
        time_window_hours: int = 24,
    ) -> List[SentimentComment]:
        """Fetch comments from 10jqka (同花顺社区).

        Requires JS reverse engineering for Cookie encryption.
        Initial version uses basic HTTP with cookie pool.
        """
        source = "10jqka"
        comments: List[SentimentComment] = []

        # 10jqka stock discussion API
        if stock_code:
            url = f"https://t.10jqka.com.cn/circle/stock/{stock_code}/"
        else:
            url = "https://t.10jqka.com.cn/circle/hotTopic/"

        headers = {
            "Referer": "https://t.10jqka.com.cn/",
        }

        try:
            resp = await self._http_get(url, source, headers=headers)
            if resp is None:
                return comments

            # 10jqka typically returns HTML; parse with regex for initial version
            html = resp.text or ""
            # Look for post items in the HTML
            post_pattern = re.compile(
                r'class="[^"]*article-content[^"]*"[^>]*>(.*?)</div>',
                re.DOTALL,
            )
            time_pattern = re.compile(
                r'class="[^"]*pub-time[^"]*"[^>]*>(.*?)</(?:span|div|time)',
                re.DOTALL,
            )

            contents = post_pattern.findall(html)
            times = time_pattern.findall(html)

            for i, content_html in enumerate(contents):
                text = re.sub(r"<[^>]+>", "", content_html).strip()
                if not text:
                    continue

                pub_time = ""
                if i < len(times):
                    raw_time = re.sub(r"<[^>]+>", "", times[i]).strip()
                    # Try to parse various time formats
                    try:
                        pub_dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                        pub_time = pub_dt.isoformat()
                    except ValueError:
                        pub_time = _now_iso()

                if pub_time and not _is_within_time_window(pub_time, time_window_hours):
                    continue

                comments.append(SentimentComment(
                    id=f"ths_{uuid.uuid4().hex[:8]}",
                    content=text,
                    source_platform=source,
                    stock_code=stock_code,
                    author_nickname="",
                    published_time=pub_time or _now_iso(),
                    content_hash=_content_hash(text),
                ))

        except Exception as exc:
            logger.error(f"10jqka crawl error: {exc}")
            self._record_failure(source)

        self.source_last_collected[source] = _now_iso()
        self.source_last_comment_count[source] = len(comments)
        return comments

    # ------------------------------------------------------------------
    # Comment cleaning
    # ------------------------------------------------------------------

    def clean_comments(self, comments: List[SentimentComment]) -> List[SentimentComment]:
        """Clean comments: remove pure emoji/symbol, spam, and duplicates.

        1. Remove pure emoji / pure symbol comments (no meaningful Chinese/English text)
        2. Remove comments containing spam keywords
        3. Deduplicate by content_hash
        """
        seen_hashes: set = set()
        cleaned: List[SentimentComment] = []

        for comment in comments:
            text = comment.content.strip()

            # Skip empty
            if not text:
                continue

            # Skip pure emoji / pure symbol
            if _PURE_EMOJI_SYMBOL_RE.match(text):
                continue

            # Skip spam
            text_lower = text.lower()
            if any(kw.lower() in text_lower for kw in self.spam_keywords):
                continue

            # Deduplicate by content_hash
            h = comment.content_hash or _content_hash(text)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

            cleaned.append(comment)

        return cleaned

    # ------------------------------------------------------------------
    # Collect from all sources
    # ------------------------------------------------------------------

    async def collect_comments(
        self,
        stock_code: Optional[str] = None,
        source_ids: Optional[List[str]] = None,
        time_window_hours: int = 24,
    ) -> List[SentimentComment]:
        """Collect comments from all enabled sources concurrently.

        Skips banned sources. Cleans and deduplicates the combined results.
        """
        if source_ids is None:
            source_ids = list(self._source_fetchers.keys())

        tasks = []
        active_sources = []
        for sid in source_ids:
            if sid not in self._source_fetchers:
                logger.warning(f"Unknown source: {sid}")
                continue
            if self.is_source_banned(sid):
                logger.info(f"Source '{sid}' is banned, skipping")
                continue
            active_sources.append(sid)
            fetcher = self._source_fetchers[sid]
            tasks.append(fetcher(stock_code=stock_code, time_window_hours=time_window_hours))

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_comments: List[SentimentComment] = []
        for sid, result in zip(active_sources, results):
            if isinstance(result, Exception):
                logger.error(f"Source '{sid}' raised exception: {result}")
                self._record_failure(sid)
                continue
            if isinstance(result, list):
                all_comments.extend(result)

        # Clean and deduplicate
        return self.clean_comments(all_comments)

    # ------------------------------------------------------------------
    # Source status reporting
    # ------------------------------------------------------------------

    def get_source_status(self) -> Dict[str, SentimentSourceStatus]:
        """Return the current status of each crawler source."""
        statuses: Dict[str, SentimentSourceStatus] = {}

        for source_id in self._source_fetchers:
            total = self.source_total_count.get(source_id, 0)
            success = self.source_success_count.get(source_id, 0)
            success_rate = success / total if total > 0 else 0.0

            if self.is_source_banned(source_id):
                status = "banned"
            elif self.rate_controller.get_cooldown(source_id) > self.rate_controller.base_cooldown:
                status = "throttled"
            else:
                status = "normal"

            statuses[source_id] = SentimentSourceStatus(
                source_id=source_id,
                source_type="crawler",
                last_collected=self.source_last_collected.get(source_id),
                success_rate=round(success_rate, 3),
                status=status,
                comment_count=self.source_last_comment_count.get(source_id, 0),
            )

        return statuses
