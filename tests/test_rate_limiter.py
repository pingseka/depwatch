"""Tests for depwatch.rate_limiter."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from depwatch.rate_limiter import RateLimiter, RateLimitConfig


@pytest.fixture()
def cfg():
    return RateLimitConfig(max_alerts=3, window_seconds=60, cooldown_seconds=10)


@pytest.fixture()
def limiter(cfg):
    return RateLimiter(cfg)


def _tick(limiter: RateLimiter, t: float) -> None:
    limiter._now = lambda: t  # type: ignore[method-assign]


def test_initially_allowed(limiter):
    _tick(limiter, 1000.0)
    assert limiter.is_allowed("log") is True


def test_cooldown_blocks_immediate_repeat(limiter):
    _tick(limiter, 1000.0)
    limiter.record("log")
    # still within cooldown
    _tick(limiter, 1005.0)
    assert limiter.is_allowed("log") is False


def test_allowed_after_cooldown(limiter):
    _tick(limiter, 1000.0)
    limiter.record("log")
    _tick(limiter, 1011.0)  # past cooldown_seconds=10
    assert limiter.is_allowed("log") is True


def test_max_alerts_blocks(limiter):
    t = 1000.0
    for i in range(3):  # max_alerts=3
        _tick(limiter, t + i * 11)  # each 11 s apart (> cooldown)
        assert limiter.is_allowed("log") is True
        limiter.record("log")
    _tick(limiter, t + 3 * 11)
    assert limiter.is_allowed("log") is False


def test_window_expires_restores_budget(limiter):
    _tick(limiter, 1000.0)
    limiter.record("log")
    limiter.record("log")  # manually push without cooldown check
    limiter.record("log")
    # advance past window_seconds=60
    _tick(limiter, 1000.0 + 61)
    assert limiter.is_allowed("log") is True


def test_remaining_decrements(limiter):
    _tick(limiter, 1000.0)
    assert limiter.remaining("log") == 3
    limiter.record("log")
    assert limiter.remaining("log") == 2


def test_reset_clears_state(limiter):
    _tick(limiter, 1000.0)
    for _ in range(3):
        limiter.record("log")
    limiter.reset("log")
    assert limiter.remaining("log") == 3


def test_channels_are_independent(limiter):
    _tick(limiter, 1000.0)
    for _ in range(3):
        limiter.record("webhook")
    assert limiter.is_allowed("log") is True
    assert limiter.is_allowed("webhook") is False
