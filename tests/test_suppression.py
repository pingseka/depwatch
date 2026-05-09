"""Tests for depwatch.suppression module."""

import json
import os
import pytest

from depwatch.suppression import (
    SuppressionEntry,
    SuppressionList,
    add_suppression,
    load_suppressions,
    save_suppressions,
)


# ---------------------------------------------------------------------------
# SuppressionEntry
# ---------------------------------------------------------------------------

def test_entry_not_expired_when_no_expiry():
    entry = SuppressionEntry(package="requests", reason="false positive")
    assert not entry.is_expired()


def test_entry_expired_past_date():
    entry = SuppressionEntry(package="requests", reason="ok", expires="2000-01-01")
    assert entry.is_expired()


def test_entry_not_expired_future_date():
    entry = SuppressionEntry(package="requests", reason="ok", expires="2099-01-01")
    assert not entry.is_expired()


def test_entry_matches_package_name():
    entry = SuppressionEntry(package="Flask", reason="ok")
    assert entry.matches("flask")
    assert not entry.matches("django")


def test_entry_matches_with_vuln_id():
    entry = SuppressionEntry(
        package="urllib3", reason="ok", vulnerability_id="CVE-2023-0001"
    )
    assert entry.matches("urllib3", "CVE-2023-0001")
    assert not entry.matches("urllib3", "CVE-2023-9999")


def test_entry_does_not_match_when_expired():
    entry = SuppressionEntry(package="requests", reason="ok", expires="2000-01-01")
    assert not entry.matches("requests")


# ---------------------------------------------------------------------------
# SuppressionList
# ---------------------------------------------------------------------------

def test_suppression_list_is_suppressed():
    sl = SuppressionList(
        entries=[SuppressionEntry(package="boto3", reason="internal")]
    )
    assert sl.is_suppressed("boto3")
    assert not sl.is_suppressed("numpy")


def test_active_entries_excludes_expired():
    sl = SuppressionList(
        entries=[
            SuppressionEntry(package="a", reason="r", expires="2000-01-01"),
            SuppressionEntry(package="b", reason="r", expires="2099-01-01"),
        ]
    )
    active = sl.active_entries()
    assert len(active) == 1
    assert active[0].package == "b"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

@pytest.fixture()
def suppression_file(tmp_path):
    return str(tmp_path / "suppressions.json")


def test_load_suppressions_missing_file(suppression_file):
    sl = load_suppressions(suppression_file)
    assert sl.entries == []


def test_save_and_load_round_trip(suppression_file):
    sl = SuppressionList(
        entries=[SuppressionEntry(package="requests", reason="test", expires="2099-12-31")]
    )
    save_suppressions(sl, suppression_file)
    loaded = load_suppressions(suppression_file)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].package == "requests"
    assert loaded.entries[0].expires == "2099-12-31"


def test_add_suppression_creates_and_appends(suppression_file):
    add_suppression("django", "known issue", path=suppression_file)
    add_suppression("flask", "another issue", path=suppression_file)
    sl = load_suppressions(suppression_file)
    names = [e.package for e in sl.entries]
    assert "django" in names
    assert "flask" in names
