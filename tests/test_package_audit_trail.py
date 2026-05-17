"""Tests for depwatch.package_audit_trail."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.package_audit_trail import (
    AuditEntry,
    clear_audit_trail,
    load_audit_trail,
    record_event,
)
from depwatch.scanner import PackageInfo, ScanResult


@pytest.fixture()
def audit_file(tmp_path: Path) -> str:
    return str(tmp_path / "audit.jsonl")


@pytest.fixture()
def scan_result() -> ScanResult:
    pkgs = [
        PackageInfo("requests", "2.28.0", "2.31.0", []),
        PackageInfo("flask", "2.0.0", "2.0.0", ["CVE-2023-1234"]),
    ]
    return ScanResult(pkgs)


def test_record_event_creates_file(audit_file: str, scan_result: ScanResult) -> None:
    record_event("requirements.txt", scan_result, audit_file=audit_file)
    assert Path(audit_file).exists()


def test_record_event_returns_entry(audit_file: str, scan_result: ScanResult) -> None:
    entry = record_event("requirements.txt", scan_result, audit_file=audit_file)
    assert isinstance(entry, AuditEntry)
    assert entry.dep_file == "requirements.txt"
    assert entry.total_packages == 2
    assert entry.outdated_count == 1
    assert entry.vulnerable_count == 1


def test_record_event_alert_flag(audit_file: str, scan_result: ScanResult) -> None:
    entry = record_event(
        "requirements.txt", scan_result, triggered_alert=True, audit_file=audit_file
    )
    assert entry.triggered_alert is True


def test_load_audit_trail_accumulates(audit_file: str, scan_result: ScanResult) -> None:
    record_event("req.txt", scan_result, audit_file=audit_file)
    record_event("req.txt", scan_result, audit_file=audit_file)
    entries = load_audit_trail(audit_file=audit_file)
    assert len(entries) == 2


def test_load_audit_trail_missing_file(audit_file: str) -> None:
    entries = load_audit_trail(audit_file=audit_file)
    assert entries == []


def test_load_audit_trail_entry_fields(audit_file: str, scan_result: ScanResult) -> None:
    record_event("req.txt", scan_result, notes="nightly", audit_file=audit_file)
    entries = load_audit_trail(audit_file=audit_file)
    assert entries[0].notes == "nightly"
    assert entries[0].timestamp  # non-empty


def test_clear_audit_trail(audit_file: str, scan_result: ScanResult) -> None:
    record_event("req.txt", scan_result, audit_file=audit_file)
    clear_audit_trail(audit_file=audit_file)
    assert not Path(audit_file).exists()


def test_clear_audit_trail_no_file_is_noop(audit_file: str) -> None:
    # Should not raise even if file doesn't exist
    clear_audit_trail(audit_file=audit_file)
