"""Package freshness checker — flags packages that have not been updated
for longer than a configurable number of days."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import List, Optional

import requests

DEFAULT_STALE_DAYS = 365
_PYPI_URL = "https://pypi.org/pypi/{name}/json"


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


@dataclass
class PackageFreshnessInfo:
    name: str
    version: str
    latest_release_date: Optional[datetime.datetime]
    days_since_release: Optional[int]
    is_stale: bool
    error: Optional[str] = None


def fetch_freshness(
    name: str,
    version: Optional[str] = None,
    stale_days: int = DEFAULT_STALE_DAYS,
) -> PackageFreshnessInfo:
    """Fetch the release date of *version* (or latest) from PyPI and decide
    whether the package is stale."""
    url = _PYPI_URL.format(name=name)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return PackageFreshnessInfo(
            name=name,
            version=version or "unknown",
            latest_release_date=None,
            days_since_release=None,
            is_stale=False,
            error=str(exc),
        )

    target_version = version or data.get("info", {}).get("version", "")
    releases = data.get("releases", {})
    release_files = releases.get(target_version, [])

    release_date: Optional[datetime.datetime] = None
    for f in release_files:
        upload_time = f.get("upload_time")
        if upload_time:
            try:
                release_date = datetime.datetime.fromisoformat(upload_time)
                break
            except ValueError:
                continue

    if release_date is None:
        return PackageFreshnessInfo(
            name=name,
            version=target_version,
            latest_release_date=None,
            days_since_release=None,
            is_stale=False,
            error="release date unavailable",
        )

    days = (_utcnow() - release_date).days
    return PackageFreshnessInfo(
        name=name,
        version=target_version,
        latest_release_date=release_date,
        days_since_release=days,
        is_stale=days >= stale_days,
    )


def scan_freshness(
    packages: List[str],
    stale_days: int = DEFAULT_STALE_DAYS,
) -> List[PackageFreshnessInfo]:
    """Check freshness for a list of package names."""
    return [fetch_freshness(pkg, stale_days=stale_days) for pkg in packages]
