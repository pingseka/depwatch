"""Tests for depwatch.package_python_version."""
from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock
import json

import pytest

from depwatch.package_python_version import (
    fetch_python_version,
    scan_python_versions,
    _check_compatible,
    PythonVersionInfo,
)


CURRENT = (sys.version_info.major, sys.version_info.minor)
CURRENT_STR = f"{CURRENT[0]}.{CURRENT[1]}"


def _mock_pypi_response(name: str, version: str, requires_python: str | None):
    payload = json.dumps({
        "info": {
            "name": name,
            "version": version,
            "requires_python": requires_python,
        }
    }).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# --- _check_compatible ---

def test_check_compatible_no_constraint():
    assert _check_compatible(None, (3, 10)) is True


def test_check_compatible_gte_passes():
    assert _check_compatible(">=3.8", (3, 10)) is True


def test_check_compatible_gte_fails():
    assert _check_compatible(">=3.11", (3, 8)) is False


def test_check_compatible_lt_fails():
    assert _check_compatible("<3.8", (3, 10)) is False


def test_check_compatible_combined():
    assert _check_compatible(">=3.8,<4.0", (3, 9)) is True
    assert _check_compatible(">=3.8,<3.9", (3, 10)) is False


# --- fetch_python_version ---

def test_fetch_python_version_compatible():
    requires = f">={CURRENT[0]}.{CURRENT[1]}"
    with patch("urllib.request.urlopen",
               return_value=_mock_pypi_response("requests", "2.31.0", requires)):
        info = fetch_python_version("requests", "2.31.0")
    assert info.name == "requests"
    assert info.version == "2.31.0"
    assert info.requires_python == requires
    assert info.compatible is True
    assert info.current_python == CURRENT_STR
    assert info.error is None


def test_fetch_python_version_incompatible():
    future_major = CURRENT[0] + 1
    requires = f">={future_major}.0"
    with patch("urllib.request.urlopen",
               return_value=_mock_pypi_response("oldpkg", "1.0.0", requires)):
        info = fetch_python_version("oldpkg", "1.0.0")
    assert info.compatible is False


def test_fetch_python_version_no_requires_python():
    with patch("urllib.request.urlopen",
               return_value=_mock_pypi_response("noreq", "0.1.0", None)):
        info = fetch_python_version("noreq")
    assert info.requires_python is None
    assert info.compatible is True


def test_fetch_python_version_network_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        info = fetch_python_version("flaky", "1.0")
    assert info.error is not None
    assert "network error" in info.error
    assert info.compatible is True  # fail-open


# --- scan_python_versions ---

def test_scan_python_versions_returns_list():
    mock_resp = _mock_pypi_response("pkgA", "1.0.0", ">=3.6")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = scan_python_versions([("pkgA", "1.0.0")])
    assert len(results) == 1
    assert isinstance(results[0], PythonVersionInfo)
