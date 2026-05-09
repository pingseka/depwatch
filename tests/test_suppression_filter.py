"""Tests for depwatch.suppression_filter module."""

import pytest

from depwatch.scanner import PackageInfo, ScanResult
from depwatch.suppression import SuppressionEntry, SuppressionList
from depwatch.suppression_filter import filter_scan_result, suppressed_packages


@pytest.fixture()
def pkg_outdated():
    return PackageInfo(
        name="requests",
        current_version="2.20.0",
        latest_version="2.31.0",
        vulnerabilities=[],
    )


@pytest.fixture()
def pkg_vulnerable():
    return PackageInfo(
        name="urllib3",
        current_version="1.26.0",
        latest_version="2.0.0",
        vulnerabilities=["CVE-2023-0001"],
    )


@pytest.fixture()
def scan_result(pkg_outdated, pkg_vulnerable):
    return ScanResult(
        packages=[pkg_outdated, pkg_vulnerable],
        scanned_file="requirements.txt",
    )


@pytest.fixture()
def suppression_list():
    return SuppressionList(
        entries=[SuppressionEntry(package="requests", reason="false positive")]
    )


def test_filter_removes_suppressed_package(scan_result, suppression_list):
    filtered = filter_scan_result(scan_result, suppression_list)
    names = [p.name for p in filtered.packages]
    assert "requests" not in names
    assert "urllib3" in names


def test_filter_preserves_scanned_file(scan_result, suppression_list):
    filtered = filter_scan_result(scan_result, suppression_list)
    assert filtered.scanned_file == scan_result.scanned_file


def test_filter_empty_suppression_list(scan_result):
    filtered = filter_scan_result(scan_result, SuppressionList())
    assert len(filtered.packages) == len(scan_result.packages)


def test_suppressed_packages_returns_only_suppressed(scan_result, suppression_list):
    suppressed = suppressed_packages(scan_result, suppression_list)
    assert len(suppressed) == 1
    assert suppressed[0].name == "requests"


def test_suppressed_packages_empty_when_no_match(scan_result):
    sl = SuppressionList(
        entries=[SuppressionEntry(package="nonexistent", reason="test")]
    )
    assert suppressed_packages(scan_result, sl) == []


def test_filter_all_suppressed(scan_result):
    sl = SuppressionList(
        entries=[
            SuppressionEntry(package="requests", reason="r"),
            SuppressionEntry(package="urllib3", reason="r"),
        ]
    )
    filtered = filter_scan_result(scan_result, sl)
    assert filtered.packages == []
