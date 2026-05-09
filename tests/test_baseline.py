"""Tests for depwatch.baseline module."""

import json
import os
import pytest

from depwatch.scanner import PackageInfo, ScanResult
from depwatch.baseline import save_baseline, load_baseline, diff_against_baseline


DEP_FILE = "requirements.txt"


@pytest.fixture
def scan_result():
    return ScanResult(packages=[
        PackageInfo("requests", "2.28.0", "2.31.0", []),
        PackageInfo("flask", "2.2.0", "2.2.0", ["CVE-2023-0001"]),
    ])


@pytest.fixture
def baseline_result():
    return ScanResult(packages=[
        PackageInfo("requests", "2.28.0", "2.28.0", []),
        PackageInfo("flask", "2.2.0", "2.2.0", []),
    ])


def test_save_baseline_creates_file(tmp_path, scan_result):
    path = str(tmp_path / "test.baseline.json")
    returned = save_baseline(scan_result, DEP_FILE, path=path)
    assert returned == path
    assert os.path.exists(path)


def test_save_baseline_json_structure(tmp_path, scan_result):
    path = str(tmp_path / "test.baseline.json")
    save_baseline(scan_result, DEP_FILE, path=path)
    with open(path) as fh:
        data = json.load(fh)
    assert "saved_at" in data
    assert data["dep_file"] == DEP_FILE
    assert len(data["packages"]) == 2
    names = {p["name"] for p in data["packages"]}
    assert names == {"requests", "flask"}


def test_load_baseline_missing_returns_none(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    result = load_baseline(DEP_FILE, path=path)
    assert result is None


def test_load_baseline_round_trip(tmp_path, scan_result):
    path = str(tmp_path / "test.baseline.json")
    save_baseline(scan_result, DEP_FILE, path=path)
    loaded = load_baseline(DEP_FILE, path=path)
    assert loaded is not None
    assert len(loaded.packages) == 2
    names = {p.name for p in loaded.packages}
    assert names == {"requests", "flask"}


def test_load_baseline_preserves_package_fields(tmp_path, scan_result):
    """Ensure all PackageInfo fields survive a save/load round trip."""
    path = str(tmp_path / "test.baseline.json")
    save_baseline(scan_result, DEP_FILE, path=path)
    loaded = load_baseline(DEP_FILE, path=path)
    pkg_map = {p.name: p for p in loaded.packages}
    assert pkg_map["requests"].installed == "2.28.0"
    assert pkg_map["requests"].latest == "2.31.0"
    assert pkg_map["flask"].vulnerabilities == ["CVE-2023-0001"]


def test_diff_finds_new_outdated(scan_result, baseline_result):
    diff = diff_against_baseline(scan_result, baseline_result)
    names = {p.name for p in diff.packages}
    assert "requests" in names


def test_diff_finds_new_vulnerability(scan_result, baseline_result):
    diff = diff_against_baseline(scan_result, baseline_result)
    names = {p.name for p in diff.packages}
    assert "flask" in names


def test_diff_no_new_issues(baseline_result):
    diff = diff_against_baseline(baseline_result, baseline_result)
    assert diff.packages == []


def test_diff_new_package_flagged(baseline_result):
    new_pkg = PackageInfo("boto3", "1.0.0", "1.5.0", [])
    current = ScanResult(packages=baseline_result.packages + [new_pkg])
    diff = diff_against_baseline(current, baseline_result)
    names = {p.name for p in diff.packages}
    assert "boto3" in names
