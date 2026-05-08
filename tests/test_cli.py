"""Tests for depwatch.cli module."""

import json
import threading
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli import build_parser, main
from depwatch.scanner import PackageInfo, ScanResult


@pytest.fixture()
def scan_result():
    pkg = PackageInfo(
        name="requests",
        current_version="2.27.0",
        latest_version="2.31.0",
        vulnerabilities=[],
    )
    return ScanResult(packages=[pkg])


@pytest.fixture()
def mock_config():
    cfg = MagicMock()
    cfg.dependency_files = ["requirements.txt"]
    return cfg


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["scan"])
    assert args.command == "scan"
    assert args.format == "text"
    assert args.out is None


def test_build_parser_scan_json():
    parser = build_parser()
    args = parser.parse_args(["scan", "--format", "json"])
    assert args.format == "json"


def test_build_parser_run_once():
    parser = build_parser()
    args = parser.parse_args(["run", "--once"])
    assert args.command == "run"
    assert args.once is True


def test_main_no_command_returns_1():
    result = main([])
    assert result == 1


def test_main_scan_text(capsys, mock_config, scan_result):
    with patch("depwatch.cli.load_config", return_value=mock_config), \
         patch("depwatch.cli.scan", return_value=scan_result):
        result = main(["scan"])
    assert result == 0
    captured = capsys.readouterr()
    assert "requests" in captured.out


def test_main_scan_json(capsys, mock_config, scan_result):
    with patch("depwatch.cli.load_config", return_value=mock_config), \
         patch("depwatch.cli.scan", return_value=scan_result):
        result = main(["scan", "--format", "json"])
    assert result == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "packages" in data


def test_main_scan_writes_file(tmp_path, mock_config, scan_result):
    out_file = tmp_path / "report.txt"
    with patch("depwatch.cli.load_config", return_value=mock_config), \
         patch("depwatch.cli.scan", return_value=scan_result), \
         patch("depwatch.cli.write_report") as mock_write:
        result = main(["scan", "--out", str(out_file)])
    assert result == 0
    mock_write.assert_called_once()


def test_main_run_once(mock_config):
    with patch("depwatch.cli.load_config", return_value=mock_config), \
         patch("depwatch.cli.Scheduler") as MockScheduler:
        instance = MockScheduler.return_value
        result = main(["run", "--once"])
    assert result == 0
    instance.run_once.assert_called_once()
