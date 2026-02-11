"""
Cookie Pool Manager for sentiment crawlers.

Maintains multiple sets of cookies per data source, rotating through them
on each request. Invalid cookies are excluded from rotation.

Requirements: 9.7
"""

from typing import Dict, List, Optional


class CookiePoolManager:
    """Cookie pool manager with per-source rotation and invalidation tracking."""

    def __init__(self):
        # source -> list of cookie dicts
        self.cookie_pool: Dict[str, List[Dict]] = {}
        # source -> list of validity flags (parallel to cookie_pool)
        self.cookie_status: Dict[str, List[bool]] = {}
        # source -> round-robin index
        self._rotation_index: Dict[str, int] = {}

    def add_cookies(self, source: str, cookies: List[Dict]) -> None:
        """Add a batch of cookies for a given source."""
        if source not in self.cookie_pool:
            self.cookie_pool[source] = []
            self.cookie_status[source] = []
            self._rotation_index[source] = 0

        for cookie in cookies:
            self.cookie_pool[source].append(cookie)
            self.cookie_status[source].append(True)

    def get_cookie(self, source: str) -> Optional[Dict]:
        """Get the next valid cookie for *source* via round-robin.

        Returns None when no valid cookies are available for the source.
        """
        pool = self.cookie_pool.get(source, [])
        status = self.cookie_status.get(source, [])
        if not pool:
            return None

        n = len(pool)
        start = self._rotation_index.get(source, 0) % n

        # Scan up to n positions looking for a valid cookie
        for offset in range(n):
            idx = (start + offset) % n
            if status[idx]:
                # Advance rotation index past this one for next call
                self._rotation_index[source] = (idx + 1) % n
                return pool[idx]

        return None

    def mark_invalid(self, source: str, index: int) -> None:
        """Mark the cookie at *index* for *source* as invalid."""
        status = self.cookie_status.get(source, [])
        if 0 <= index < len(status):
            status[index] = False

    def valid_count(self, source: str) -> int:
        """Number of valid cookies for *source*."""
        return sum(1 for v in self.cookie_status.get(source, []) if v)

    def total_count(self, source: str) -> int:
        """Total cookies configured for *source*."""
        return len(self.cookie_pool.get(source, []))
