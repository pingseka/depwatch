"""Tests for depwatch.package_changelog."""
from __future__ import annotations

from unittest.mock import patch, MagicMock
import json
import io

import pytest

from depwatch.package_changelog import (
    fetch_changelog,
    scan_changelogs,
    PackageChangelogInfo,
    _extract_urls,
)


def _mock_pypi_response(info_overrides: dict) -> MagicMock:
    base_info = {
        "name": "requests",
        "version": "2.31.0",
        "home_page": "https://requests.readthedocs.io",
        "project_urls": {
            "Changelog": "https://github.com/psf/requests/blob/main/HISTORY.md",
            "Source": "https://github.com/psf/requests",
        },
    }
    base_info.update(info_overrides)
    payload = json.dumps({"info": base_info}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_fetch_changelog_found():
    mock_resp = _mock_pypi_response({})
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fetch_changelog("requests", "2.31.0")
    assert result.found is True
    assert result.name == "requests"
    assert result.version == "2.31.0"
    assert result.changelog_url == "https://github.com/psf/requests/blob/main/HISTORY.md"
    assert result.source_url == "https://github.com/psf/requests"
    assert result.home_page == "https://requests.readthedocs.io"


def test_fetch_changelog_no_changelog_url():
    mock_resp = _mock_pypi_response({"project_urls": {"Source": "https://github.com/x/y"}})
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fetch_changelog("mypkg")
    assert result.changelog_url is None
    assert result.source_url == "https://github.com/x/y"
    assert result.found is True


def test_fetch_changelog_network_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = fetch_changelog("brokenpkg", "1.0.0")
    assert result.found is False
    assert result.name == "brokenpkg"
    assert result.changelog_url is None


def test_fetch_changelog_no_version_uses_latest():
    mock_resp = _mock_pypi_response({"version": "3.0.0", "project_urls": {}})
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fetch_changelog("somepkg")
    assert result.version == "3.0.0"
    assert result.found is True


def test_extract_urls_release_notes_key():
    info = {"project_urls": {"Release Notes": "https://example.com/notes"}, "home_page": None}
    changelog, home, source = _extract_urls(info)
    assert changelog == "https://example.com/notes"


def test_extract_urls_missing_project_urls():
    info = {"home_page": "https://example.com"}
    changelog, home, source = _extract_urls(info)
    assert changelog is None
    assert home == "https://example.com"
    assert source is None


def test_scan_changelogs_returns_list():
    mock_resp = _mock_pypi_response({})
    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = scan_changelogs(["requests", "flask"])
    assert len(results) == 2
    assert all(isinstance(r, PackageChangelogInfo) for r in results)
