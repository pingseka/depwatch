"""Tests for depwatch.package_ownership."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from depwatch.package_ownership import (
    PackageOwnershipInfo,
    fetch_ownership,
    scan_ownership,
)


def _mock_pypi_response(maintainer: str = "", author: str = "") -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        "info": {"maintainer": maintainer, "author": author}
    }
    return mock


def test_fetch_ownership_multiple_maintainers():
    with patch("depwatch.package_ownership.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(maintainer="Alice, Bob")
        result = fetch_ownership("requests")
    assert result.package == "requests"
    assert result.maintainer_count == 2
    assert not result.sole_maintainer
    assert "Alice" in result.maintainers
    assert result.error is None


def test_fetch_ownership_sole_maintainer():
    with patch("depwatch.package_ownership.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(maintainer="Alice")
        result = fetch_ownership("tiny-pkg")
    assert result.sole_maintainer is True
    assert result.maintainer_count == 1


def test_fetch_ownership_falls_back_to_author():
    with patch("depwatch.package_ownership.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(maintainer="", author="Bob")
        result = fetch_ownership("some-pkg")
    assert result.maintainers == ["Bob"]
    assert result.sole_maintainer is True


def test_fetch_ownership_network_error():
    import requests as req
    with patch("depwatch.package_ownership.requests.get", side_effect=req.RequestException("timeout")):
        result = fetch_ownership("broken-pkg")
    assert result.error is not None
    assert "timeout" in result.error
    assert result.maintainer_count == 0


def test_fetch_ownership_no_maintainer_info():
    with patch("depwatch.package_ownership.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response()
        result = fetch_ownership("mystery-pkg")
    assert result.maintainers == []
    assert result.maintainer_count == 0
    assert result.sole_maintainer is False


def test_scan_ownership_returns_all():
    packages = ["pkgA", "pkgB"]
    with patch("depwatch.package_ownership.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(maintainer="Dev")
        results = scan_ownership(packages)
    assert len(results) == 2
    assert {r.package for r in results} == set(packages)
