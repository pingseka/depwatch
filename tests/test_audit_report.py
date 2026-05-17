"""Tests for depwatch.audit_report."""
from __future__ import annotations

import json

import pytest

from depwatch.audit_report import has_alerts, render_json, render_text, summary_stats
from depwatch.package_audit_trail import AuditEntry


@pytest.fixture()
def entries() -> list:
    return [
        AuditEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            dep_file="requirements.txt",
            total_packages=5,
            outdated_count=2,
            vulnerable_count=1,
            triggered_alert=False,
        ),
        AuditEntry(
            timestamp="2024-01-02T00:00:00+00:00",
            dep_file="requirements.txt",
            total_packages=5,
            outdated_count=3,
            vulnerable_count=2,
            triggered_alert=True,
            notes="critical alert",
        ),
    ]


def test_render_text_contains_timestamps(entries: list) -> None:
    out = render_text(entries)
    assert "2024-01-01" in out
    assert "2024-01-02" in out


def test_render_text_shows_alert_flag(entries: list) -> None:
    out = render_text(entries)
    assert "[ALERT]" in out


def test_render_text_shows_counts(entries: list) -> None:
    out = render_text(entries)
    assert "outdated=2" in out
    assert "vulnerable=1" in out


def test_render_text_shows_notes(entries: list) -> None:
    out = render_text(entries)
    assert "critical alert" in out


def test_render_text_empty() -> None:
    out = render_text([])
    assert "No audit entries" in out


def test_render_json_is_valid(entries: list) -> None:
    out = render_json(entries)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[1]["triggered_alert"] is True


def test_has_alerts_true(entries: list) -> None:
    assert has_alerts(entries) is True


def test_has_alerts_false() -> None:
    e = AuditEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        dep_file="req.txt",
        total_packages=1,
        outdated_count=0,
        vulnerable_count=0,
        triggered_alert=False,
    )
    assert has_alerts([e]) is False


def test_summary_stats(entries: list) -> None:
    stats = summary_stats(entries)
    assert stats["total_scans"] == 2
    assert stats["total_alerts"] == 1
    assert stats["avg_outdated"] == 2.5
    assert stats["avg_vulnerable"] == 1.5


def test_summary_stats_empty() -> None:
    stats = summary_stats([])
    assert stats["total_scans"] == 0
