"""Tests for depwatch.package_size and depwatch.size_report."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from depwatch.package_size import (
    PackageSizeInfo,
    DEFAULT_SIZE_THRESHOLD,
    fetch_size,
    scan_sizes,
)
from depwatch.size_report import render_text, render_json, has_large_packages


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_pypi_response(size_bytes: int, version: str = "1.0.0"):
    payload = {
        "info": {"version": version},
        "urls": [{"size": size_bytes}],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# PackageSizeInfo unit tests
# ---------------------------------------------------------------------------

def test_is_large_when_exceeds_threshold():
    info = PackageSizeInfo(name="big", version="1.0", size_bytes=20 * 1024 * 1024)
    assert info.is_large is True


def test_is_not_large_when_below_threshold():
    info = PackageSizeInfo(name="small", version="1.0", size_bytes=1024)
    assert info.is_large is False


def test_is_not_large_when_size_unknown():
    info = PackageSizeInfo(name="pkg", version="1.0", size_bytes=None)
    assert info.is_large is False


def test_size_kb_rounds_correctly():
    info = PackageSizeInfo(name="pkg", version="1.0", size_bytes=2048)
    assert info.size_kb == 2.0


def test_size_kb_none_when_size_bytes_none():
    info = PackageSizeInfo(name="pkg", version="1.0", size_bytes=None)
    assert info.size_kb is None


# ---------------------------------------------------------------------------
# fetch_size
# ---------------------------------------------------------------------------

def test_fetch_size_success():
    with patch("urllib.request.urlopen", return_value=_mock_pypi_response(5 * 1024 * 1024)):
        info = fetch_size("requests")
    assert info.name == "requests"
    assert info.size_bytes == 5 * 1024 * 1024
    assert info.error is None
    assert info.is_large is False


def test_fetch_size_large_package():
    big = 15 * 1024 * 1024
    with patch("urllib.request.urlopen", return_value=_mock_pypi_response(big)):
        info = fetch_size("tensorflow")
    assert info.is_large is True


def test_fetch_size_network_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        info = fetch_size("requests")
    assert info.size_bytes is None
    assert info.error is not None
    assert "timeout" in info.error


def test_fetch_size_unexpected_error():
    with patch("urllib.request.urlopen", side_effect=ValueError("boom")):
        info = fetch_size("requests")
    assert info.error is not None
    assert "boom" in info.error


# ---------------------------------------------------------------------------
# scan_sizes
# ---------------------------------------------------------------------------

def test_scan_sizes_returns_one_per_package():
    with patch("depwatch.package_size.fetch_size") as mock_fetch:
        mock_fetch.side_effect = lambda name, **kw: PackageSizeInfo(
            name=name, version="1.0", size_bytes=1024
        )
        results = scan_sizes(["requests", "flask"])
    assert len(results) == 2
    assert {r.name for r in results} == {"requests", "flask"}


# ---------------------------------------------------------------------------
# size_report
# ---------------------------------------------------------------------------

@pytest.fixture()
def small_pkg():
    return PackageSizeInfo(name="small", version="1.2.3", size_bytes=512 * 1024)


@pytest.fixture()
def large_pkg():
    return PackageSizeInfo(name="biglib", version="2.0.0", size_bytes=20 * 1024 * 1024)


def test_render_text_contains_package_names(small_pkg, large_pkg):
    text = render_text([small_pkg, large_pkg])
    assert "small" in text
    assert "biglib" in text


def test_render_text_flags_large_package(large_pkg):
    text = render_text([large_pkg])
    assert "[LARGE]" in text


def test_render_text_no_flag_for_small(small_pkg):
    text = render_text([small_pkg])
    assert "[LARGE]" not in text


def test_render_text_shows_summary(small_pkg, large_pkg):
    text = render_text([small_pkg, large_pkg])
    assert "Total packages: 2" in text
    assert "Large packages: 1" in text


def test_render_json_is_valid(small_pkg, large_pkg):
    raw = render_json([small_pkg, large_pkg])
    data = json.loads(raw)
    assert len(data) == 2
    assert data[0]["name"] == "small"


def test_has_large_packages_true(large_pkg):
    assert has_large_packages([large_pkg]) is True


def test_has_large_packages_false(small_pkg):
    assert has_large_packages([small_pkg]) is False


def test_render_text_empty():
    assert "No packages" in render_text([])
