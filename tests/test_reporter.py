"""Tests for depwatch.reporter and depwatch.report_writer."""

from __future__ import annotations

import json
import csv
import io
from pathlib import Path

import pytest

from depwatch.scanner import PackageInfo, ScanResult
from depwatch.reporter import generate_report, render_text, render_json, render_csv
from depwatch.report_writer import write_report, report_path_for_file


@pytest.fixture()
def pkg_outdated() -> PackageInfo:
    return PackageInfo(
        name="requests",
        current_version="2.28.0",
        latest_version="2.31.0",
        vulnerabilities=[],
    )


@pytest.fixture()
def pkg_vulnerable() -> PackageInfo:
    return PackageInfo(
        name="urllib3",
        current_version="1.26.5",
        latest_version="2.0.0",
        vulnerabilities=["CVE-2023-1234"],
    )


@pytest.fixture()
def scan_result(pkg_outdated, pkg_vulnerable) -> ScanResult:
    return ScanResult(
        dependency_file="requirements.txt",
        packages=[pkg_outdated, pkg_vulnerable],
    )


def test_render_text_contains_summary(scan_result):
    report = render_text(scan_result)
    assert "Total packages : 2" in report
    assert "Outdated" in report
    assert "Vulnerable" in report


def test_render_text_lists_packages(scan_result):
    report = render_text(scan_result)
    assert "requests" in report
    assert "2.28.0" in report
    assert "2.31.0" in report
    assert "CVE-2023-1234" in report


def test_render_json_valid(scan_result):
    raw = render_json(scan_result)
    data = json.loads(raw)
    assert data["summary"]["total"] == 2
    assert data["summary"]["outdated"] == 2
    assert len(data["packages"]) == 2


def test_render_csv_parseable(scan_result):
    raw = render_csv(scan_result)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 2
    names = {r["name"] for r in rows}
    assert "requests" in names
    assert "urllib3" in names


def test_generate_report_delegates_format(scan_result):
    assert generate_report(scan_result, "json").startswith("{")
    assert "name" in generate_report(scan_result, "csv")
    assert "Depwatch Report" in generate_report(scan_result, "text")


def test_write_report_to_file(tmp_path, scan_result):
    out = tmp_path / "report.txt"
    write_report(scan_result, fmt="text", output_path=str(out))
    assert out.exists()
    assert "requests" in out.read_text()


def test_write_report_creates_parent_dirs(tmp_path, scan_result):
    out = tmp_path / "sub" / "deep" / "report.json"
    write_report(scan_result, fmt="json", output_path=str(out))
    assert out.exists()


def test_report_path_for_file():
    path = report_path_for_file("requirements.txt", fmt="json", reports_dir="out")
    assert path == "out/requirements_report.json"
