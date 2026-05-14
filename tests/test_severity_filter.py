"""Tests for depwatch.severity_filter."""

from __future__ import annotations

import pytest

from depwatch.scanner import PackageInfo, ScanResult
from depwatch.severity_filter import (
    filter_by_severity,
    meets_minimum_severity,
    severity_counts,
)


@pytest.fixture()
def pkg_low() -> PackageInfo:
    return PackageInfo(name="pkgA", current="1.0", latest="1.1", vulns=["CVE-001"], vuln_severity="low")


@pytest.fixture()
def pkg_medium() -> PackageInfo:
    return PackageInfo(name="pkgB", current="2.0", latest="2.1", vulns=["CVE-002"], vuln_severity="medium")


@pytest.fixture()
def pkg_high() -> PackageInfo:
    return PackageInfo(name="pkgC", current="3.0", latest="3.1", vulns=["CVE-003"], vuln_severity="high")


@pytest.fixture()
def pkg_critical() -> PackageInfo:
    return PackageInfo(name="pkgD", current="4.0", latest="4.1", vulns=["CVE-004"], vuln_severity="critical")


@pytest.fixture()
def pkg_outdated_only() -> PackageInfo:
    return PackageInfo(name="pkgE", current="5.0", latest="5.1", vulns=[], vuln_severity=None)


@pytest.fixture()
def full_result(pkg_low, pkg_medium, pkg_high, pkg_critical, pkg_outdated_only) -> ScanResult:
    return ScanResult(
        packages=[pkg_low, pkg_medium, pkg_high, pkg_critical, pkg_outdated_only],
        scanned_file="requirements.txt",
    )


def test_meets_minimum_severity_no_vuln(pkg_outdated_only):
    assert meets_minimum_severity(pkg_outdated_only, "critical") is True


def test_meets_minimum_severity_exact_match(pkg_medium):
    assert meets_minimum_severity(pkg_medium, "medium") is True


def test_meets_minimum_severity_below_threshold(pkg_low):
    assert meets_minimum_severity(pkg_low, "high") is False


def test_meets_minimum_severity_above_threshold(pkg_critical):
    assert meets_minimum_severity(pkg_critical, "medium") is True


def test_filter_by_severity_high_keeps_high_and_critical(full_result):
    result = filter_by_severity(full_result, "high")
    names = {p.name for p in result.packages}
    assert "pkgC" in names  # high
    assert "pkgD" in names  # critical
    assert "pkgE" in names  # outdated-only always included
    assert "pkgA" not in names  # low
    assert "pkgB" not in names  # medium


def test_filter_by_severity_low_keeps_all(full_result):
    result = filter_by_severity(full_result, "low")
    assert len(result.packages) == 5


def test_filter_by_severity_critical_only(full_result):
    result = filter_by_severity(full_result, "critical")
    names = {p.name for p in result.packages}
    assert "pkgD" in names
    assert "pkgE" in names
    assert len(names) == 2


def test_filter_preserves_scanned_file(full_result):
    result = filter_by_severity(full_result, "medium")
    assert result.scanned_file == "requirements.txt"


def test_severity_counts(full_result):
    counts = severity_counts(full_result)
    assert counts["low"] == 1
    assert counts["medium"] == 1
    assert counts["high"] == 1
    assert counts["critical"] == 1
    assert counts["unknown"] == 0


def test_severity_counts_empty():
    result = ScanResult(packages=[], scanned_file="req.txt")
    counts = severity_counts(result)
    assert all(v == 0 for v in counts.values())
