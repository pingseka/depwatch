"""Tests for package_popularity and popularity_report modules."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from depwatch.package_popularity import (
    fetch_popularity,
    scan_popularity,
    PackagePopularityInfo,
)
from depwatch.popularity_report import render_text, render_json, has_low_popularity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(monthly: int):
    payload = json.dumps({"data": {"last_month": monthly}}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# fetch_popularity
# ---------------------------------------------------------------------------

def test_fetch_popularity_high(monkeypatch):
    with patch("urllib.request.urlopen", return_value=_mock_response(50_000)):
        info = fetch_popularity("requests", low_threshold=1000)
    assert info.name == "requests"
    assert info.monthly_downloads == 50_000
    assert info.is_low_popularity is False


def test_fetch_popularity_low(monkeypatch):
    with patch("urllib.request.urlopen", return_value=_mock_response(200)):
        info = fetch_popularity("obscure-pkg", low_threshold=1000)
    assert info.monthly_downloads == 200
    assert info.is_low_popularity is True


def test_fetch_popularity_network_error():
    with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
        info = fetch_popularity("some-pkg")
    assert info.monthly_downloads is None
    assert info.is_low_popularity is False


def test_fetch_popularity_exactly_on_threshold():
    with patch("urllib.request.urlopen", return_value=_mock_response(1000)):
        info = fetch_popularity("edge-pkg", low_threshold=1000)
    # equal to threshold → NOT low
    assert info.is_low_popularity is False


# ---------------------------------------------------------------------------
# scan_popularity
# ---------------------------------------------------------------------------

def test_scan_popularity_returns_one_per_package():
    with patch("urllib.request.urlopen", return_value=_mock_response(5000)):
        results = scan_popularity(["pkgA", "pkgB", "pkgC"])
    assert len(results) == 3
    assert all(isinstance(r, PackagePopularityInfo) for r in results)


# ---------------------------------------------------------------------------
# popularity_report
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_infos():
    return [
        PackagePopularityInfo("popular-pkg", 99_000, False, 1000),
        PackagePopularityInfo("obscure-pkg", 50, True, 1000),
        PackagePopularityInfo("unknown-pkg", None, False, 1000),
    ]


def test_render_text_contains_package_names(sample_infos):
    text = render_text(sample_infos)
    assert "popular-pkg" in text
    assert "obscure-pkg" in text
    assert "unknown-pkg" in text


def test_render_text_flags_low(sample_infos):
    text = render_text(sample_infos)
    assert "Low popularity" in text


def test_render_json_valid(sample_infos):
    raw = render_json(sample_infos)
    data = json.loads(raw)
    assert "popularity" in data
    assert len(data["popularity"]) == 3


def test_has_low_popularity_true(sample_infos):
    assert has_low_popularity(sample_infos) is True


def test_has_low_popularity_false():
    infos = [PackagePopularityInfo("big-pkg", 10_000, False, 1000)]
    assert has_low_popularity(infos) is False
