"""Tests for depwatch.package_freshness."""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest

from depwatch.package_freshness import (
    DEFAULT_STALE_DAYS,
    PackageFreshnessInfo,
    fetch_freshness,
    scan_freshness,
)

_NOW = datetime.datetime(2024, 6, 1, 12, 0, 0)


def _mock_pypi_response(upload_time: str, version: str = "1.0.0") -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "info": {"version": version},
        "releases": {
            version: [{"upload_time": upload_time, "filename": f"{version}.tar.gz"}]
        },
    }
    return mock_resp


@patch("depwatch.package_freshness._utcnow", return_value=_NOW)
@patch("depwatch.package_freshness.requests.get")
def test_fetch_freshness_not_stale(mock_get, _mock_now):
    upload = ((_NOW - datetime.timedelta(days=100)).isoformat())
    mock_get.return_value = _mock_pypi_response(upload)

    info = fetch_freshness("requests", stale_days=DEFAULT_STALE_DAYS)

    assert info.name == "requests"
    assert info.days_since_release == 100
    assert info.is_stale is False
    assert info.error is None


@patch("depwatch.package_freshness._utcnow", return_value=_NOW)
@patch("depwatch.package_freshness.requests.get")
def test_fetch_freshness_stale(mock_get, _mock_now):
    upload = ((_NOW - datetime.timedelta(days=400)).isoformat())
    mock_get.return_value = _mock_pypi_response(upload)

    info = fetch_freshness("oldpkg", stale_days=DEFAULT_STALE_DAYS)

    assert info.is_stale is True
    assert info.days_since_release == 400


@patch("depwatch.package_freshness._utcnow", return_value=_NOW)
@patch("depwatch.package_freshness.requests.get")
def test_fetch_freshness_exactly_on_boundary_is_stale(mock_get, _mock_now):
    upload = ((_NOW - datetime.timedelta(days=DEFAULT_STALE_DAYS)).isoformat())
    mock_get.return_value = _mock_pypi_response(upload)

    info = fetch_freshness("edgepkg")

    assert info.is_stale is True


@patch("depwatch.package_freshness.requests.get", side_effect=ConnectionError("timeout"))
def test_fetch_freshness_network_error(mock_get):
    info = fetch_freshness("badpkg")

    assert info.error is not None
    assert "timeout" in info.error
    assert info.is_stale is False
    assert info.latest_release_date is None


@patch("depwatch.package_freshness._utcnow", return_value=_NOW)
@patch("depwatch.package_freshness.requests.get")
def test_fetch_freshness_missing_release_date(mock_get, _mock_now):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "info": {"version": "2.0.0"},
        "releases": {"2.0.0": []},
    }
    mock_get.return_value = mock_resp

    info = fetch_freshness("nopkg")

    assert info.latest_release_date is None
    assert info.error == "release date unavailable"


@patch("depwatch.package_freshness._utcnow", return_value=_NOW)
@patch("depwatch.package_freshness.requests.get")
def test_scan_freshness_returns_list(mock_get, _mock_now):
    upload = ((_NOW - datetime.timedelta(days=50)).isoformat())
    mock_get.return_value = _mock_pypi_response(upload)

    results = scan_freshness(["pkg1", "pkg2"], stale_days=200)

    assert len(results) == 2
    assert all(isinstance(r, PackageFreshnessInfo) for r in results)
    assert all(r.is_stale is False for r in results)
