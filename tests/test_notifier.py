"""Tests for depwatch.notifier module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from depwatch.notifier import (
    NotifierConfig,
    _format_message,
    notify_log,
    notify_webhook,
    send_alert,
)
from depwatch.scanner import PackageInfo, ScanResult


@pytest.fixture
def outdated_pkg():
    return PackageInfo(name="requests", current_version="2.25.0", latest_version="2.31.0")


@pytest.fixture
def vulnerable_pkg():
    return PackageInfo(
        name="urllib3",
        current_version="1.26.0",
        latest_version="2.0.0",
        vulnerabilities=["CVE-2023-1234"],
    )


@pytest.fixture
def scan_result(outdated_pkg, vulnerable_pkg):
    return ScanResult(packages=[outdated_pkg, vulnerable_pkg])


@pytest.fixture
def empty_result():
    pkg = PackageInfo(name="flask", current_version="2.3.0", latest_version="2.3.0")
    return ScanResult(packages=[pkg])


def test_format_message_contains_package_names(scan_result):
    msg = _format_message(scan_result)
    assert "requests" in msg
    assert "urllib3" in msg
    assert "CVE-2023-1234" in msg
    assert "2.25.0" in msg
    assert "2.31.0" in msg


def test_notify_log_calls_logger(scan_result):
    with patch("depwatch.notifier.logger") as mock_logger:
        notify_log(scan_result)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "depwatch" in call_args


def test_notify_webhook_posts_json(scan_result):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        notify_webhook(scan_result, "http://example.com/hook")
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        assert "requests" in body["outdated"]
        assert "urllib3" in body["vulnerable"]


def test_send_alert_no_op_when_no_issues(empty_result):
    cfg = NotifierConfig(method="log")
    with patch("depwatch.notifier.notify_log") as mock_log:
        send_alert(empty_result, cfg)
        mock_log.assert_not_called()


def test_send_alert_webhook_raises_without_url(scan_result):
    cfg = NotifierConfig(method="webhook")
    with pytest.raises(ValueError, match="webhook_url"):
        send_alert(scan_result, cfg)


def test_send_alert_dispatches_webhook(scan_result):
    cfg = NotifierConfig(method="webhook", webhook_url="http://example.com/hook")
    with patch("depwatch.notifier.notify_webhook") as mock_wh:
        send_alert(scan_result, cfg)
        mock_wh.assert_called_once_with(scan_result, "http://example.com/hook")
