"""Fetch and summarise changelog / release-note URLs for PyPI packages."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import urllib.request
import urllib.error
import json


@dataclass
class PackageChangelogInfo:
    name: str
    version: str
    changelog_url: Optional[str] = None
    home_page: Optional[str] = None
    source_url: Optional[str] = None
    found: bool = False


def _pypi_url(name: str, version: Optional[str] = None) -> str:
    if version:
        return f"https://pypi.org/pypi/{name}/{version}/json"
    return f"https://pypi.org/pypi/{name}/json"


def _extract_urls(info: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (changelog_url, home_page, source_url) from PyPI info dict."""
    project_urls: dict = info.get("project_urls") or {}
    changelog_url = (
        project_urls.get("Changelog")
        or project_urls.get("CHANGELOG")
        or project_urls.get("Changes")
        or project_urls.get("Release Notes")
    )
    home_page = info.get("home_page") or project_urls.get("Homepage")
    source_url = (
        project_urls.get("Source")
        or project_urls.get("Source Code")
        or project_urls.get("Repository")
    )
    return changelog_url, home_page, source_url


def fetch_changelog(name: str, version: Optional[str] = None) -> PackageChangelogInfo:
    """Query PyPI and return changelog-related URLs for *name*."""
    url = _pypi_url(name, version)
    resolved_version = version or "latest"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return PackageChangelogInfo(name=name, version=resolved_version or "unknown")

    info = data.get("info", {})
    resolved_version = info.get("version", version or "unknown")
    changelog_url, home_page, source_url = _extract_urls(info)
    return PackageChangelogInfo(
        name=name,
        version=resolved_version,
        changelog_url=changelog_url,
        home_page=home_page,
        source_url=source_url,
        found=True,
    )


def scan_changelogs(names: list[str]) -> list[PackageChangelogInfo]:
    """Fetch changelog info for a list of package names."""
    return [fetch_changelog(name) for name in names]
