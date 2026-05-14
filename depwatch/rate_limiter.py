"""Rate limiter for notification channels to prevent alert flooding."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RateLimitConfig:
    max_alerts: int = 5          # max alerts per window
    window_seconds: int = 3600   # rolling window in seconds
    cooldown_seconds: int = 300  # minimum gap between any two alerts


@dataclass
class _ChannelState:
    timestamps: list = field(default_factory=list)
    last_sent: float = 0.0


class RateLimiter:
    """Tracks per-channel alert rates and enforces limits."""

    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        self._config = config or RateLimitConfig()
        self._state: Dict[str, _ChannelState] = defaultdict(_ChannelState)

    def _now(self) -> float:  # pragma: no cover — overridden in tests
        return time.time()

    def _prune(self, state: _ChannelState, now: float) -> None:
        cutoff = now - self._config.window_seconds
        state.timestamps = [t for t in state.timestamps if t >= cutoff]

    def is_allowed(self, channel: str) -> bool:
        """Return True if an alert on *channel* is permitted right now."""
        now = self._now()
        state = self._state[channel]
        self._prune(state, now)

        if now - state.last_sent < self._config.cooldown_seconds:
            return False

        if len(state.timestamps) >= self._config.max_alerts:
            return False

        return True

    def record(self, channel: str) -> None:
        """Record that an alert was sent on *channel*."""
        now = self._now()
        state = self._state[channel]
        self._prune(state, now)
        state.timestamps.append(now)
        state.last_sent = now

    def remaining(self, channel: str) -> int:
        """Return how many more alerts are allowed in the current window."""
        now = self._now()
        state = self._state[channel]
        self._prune(state, now)
        return max(0, self._config.max_alerts - len(state.timestamps))

    def reset(self, channel: str) -> None:
        """Clear rate-limit state for *channel*."""
        self._state.pop(channel, None)
