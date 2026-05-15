"""Utilities for checking how old a package version is based on release date."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import urllib.request
import json


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PackageAgeInfo:
    name: str
    version: str
    release_date: Optional[datetime]
    age_days: Optional[int]
    is_stale: bool


def fetch_release_date(package_name: str, version: str) -> Optional[datetime]:
    """Query PyPI JSON API for the release date of a specific package version."""
    url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        # Release files list; grab the upload_time of the first file
        files = data.get("urls", [])
        if not files:
            return None
        upload_time = files[0].get("upload_time_iso_8601") or files[0].get("upload_time")
        if not upload_time:
            return None
        # Normalise: PyPI uses '+00:00' or no tz suffix
        if upload_time.endswith("Z"):
            upload_time = upload_time[:-1] + "+00:00"
        elif "+" not in upload_time and upload_time.count("-") < 3:
            upload_time += "+00:00"
        return datetime.fromisoformat(upload_time)
    except Exception:
        return None


def package_age_info(
    package_name: str,
    version: str,
    stale_days: int = 365,
    _now: Optional[datetime] = None,
    _release_date: Optional[datetime] = None,
) -> PackageAgeInfo:
    """Return age information for a package version.

    Parameters
    ----------
    package_name:   PyPI package name.
    version:        Installed version string.
    stale_days:     Number of days after which a version is considered stale.
    _now:           Override current time (testing).
    _release_date:  Override fetched release date (testing).
    """
    now = _now or _utcnow()
    release_date = _release_date if _release_date is not None else fetch_release_date(package_name, version)

    if release_date is None:
        return PackageAgeInfo(
            name=package_name,
            version=version,
            release_date=None,
            age_days=None,
            is_stale=False,
        )

    if release_date.tzinfo is None:
        release_date = release_date.replace(tzinfo=timezone.utc)

    age_days = (now - release_date).days
    return PackageAgeInfo(
        name=package_name,
        version=version,
        release_date=release_date,
        age_days=age_days,
        is_stale=age_days >= stale_days,
    )
