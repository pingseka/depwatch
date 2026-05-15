"""Tests for depwatch.package_license"""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock
import io

import pytest

from depwatch.package_license import (
    fetch_license,
    scan_licenses,
    PackageLicenseInfo,
    _normalize,
)


def _mock_pypi_response(license_str: str) -> MagicMock:
    payload = json.dumps({"info": {"version": "1.2.3", "license": license_str}}).encode()
    cm = MagicMock()
    cm.__enter__ = lambda s: io.BytesIO(payload)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def test_normalize_lowercases_and_strips():
    assert _normalize("  MIT  ") == "mit"


def test_fetch_license_permissive():
    with patch("urllib.request.urlopen", return_value=_mock_pypi_response("MIT")):
        info = fetch_license("requests")
    assert info.is_permissive is True
    assert info.is_copyleft is False
    assert info.is_unknown is False
    assert info.license == "MIT"
    assert info.version == "1.2.3"


def test_fetch_license_copyleft():
    with patch("urllib.request.urlopen", return_value=_mock_pypi_response("GPL-3.0")):
        info = fetch_license("somepkg")
    assert info.is_copyleft is True
    assert info.is_permissive is False
    assert info.is_unknown is False


def test_fetch_license_unknown_when_empty():
    with patch("urllib.request.urlopen", return_value=_mock_pypi_response("")):
        info = fetch_license("mypkg")
    assert info.is_unknown is True
    assert info.license is None


def test_fetch_license_network_error_returns_unknown():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        info = fetch_license("badpkg", version="0.1")
    assert info.is_unknown is True
    assert info.name == "badpkg"
    assert info.version == "0.1"


def test_scan_licenses_returns_list():
    mit_resp = _mock_pypi_response("MIT")
    gpl_resp = _mock_pypi_response("GPL-3.0")
    with patch("urllib.request.urlopen", side_effect=[mit_resp, gpl_resp]):
        results = scan_licenses(["requests", "somepkg"])
    assert len(results) == 2
    assert results[0].is_permissive is True
    assert results[1].is_copyleft is True
