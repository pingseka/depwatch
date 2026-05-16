"""Tests for depwatch.package_deprecation."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from depwatch.package_deprecation import (
    PackageDeprecationInfo,
    fetch_deprecation,
    scan_deprecations,
)


def _mock_pypi_response(summary: str = "", description: str = "", classifiers=None):
    data = {
        "info": {
            "name": "somepkg",
            "version": "1.2.3",
            "summary": summary,
            "description": description,
            "classifiers": classifiers or [],
        }
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def test_fetch_deprecation_not_deprecated():
    with patch("depwatch.package_deprecation.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(summary="A useful library")
        result = fetch_deprecation("somepkg", "1.2.3")
    assert isinstance(result, PackageDeprecationInfo)
    assert result.is_deprecated is False
    assert result.deprecation_message is None
    assert result.name == "somepkg"
    assert result.version == "1.2.3"


def test_fetch_deprecation_via_summary():
    with patch("depwatch.package_deprecation.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(
            summary="This package is deprecated. Use newpkg instead."
        )
        result = fetch_deprecation("somepkg", "1.2.3")
    assert result.is_deprecated is True
    assert result.deprecation_message is not None


def test_fetch_deprecation_successor_extracted():
    with patch("depwatch.package_deprecation.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(
            summary="Deprecated. Use newpkg for the latest version."
        )
        result = fetch_deprecation("somepkg", "1.2.3")
    assert result.is_deprecated is True
    assert result.successor == "newpkg"


def test_fetch_deprecation_via_inactive_classifier():
    classifiers = ["Development Status :: 7 - Inactive"]
    with patch("depwatch.package_deprecation.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(classifiers=classifiers)
        result = fetch_deprecation("somepkg", "1.2.3")
    assert result.is_deprecated is True
    assert "Inactive" in result.deprecation_message


def test_fetch_deprecation_network_error():
    with patch("depwatch.package_deprecation.requests.get", side_effect=Exception("timeout")):
        result = fetch_deprecation("somepkg", "1.0.0")
    assert result.is_deprecated is False
    assert result.version == "1.0.0"


def test_fetch_deprecation_uses_pypi_version_when_none_given():
    with patch("depwatch.package_deprecation.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(summary="Fine library")
        result = fetch_deprecation("somepkg")
    assert result.version == "1.2.3"


def test_scan_deprecations_returns_all_packages():
    with patch("depwatch.package_deprecation.requests.get") as mock_get:
        mock_get.return_value = _mock_pypi_response(summary="All good")
        results = scan_deprecations(["pkgA", "pkgB"], versions={"pkgA": "0.1", "pkgB": "0.2"})
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"somepkg"}  # mocked name from PyPI response


def test_scan_deprecations_empty_list():
    results = scan_deprecations([])
    assert results == []
