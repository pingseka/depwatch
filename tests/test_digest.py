"""Tests for depwatch.digest and depwatch.digest_store."""

from __future__ import annotations

import json
import os
import pytest

from depwatch.scanner import PackageInfo, ScanResult
from depwatch.digest import compute_digest, digests_differ, digest_summary
from depwatch.digest_store import (
    load_store,
    save_digest,
    get_digest,
    remove_digest,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def pkg_outdated():
    return PackageInfo("requests", "2.28.0", "2.31.0", vuln_ids=[])


@pytest.fixture()
def pkg_vulnerable():
    return PackageInfo("flask", "2.0.0", "2.0.0", vuln_ids=["CVE-2023-1234"])


@pytest.fixture()
def scan_result(pkg_outdated, pkg_vulnerable):
    return ScanResult(packages=[pkg_outdated, pkg_vulnerable])


@pytest.fixture()
def store_file(tmp_path):
    return str(tmp_path / "digests.json")


# ---------------------------------------------------------------------------
# digest.py tests
# ---------------------------------------------------------------------------

def test_compute_digest_is_string(scan_result):
    d = compute_digest(scan_result)
    assert isinstance(d, str) and len(d) == 64


def test_compute_digest_deterministic(scan_result):
    assert compute_digest(scan_result) == compute_digest(scan_result)


def test_compute_digest_order_independent(pkg_outdated, pkg_vulnerable):
    r1 = ScanResult(packages=[pkg_outdated, pkg_vulnerable])
    r2 = ScanResult(packages=[pkg_vulnerable, pkg_outdated])
    assert compute_digest(r1) == compute_digest(r2)


def test_compute_digest_changes_with_new_package(scan_result, pkg_outdated):
    extra = PackageInfo("numpy", "1.0.0", "2.0.0", vuln_ids=[])
    r2 = ScanResult(packages=[pkg_outdated, extra])
    assert compute_digest(scan_result) != compute_digest(r2)


def test_digests_differ_none_always_true():
    assert digests_differ(None, "abc") is True
    assert digests_differ("abc", None) is True
    assert digests_differ(None, None) is True


def test_digests_differ_same_returns_false():
    assert digests_differ("abc", "abc") is False


def test_digest_summary_keys(scan_result):
    d = compute_digest(scan_result)
    summary = digest_summary(scan_result, d)
    assert "digest" in summary
    assert summary["total"] == 2
    assert summary["outdated"] >= 0
    assert summary["vulnerable"] >= 0


# ---------------------------------------------------------------------------
# digest_store.py tests
# ---------------------------------------------------------------------------

def test_load_store_missing_file(store_file):
    assert load_store(store_file) == {}


def test_save_and_get_digest(store_file):
    save_digest("requirements.txt", "deadbeef", path=store_file)
    assert get_digest("requirements.txt", path=store_file) == "deadbeef"


def test_get_digest_unknown_key_returns_none(store_file):
    assert get_digest("nonexistent.txt", path=store_file) is None


def test_remove_digest(store_file):
    save_digest("requirements.txt", "aabbcc", path=store_file)
    remove_digest("requirements.txt", path=store_file)
    assert get_digest("requirements.txt", path=store_file) is None


def test_load_store_invalid_json(store_file, tmp_path):
    with open(store_file, "w") as fh:
        fh.write("not-json")
    assert load_store(store_file) == {}
