"""
Adaptive Rate Controller for sentiment crawlers.

Detects anti-crawl signals (HTTP 403/429, captcha pages, empty responses)
and dynamically adjusts request cooldown per source. Cooldown doubles on
detection (capped at 60s) and recovers to base after 3 consecutive successes.

Requirements: 9.6
"""

from typing import Dict


class AdaptiveRateController:
    """Request frequency adaptive controller with per-source state."""

    MAX_COOLDOWN = 60.0  # seconds

    def __init__(self, base_cooldown: float = 2.0):
        self.base_cooldown = base_cooldown
        self.current_cooldown: Dict[str, float] = {}
        self.consecutive_success: Dict[str, int] = {}

    def detect_anti_crawl(self, status_code: int, response_body: str) -> bool:
        """Return True if the response indicates an anti-crawl signal.

        Signals:
        - HTTP 403 Forbidden / 429 Too Many Requests
        - Response body contains captcha keywords
        - Empty response body
        """
        if status_code in (403, 429):
            return True
        if "验证码" in response_body or "captcha" in response_body.lower():
            return True
        if len(response_body.strip()) == 0:
            return True
        return False

    def on_anti_crawl_detected(self, source: str) -> None:
        """Double the cooldown for *source* (capped at MAX_COOLDOWN).

        Resets the consecutive success counter.
        """
        current = self.current_cooldown.get(source, self.base_cooldown)
        self.current_cooldown[source] = min(current * 2, self.MAX_COOLDOWN)
        self.consecutive_success[source] = 0

    def on_success(self, source: str) -> None:
        """Record a successful request. After 3 consecutive successes,
        restore cooldown to base_cooldown.
        """
        self.consecutive_success[source] = self.consecutive_success.get(source, 0) + 1
        if self.consecutive_success[source] >= 3:
            self.current_cooldown[source] = self.base_cooldown

    def get_cooldown(self, source: str) -> float:
        """Get the current cooldown interval for *source*."""
        return self.current_cooldown.get(source, self.base_cooldown)
