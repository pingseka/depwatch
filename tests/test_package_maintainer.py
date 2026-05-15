"""Tests for depwatch.package_maintainer"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock
import urllib.error

import pytest

from depwatch.package_maintainer import (
    fetch_maintainer,
    scan_maintainers,
    PackageMaintainerInfo,
)


def _mock_pypi_response(author: str = "Alice", author_email: str = "alice@example.com"):
    payload = {
        "info": {
            "name": "mypackage",
            "version": "1.2.3",
            "author": author,
            "author_email": author_email,
        },
        "urls": [],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_fetch_maintainer_fields():
    with patch("urllib.request.urlopen", return_value=_mock_pypi_response()) as _:
        info = fetch_maintainer("mypackage", "1.2.3")
    assert info.name == "mypackage"
    assert info.version == "1.2.3"
    assert info.author == "Alice"
    assert info.author_email == "alice@example.com"
    assert info.is_abandoned is False
    assert info.warning is None


def test_fetch_maintainer_abandoned_when_no_author():
    with patch("urllib.request.urlopen", return_value=_mock_pypi_response(author="", author_email="")):
        info = fetch_maintainer("orphan")
    assert info.is_abandoned is True


def test_fetch_maintainer_network_error():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        info = fetch_maintainer("mypackage", "1.0.0")
    assert info.warning is not None
    assert "network error" in info.warning
    assert info.version == "1.0.0"


def test_fetch_maintainer_unexpected_error():
    with patch("urllib.request.urlopen", side_effect=ValueError("bad")):
        info = fetch_maintainer("mypackage")
    assert info.warning is not None
    assert "unexpected error" in info.warning


def test_scan_maintainers_returns_list():
    with patch("urllib.request.urlopen", return_value=_mock_pypi_response()):
        results = scan_maintainers(["pkg-a", "pkg-b"])
    assert len(results) == 2
    assert all(isinstance(r, PackageMaintainerInfo) for r in results)


def test_fetch_maintainer_uses_version_url():
    captured = []
    original = __import__("urllib.request", fromlist=["urlopen"]).urlopen

    def capturing_open(url, timeout=10):
        captured.append(url)
        return _mock_pypi_response()

    with patch("urllib.request.urlopen", side_effect=capturing_open):
        fetch_maintainer("somelib", "2.0.0")
    assert "2.0.0" in captured[0]
