"""
IP Proxy Pool Manager for sentiment crawlers.

Manages HTTP/SOCKS5 proxy rotation with failure tracking.
When all proxies fail, falls back to direct connection (returns None).

Requirements: 9.5
"""

import random
from typing import List, Optional, Set


class ProxyPoolManager:
    """IP proxy pool manager supporting HTTP/SOCKS5 proxy rotation."""

    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies: List[str] = list(proxies) if proxies else []
        self.failed_proxies: Set[str] = set()

    def get_random_proxy(self) -> Optional[str]:
        """Pick a random available proxy, excluding failed ones.

        Returns None when no proxies are configured or all have failed
        (fallback to direct connection).
        """
        available = [p for p in self.proxies if p not in self.failed_proxies]
        if not available:
            return None
        return random.choice(available)

    def mark_failed(self, proxy: str) -> None:
        """Mark a proxy as failed so it won't be returned again."""
        self.failed_proxies.add(proxy)

    def reset_failed(self) -> None:
        """Reset the failed proxy set, giving all proxies another chance."""
        self.failed_proxies.clear()

    @property
    def available_count(self) -> int:
        """Number of proxies currently available (not failed)."""
        return len([p for p in self.proxies if p not in self.failed_proxies])

    @property
    def total_count(self) -> int:
        """Total number of configured proxies."""
        return len(self.proxies)
