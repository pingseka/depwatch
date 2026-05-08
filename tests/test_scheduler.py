"""Tests for depwatch.scheduler."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from depwatch.config import DepwatchConfig
from depwatch.scanner import PackageInfo, ScanResult
from depwatch.scheduler import Scheduler


@pytest.fixture()
def config(tmp_path: Path) -> DepwatchConfig:
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.28.0\n")
    return DepwatchConfig(
        watch_paths=[str(req)],
        interval=60,
        min_severity="low",
        webhook_url=None,
        email_to=None,
        smtp_host=None,
        smtp_port=587,
        report_dir=None,
        report_format="text",
    )


@pytest.fixture()
def scan_result() -> ScanResult:
    pkg = PackageInfo(name="requests", current="2.28.0", latest="2.31.0", vulnerabilities=[])
    return ScanResult(packages=[pkg])


def test_run_once_no_change(config: DepwatchConfig) -> None:
    scheduler = Scheduler(config)
    with patch.object(
        list(scheduler._watchers.values())[0], "check_once", return_value=False
    ) as mock_check:
        with patch("depwatch.scheduler.scan") as mock_scan:
            scheduler.run_once()
            mock_check.assert_called_once()
            mock_scan.assert_not_called()


def test_run_once_with_change(config: DepwatchConfig, scan_result: ScanResult) -> None:
    scheduler = Scheduler(config)
    watcher = list(scheduler._watchers.values())[0]
    with patch.object(watcher, "check_once", return_value=True):
        with patch("depwatch.scheduler.scan", return_value=scan_result) as mock_scan:
            with patch("depwatch.scheduler.notify_log") as mock_log:
                scheduler.run_once()
                mock_scan.assert_called_once()
                mock_log.assert_called_once_with(scan_result, config.min_severity)


def test_run_stops_on_stop_event(config: DepwatchConfig) -> None:
    calls = {"n": 0}

    def stop_after_two() -> bool:
        calls["n"] += 1
        return calls["n"] > 2

    scheduler = Scheduler(config, stop_event=stop_after_two)
    with patch.object(scheduler, "run_once") as mock_once:
        with patch("depwatch.scheduler.time.sleep"):
            scheduler.run()
            assert mock_once.call_count == 2


def test_webhook_called_when_configured(config: DepwatchConfig, scan_result: ScanResult) -> None:
    config.webhook_url = "https://hooks.example.com/test"
    scheduler = Scheduler(config)
    watcher = list(scheduler._watchers.values())[0]
    with patch.object(watcher, "check_once", return_value=True):
        with patch("depwatch.scheduler.scan", return_value=scan_result):
            with patch("depwatch.scheduler.notify_log"):
                with patch("depwatch.scheduler.notify_webhook") as mock_wh:
                    scheduler.run_once()
                    mock_wh.assert_called_once()
