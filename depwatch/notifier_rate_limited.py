"""Wrapper around notifier that applies rate limiting before dispatching."""

from __future__ import annotations

import logging
from typing import Optional

from depwatch.notifier import NotifierConfig, notify_log, notify_webhook, notify_email
from depwatch.rate_limiter import RateLimiter, RateLimitConfig
from depwatch.scanner import ScanResult

logger = logging.getLogger(__name__)


def _dispatch(channel: str, config: NotifierConfig, result: ScanResult) -> bool:
    """Send via the appropriate backend; return True on success."""
    if channel == "log":
        notify_log(config, result)
        return True
    if channel == "webhook":
        return notify_webhook(config, result)
    if channel == "email":
        return notify_email(config, result)
    logger.warning("Unknown channel: %s", channel)
    return False


class RateLimitedNotifier:
    """Notifier that silently drops alerts that exceed the rate limit."""

    def __init__(
        self,
        notifier_config: NotifierConfig,
        rate_config: Optional[RateLimitConfig] = None,
    ) -> None:
        self._ncfg = notifier_config
        self._limiter = RateLimiter(rate_config)

    def notify(self, channel: str, result: ScanResult) -> bool:
        """
        Attempt to send *result* via *channel*.

        Returns True if the alert was dispatched, False if rate-limited.
        """
        if result.is_empty():
            return False

        if not self._limiter.is_allowed(channel):
            logger.info(
                "Rate limit reached for channel '%s'; alert suppressed.", channel
            )
            return False

        sent = _dispatch(channel, self._ncfg, result)
        if sent:
            self._limiter.record(channel)
        return sent

    def remaining(self, channel: str) -> int:
        """Remaining alert budget for *channel* in the current window."""
        return self._limiter.remaining(channel)

    def reset(self, channel: str) -> None:
        """Reset rate-limit counters for *channel* (e.g. after config reload)."""
        self._limiter.reset(channel)
