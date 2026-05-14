"""Tests for depwatch.notifier_rate_limited."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from depwatch.notifier import NotifierConfig
from depwatch.notifier_rate_limited import RateLimitedNotifier
from depwatch.rate_limiter import RateLimitConfig
from depwatch.scanner import PackageInfo, ScanResult


@pytest.fixture()
def pkg():
    return PackageInfo(name="flask", current="2.0.0", latest="3.0.0",
                       vulnerabilities=["CVE-2023-0001"])


@pytest.fixture()
def result(pkg):
    return ScanResult(packages=[pkg])


@pytest.fixture()
def empty_result():
    return ScanResult(packages=[])


@pytest.fixture()
def ncfg():
    return NotifierConfig(log_level="WARNING")


@pytest.fixture()
def rl_notifier(ncfg):
    rc = RateLimitConfig(max_alerts=2, window_seconds=60, cooldown_seconds=5)
    n = RateLimitedNotifier(ncfg, rc)
    n._limiter._now = lambda: 1000.0  # type: ignore[method-assign]
    return n


def test_empty_result_not_sent(rl_notifier, empty_result):
    with patch("depwatch.notifier_rate_limited.notify_log") as mock_log:
        sent = rl_notifier.notify("log", empty_result)
    assert sent is False
    mock_log.assert_not_called()


def test_first_alert_dispatched(rl_notifier, result):
    with patch("depwatch.notifier_rate_limited.notify_log") as mock_log:
        mock_log.return_value = None
        sent = rl_notifier.notify("log", result)
    assert sent is True
    mock_log.assert_called_once()


def test_rate_limited_after_max(rl_notifier, result):
    times = iter([1000.0, 1006.0, 1012.0, 1018.0])
    rl_notifier._limiter._now = lambda: next(times)  # type: ignore[method-assign]

    with patch("depwatch.notifier_rate_limited.notify_log"):
        rl_notifier.notify("log", result)  # 1st
        rl_notifier.notify("log", result)  # 2nd — hits max_alerts=2
        sent = rl_notifier.notify("log", result)  # 3rd — should be blocked
    assert sent is False


def test_remaining_exposed(rl_notifier, result):
    assert rl_notifier.remaining("log") == 2
    with patch("depwatch.notifier_rate_limited.notify_log"):
        rl_notifier.notify("log", result)
    assert rl_notifier.remaining("log") == 1


def test_reset_restores_budget(rl_notifier, result):
    with patch("depwatch.notifier_rate_limited.notify_log"):
        rl_notifier.notify("log", result)
    rl_notifier.reset("log")
    assert rl_notifier.remaining("log") == 2


def test_unknown_channel_returns_false(rl_notifier, result):
    sent = rl_notifier.notify("sms", result)
    assert sent is False
