"""Foreign news crawler service.

Goal: provide a MediaCrawlerService-like interface for foreign platforms that are easiest to crawl
and (ideally) include comment content.

Initial supported platform:
- hn (Hacker News): search via Algolia, comments via official Firebase item API.
"""

from __future__ import annotations

import asyncio
import html
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx


_TAG_RE = re.compile(r"<[^>]+>")
_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_SPACE_RE = re.compile(r"\s+")


_HN_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "about",
    "latest",
    "new",
    "news",
    "trend",
    "trends",
    "analysis",
    "analyze",
    "overview",
    "update",
    "updates",
    "report",
    "reports",
    "insight",
    "insights",
    "dynamic",
    "dynamics",
    "industry",
}


def _strip_html(text: str) -> str:
    if not text:
        return ""
    # HN comment text is HTML.
    text = html.unescape(text)
    text = _TAG_RE.sub("", text)
    # Normalize whitespace.
    text = text.replace("\r", "").strip()
    return text


@dataclass(frozen=True)
class HackerNewsStory:
    story_id: str
    title: str
    url: str
    author: str
    created_at_i: int
    points: int
    num_comments: int


class ForeignNewsCrawlerService:
    """Crawl foreign news/discussion platforms by topic."""

    PLATFORM_MAP = {
        "hn": "hn",
        "nh": "hn",
        "hackernews": "hn",
        "hacker_news": "hn",
        "reddit": "reddit",
        "r": "reddit",
    }

    def __init__(self) -> None:
        self._reddit_token: Optional[str] = None
        self._reddit_token_expires_at: float = 0.0
        self._reddit_lock = asyncio.Lock()

    def _normalize_platform(self, platform: str) -> str:
        return self.PLATFORM_MAP.get(platform.lower(), platform.lower())

    async def crawl_platform(
        self,
        platform: str,
        keywords: str,
        max_items: int = 20,
        max_comments: int = 20,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        normalized = self._normalize_platform(platform)
        if normalized not in {"hn", "reddit"}:
            raise ValueError(f"Unsupported foreign platform: {platform}")

        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            if normalized == "hn":
                stories = await self._hn_search_stories(client, keywords, max_items=max_items)
                results: List[Dict[str, Any]] = []

                # Fetch comments with modest concurrency.
                sem = asyncio.Semaphore(6)

                async def fetch_one(story: HackerNewsStory) -> Dict[str, Any]:
                    async with sem:
                        comments = await self._hn_fetch_top_comments(
                            client, story.story_id, max_comments=max_comments
                        )
                        return self._standardize_hn_story(story, comments)

                tasks = [fetch_one(s) for s in stories]
                for coro in asyncio.as_completed(tasks):
                    try:
                        results.append(await coro)
                    except Exception:
                        continue

                story_index = {s.story_id: i for i, s in enumerate(stories)}
                results.sort(
                    key=lambda x: story_index.get(x.get("content_id", ""), 10**9)
                )
                return results

            # Reddit
            posts = await self._reddit_search_posts(client, keywords, max_items=max_items)
            results: List[Dict[str, Any]] = []

            sem = asyncio.Semaphore(4)

            async def fetch_one(post: Dict[str, Any]) -> Dict[str, Any]:
                async with sem:
                    comments = await self._reddit_fetch_top_comments(
                        client, post_id=str(post.get("id") or ""), max_comments=max_comments
                    )
                    return self._standardize_reddit_post(post, comments)

            tasks = [fetch_one(p) for p in posts]
            for coro in asyncio.as_completed(tasks):
                try:
                    results.append(await coro)
                except Exception:
                    continue

            post_index = {str(p.get("id") or ""): i for i, p in enumerate(posts)}
            results.sort(key=lambda x: post_index.get(x.get("content_id", ""), 10**9))
            return results

    async def _hn_search_stories(
        self, client: httpx.AsyncClient, keywords: str, max_items: int
    ) -> List[HackerNewsStory]:
        # Algolia provides HN search (no key required).
        # We use a hybrid strategy: combine relevance-ranked results (search)
        # with newest-ranked results (search_by_date), then blend-rank.

        # HN queries are sensitive to phrasing. Long natural-language sentences
        # often return 0 hits. We'll try a few fallback keyword queries.
        queries = self._hn_build_queries(keywords)

        hits_per_page = min(100, max(1, int(max_items)))
        fetch_target = max_items

        async def fetch_algolia(endpoint: str, query: str) -> List[Dict[str, Any]]:
            # Grab a bit extra from each list to have room for de-dupe.
            per_source_target = max(fetch_target, int(fetch_target * 1.5))
            url = f"https://hn.algolia.com/api/v1/{endpoint}"
            hits: List[Dict[str, Any]] = []
            page = 0
            seen_pages = 0
            while len(hits) < per_source_target:
                params = {
                    "query": query,
                    "tags": "story",
                    "hitsPerPage": str(hits_per_page),
                    "page": str(page),
                }
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json() or {}
                page_hits = data.get("hits", []) or []
                if not page_hits:
                    break
                hits.extend(page_hits)
                nb_pages = int(data.get("nbPages") or 0)
                page += 1
                seen_pages += 1
                if nb_pages and page >= nb_pages:
                    break
                if seen_pages >= 10:
                    break
            return hits

        def to_story(hit: Dict[str, Any]) -> Optional[HackerNewsStory]:
            story_id = str(hit.get("objectID") or "").strip()
            if not story_id:
                return None
            title = (hit.get("title") or "").strip()
            story_url = (hit.get("url") or "").strip()
            if not story_url:
                story_url = f"https://news.ycombinator.com/item?id={story_id}"
            author = (hit.get("author") or "").strip()
            created_at_i = int(hit.get("created_at_i") or 0)
            points = int(hit.get("points") or 0)
            num_comments = int(hit.get("num_comments") or 0)
            return HackerNewsStory(
                story_id=story_id,
                title=title,
                url=story_url,
                author=author,
                created_at_i=created_at_i,
                points=points,
                num_comments=num_comments,
            )

        aggregated: List[HackerNewsStory] = []
        seen_story_ids: set[str] = set()

        for q_index, query in enumerate(queries):
            relevance_hits, recent_hits = await asyncio.gather(
                fetch_algolia("search", query),
                fetch_algolia("search_by_date", query),
            )

            # If the original query yields nothing, try fallbacks.
            if q_index == 0 and not relevance_hits and not recent_hits and len(queries) > 1:
                print(f"[HN] Query returned 0 hits, trying fallbacks: {queries[1:]} ")

            # Build rank maps.
            rel_rank: Dict[str, int] = {}
            for idx, hit in enumerate(relevance_hits):
                sid = str(hit.get("objectID") or "").strip()
                if sid and sid not in rel_rank:
                    rel_rank[sid] = idx
            rec_rank: Dict[str, int] = {}
            for idx, hit in enumerate(recent_hits):
                sid = str(hit.get("objectID") or "").strip()
                if sid and sid not in rec_rank:
                    rec_rank[sid] = idx

            combined_ids = set(rel_rank) | set(rec_rank)
            combined: List[Tuple[float, HackerNewsStory]] = []

            w_rel = 0.55
            w_new = 0.45

            hit_by_id: Dict[str, Dict[str, Any]] = {}
            for hit in recent_hits:
                sid = str(hit.get("objectID") or "").strip()
                if sid and sid not in hit_by_id:
                    hit_by_id[sid] = hit
            for hit in relevance_hits:
                sid = str(hit.get("objectID") or "").strip()
                if sid:
                    hit_by_id[sid] = hit

            for sid in combined_ids:
                hit = hit_by_id.get(sid)
                if not hit:
                    continue
                story = to_story(hit)
                if not story:
                    continue
                rr = rel_rank.get(sid)
                nr = rec_rank.get(sid)
                score = 0.0
                if rr is not None:
                    score += w_rel / (1.0 + rr)
                if nr is not None:
                    score += w_new / (1.0 + nr)
                combined.append((score, story))

            combined.sort(key=lambda x: (x[0], x[1].created_at_i), reverse=True)

            for _, story in combined:
                if story.story_id in seen_story_ids:
                    continue
                seen_story_ids.add(story.story_id)
                aggregated.append(story)
                if len(aggregated) >= max_items:
                    return aggregated[:max_items]

        return aggregated[:max_items]

    def _hn_build_queries(self, keywords: str) -> List[str]:
        raw = (keywords or "").strip()
        raw = _SPACE_RE.sub(" ", raw)
        if not raw:
            return []

        queries: List[str] = [raw]

        # If user passes a full sentence, keywordize it.
        words = [w for w in _WORD_RE.findall(raw) if w]
        lowered = [w.lower() for w in words]
        kept = [w for w, lw in zip(words, lowered) if lw not in _HN_STOPWORDS]

        # Extract core entities (proper nouns - capitalized words) and key action words
        # This helps with cases like "Trump Venezuela Maduro capture"
        proper_nouns = [w for w in words if w[0].isupper() and len(w) > 1]  # Capitalized words (likely names/entities)
        action_words = [w for w in kept if w.lower() not in ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been']]
        
        # Build queries with different combinations for better recall
        if len(words) >= 3:
            # Query 1: All proper nouns (entities) - highest priority
            if proper_nouns:
                entity_query = " ".join(proper_nouns[:5])
                if entity_query and entity_query.lower() != raw.lower():
                    queries.append(entity_query)
            
            # Query 2: Proper nouns + key action words
            if proper_nouns and action_words:
                combined = " ".join(proper_nouns[:3] + action_words[:2])
                if combined and combined.lower() != raw.lower():
                    queries.append(combined)
            
            # Query 3: Condensed version (original logic)
            if kept:
                condensed = " ".join(kept[:8])
                if condensed and condensed.lower() != raw.lower():
                    queries.append(condensed)
            
            # Query 4: Individual proper nouns (for very specific searches)
            if len(proper_nouns) > 1:
                for pn in proper_nouns[:3]:  # Try each major entity separately
                    if pn.lower() not in [q.lower() for q in queries]:
                        queries.append(pn)

        # EV synonym expansion: many posts use “electric vehicle(s)”.
        has_ev = any(lw == "ev" or lw.startswith("evs") for lw in lowered)
        if has_ev:
            queries.append("electric vehicles")
            queries.append("electric vehicle")
            # If the raw query contains 'EV', replace it.
            queries.append(re.sub(r"\bEV\b", "electric vehicles", raw, flags=re.IGNORECASE))

        # A generally high-recall fallback for this domain.
        if any(lw in {"vehicle", "vehicles", "electric"} for lw in lowered) or has_ev:
            queries.append("EV")

        # De-dupe while preserving order.
        seen: set[str] = set()
        out: List[str] = []
        for q in queries:
            q2 = _SPACE_RE.sub(" ", (q or "").strip())
            if not q2:
                continue
            key = q2.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(q2)
        return out

    async def _hn_fetch_item(self, client: httpx.AsyncClient, item_id: str) -> Optional[Dict[str, Any]]:
        url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def _hn_fetch_top_comments(
        self,
        client: httpx.AsyncClient,
        story_id: str,
        max_comments: int,
    ) -> List[Dict[str, Any]]:
        if max_comments <= 0:
            return []

        story = await self._hn_fetch_item(client, story_id)
        if not story:
            return []

        kids = story.get("kids") or []
        if not kids:
            return []

        collected: List[Dict[str, Any]] = []
        queue: List[Tuple[str, int]] = [(str(k), 1) for k in kids]
        seen: set[str] = set()

        # Batched BFS (approx) so we keep top-level-ish order but fetch faster.
        batch_size = 10
        max_depth = 6

        while queue and len(collected) < max_comments:
            batch: List[Tuple[str, int]] = []
            while queue and len(batch) < batch_size and len(collected) + len(batch) < max_comments:
                item_id, depth = queue.pop(0)
                if depth > max_depth:
                    continue
                if item_id in seen:
                    continue
                seen.add(item_id)
                batch.append((item_id, depth))

            if not batch:
                continue

            async def fetch_one(item_id: str) -> Optional[Dict[str, Any]]:
                try:
                    return await self._hn_fetch_item(client, item_id)
                except Exception:
                    return None

            items = await asyncio.gather(*[fetch_one(i) for i, _ in batch])

            for (item_id, depth), item in zip(batch, items):
                if len(collected) >= max_comments:
                    break
                if not item:
                    continue
                if item.get("deleted") or item.get("dead"):
                    continue
                if item.get("type") != "comment":
                    continue

                text = _strip_html(item.get("text") or "")
                if not text:
                    continue

                collected.append(
                    {
                        "id": str(item.get("id") or item_id),
                        "author": item.get("by") or "",
                        "text": text,
                        "time": str(item.get("time") or ""),
                        "parent": str(item.get("parent") or ""),
                        "depth": depth,
                    }
                )

                for child in item.get("kids") or []:
                    if len(collected) >= max_comments:
                        break
                    queue.append((str(child), depth + 1))

        return collected

    def _standardize_hn_story(self, story: HackerNewsStory, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        comment_lines = []
        for c in comments:
            author = c.get("author") or ""
            text = c.get("text") or ""
            if author:
                comment_lines.append(f"- {author}: {text}")
            else:
                comment_lines.append(f"- {text}")

        content_parts = [story.title]
        if comment_lines:
            content_parts.append("\nComments:\n" + "\n".join(comment_lines))

        return {
            "platform": "hn",
            "content_id": story.story_id,
            "title": story.title,
            "content": "\n".join(content_parts).strip(),
            "author": {
                "user_id": story.author,
                "nickname": story.author,
                "avatar": "",
            },
            "interactions": {
                "liked_count": story.points,
                "comment_count": story.num_comments,
                "share_count": 0,
                "collected_count": 0,
            },
            "timestamp": str(story.created_at_i),
            "url": story.url,
            "raw_data": {
                "story": {
                    "id": story.story_id,
                    "title": story.title,
                    "url": story.url,
                    "author": story.author,
                    "created_at_i": story.created_at_i,
                    "points": story.points,
                    "num_comments": story.num_comments,
                },
                "comments": comments,
            },
        }

    # -------------------- Reddit --------------------

    def _reddit_user_agent(self) -> str:
        ua = (os.getenv("REDDIT_USER_AGENT") or "").strip()
        if not ua:
            raise RuntimeError(
                "Missing REDDIT_USER_AGENT. Set it in .env, e.g. 'AgentPro/1.0 by u/yourname'."
            )
        return ua

    async def _reddit_get_token(self, client: httpx.AsyncClient) -> str:
        async with self._reddit_lock:
            now = time.time()
            if self._reddit_token and now < self._reddit_token_expires_at:
                return self._reddit_token

            client_id = (os.getenv("REDDIT_CLIENT_ID") or "").strip()
            client_secret = (os.getenv("REDDIT_CLIENT_SECRET") or "").strip()
            if not client_id or not client_secret:
                raise RuntimeError(
                    "Missing Reddit credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env."
                )

            headers = {
                "User-Agent": self._reddit_user_agent(),
            }
            data = {
                "grant_type": "client_credentials",
            }
            resp = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                headers=headers,
                data=data,
                auth=(client_id, client_secret),
            )
            if resp.status_code in {401, 403}:
                raise RuntimeError(
                    "Reddit OAuth denied (401/403). Reddit has started requiring approval for NEW OAuth access in many cases. "
                    "If you don't already have working API access, you'll need to request approval per the Responsible Builder Policy/Devvit flow. "
                    f"Raw response: {resp.status_code} {resp.text}"
                )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Reddit token request failed: {resp.status_code} {resp.text}"
                )
            payload = resp.json()
            token = (payload.get("access_token") or "").strip()
            expires_in = int(payload.get("expires_in") or 0)
            if not token:
                raise RuntimeError(f"Reddit token missing in response: {payload}")

            # Refresh 30s early.
            self._reddit_token = token
            self._reddit_token_expires_at = time.time() + max(0, expires_in - 30)
            return token

    async def _reddit_get(
        self,
        client: httpx.AsyncClient,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        token = await self._reddit_get_token(client)
        headers = {
            "Authorization": f"bearer {token}",
            "User-Agent": self._reddit_user_agent(),
            "Accept": "application/json",
        }
        url = f"https://oauth.reddit.com{path}"
        resp = await client.get(url, headers=headers, params=params)

        # Token can occasionally expire earlier; retry once.
        if resp.status_code == 401:
            async with self._reddit_lock:
                self._reddit_token = None
                self._reddit_token_expires_at = 0.0
            token = await self._reddit_get_token(client)
            headers["Authorization"] = f"bearer {token}"
            resp = await client.get(url, headers=headers, params=params)

        resp.raise_for_status()
        return resp.json()

    async def _reddit_search_posts(
        self, client: httpx.AsyncClient, keywords: str, max_items: int
    ) -> List[Dict[str, Any]]:
        params = {
            "q": keywords,
            "limit": str(max_items),
            "sort": "relevance",
            "t": "week",
            "type": "link",
            "raw_json": "1",
        }
        data = await self._reddit_get(client, "/search", params=params)
        children = (((data or {}).get("data") or {}).get("children") or [])
        posts: List[Dict[str, Any]] = []
        for child in children[:max_items]:
            if not isinstance(child, dict):
                continue
            if child.get("kind") != "t3":
                continue
            post = child.get("data") or {}
            if post.get("over_18"):
                # Keep it simple: skip NSFW by default.
                continue
            if not post.get("id"):
                continue
            posts.append(post)
        return posts

    async def _reddit_fetch_top_comments(
        self, client: httpx.AsyncClient, post_id: str, max_comments: int
    ) -> List[Dict[str, Any]]:
        if not post_id or max_comments <= 0:
            return []

        params = {
            "limit": str(max_comments),
            "depth": "2",
            "sort": "top",
            "raw_json": "1",
        }
        data = await self._reddit_get(client, f"/comments/{post_id}", params=params)
        if not isinstance(data, list) or len(data) < 2:
            return []

        comments_listing = data[1] or {}
        children = (((comments_listing.get("data") or {}).get("children")) or [])

        collected: List[Dict[str, Any]] = []

        def walk(items: List[Dict[str, Any]], depth: int) -> None:
            nonlocal collected
            for it in items:
                if len(collected) >= max_comments:
                    return
                if not isinstance(it, dict):
                    continue
                kind = it.get("kind")
                if kind != "t1":
                    continue
                d = it.get("data") or {}
                body = (d.get("body") or "").strip()
                if not body:
                    continue
                collected.append(
                    {
                        "id": str(d.get("id") or ""),
                        "author": d.get("author") or "",
                        "text": body,
                        "time": str(d.get("created_utc") or ""),
                        "depth": depth,
                        "score": int(d.get("score") or 0),
                    }
                )
                replies = d.get("replies")
                if (
                    replies
                    and isinstance(replies, dict)
                    and (replies.get("data") or {}).get("children")
                    and len(collected) < max_comments
                ):
                    walk((replies.get("data") or {}).get("children") or [], depth + 1)

        walk(children, 1)
        return collected

    def _standardize_reddit_post(
        self, post: Dict[str, Any], comments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        post_id = str(post.get("id") or "")
        title = (post.get("title") or "").strip()
        selftext = (post.get("selftext") or "").strip()
        author = (post.get("author") or "").strip()
        permalink = (post.get("permalink") or "").strip()
        url = f"https://www.reddit.com{permalink}" if permalink else (post.get("url") or "")

        comment_lines = []
        for c in comments:
            a = c.get("author") or ""
            t = c.get("text") or ""
            if a:
                comment_lines.append(f"- {a}: {t}")
            else:
                comment_lines.append(f"- {t}")

        content_parts = [title]
        if selftext:
            content_parts.append(selftext)
        if comment_lines:
            content_parts.append("\nComments:\n" + "\n".join(comment_lines))

        return {
            "platform": "reddit",
            "content_id": post_id,
            "title": title,
            "content": "\n\n".join([p for p in content_parts if p]).strip(),
            "author": {
                "user_id": author,
                "nickname": author,
                "avatar": "",
            },
            "interactions": {
                "liked_count": int(post.get("ups") or 0),
                "comment_count": int(post.get("num_comments") or 0),
                "share_count": 0,
                "collected_count": 0,
            },
            "timestamp": str(post.get("created_utc") or ""),
            "url": url or "",
            "raw_data": {
                "post": post,
                "comments": comments,
            },
        }


foreign_crawler_service = ForeignNewsCrawlerService()
