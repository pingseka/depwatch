"""Tests for depwatch.trend."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from depwatch.trend import build_trend, render_trend_text, TrendPoint, TrendReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_history(tmp_path: Path, dep_file: str, entries: list) -> str:
    """Write a fake history JSON file and return the history_dir."""
    history_dir = str(tmp_path)
    safe = dep_file.replace(os.sep, "_").replace("/", "_")
    hist_file = tmp_path / f"{safe}.history.json"
    hist_file.write_text(json.dumps(entries))
    return history_dir


TWO_ENTRIES = [
    {"timestamp": "2024-01-01T00:00:00Z", "outdated_count": 2, "vulnerable_count": 1},
    {"timestamp": "2024-01-02T00:00:00Z", "outdated_count": 4, "vulnerable_count": 2},
]

IMPROVING_ENTRIES = [
    {"timestamp": "2024-01-01T00:00:00Z", "outdated_count": 5, "vulnerable_count": 3},
    {"timestamp": "2024-01-02T00:00:00Z", "outdated_count": 3, "vulnerable_count": 1},
]

STABLE_ENTRIES = [
    {"timestamp": "2024-01-01T00:00:00Z", "outdated_count": 2, "vulnerable_count": 1},
    {"timestamp": "2024-01-02T00:00:00Z", "outdated_count": 2, "vulnerable_count": 1},
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_build_trend_no_history(tmp_path):
    report = build_trend("requirements.txt", history_dir=str(tmp_path))
    assert report.points == []
    assert report.outdated_delta is None
    assert report.vulnerable_delta is None


def test_build_trend_single_entry(tmp_path):
    _write_history(tmp_path, "requirements.txt", [TWO_ENTRIES[0]])
    report = build_trend("requirements.txt", history_dir=str(tmp_path))
    assert len(report.points) == 1
    assert report.outdated_delta is None


def test_build_trend_worsening(tmp_path):
    _write_history(tmp_path, "requirements.txt", TWO_ENTRIES)
    report = build_trend("requirements.txt", history_dir=str(tmp_path))
    assert report.outdated_delta == 2
    assert report.vulnerable_delta == 1
    assert report.is_worsening is True
    assert report.is_improving is False


def test_build_trend_improving(tmp_path):
    _write_history(tmp_path, "requirements.txt", IMPROVING_ENTRIES)
    report = build_trend("requirements.txt", history_dir=str(tmp_path))
    assert report.is_improving is True
    assert report.is_worsening is False


def test_build_trend_stable(tmp_path):
    _write_history(tmp_path, "requirements.txt", STABLE_ENTRIES)
    report = build_trend("requirements.txt", history_dir=str(tmp_path))
    assert report.is_improving is False
    assert report.is_worsening is False


def test_build_trend_respects_limit(tmp_path):
    many = [
        {"timestamp": f"2024-01-{i:02d}T00:00:00Z", "outdated_count": i, "vulnerable_count": 0}
        for i in range(1, 21)
    ]
    _write_history(tmp_path, "requirements.txt", many)
    report = build_trend("requirements.txt", history_dir=str(tmp_path), limit=5)
    assert len(report.points) == 5
    assert report.points[0].outdated_count == 16


def test_render_trend_text_no_history(tmp_path):
    report = build_trend("requirements.txt", history_dir=str(tmp_path))
    text = render_trend_text(report)
    assert "No history available" in text


def test_render_trend_text_worsening(tmp_path):
    _write_history(tmp_path, "requirements.txt", TWO_ENTRIES)
    report = build_trend("requirements.txt", history_dir=str(tmp_path))
    text = render_trend_text(report)
    assert "worsening" in text
    assert "+2" in text or "Δ+2" in text


def test_render_trend_text_improving(tmp_path):
    _write_history(tmp_path, "requirements.txt", IMPROVING_ENTRIES)
    report = build_trend("requirements.txt", history_dir=str(tmp_path))
    text = render_trend_text(report)
    assert "improving" in text
