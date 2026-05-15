"""Fetch and evaluate package popularity metrics from PyPI stats."""
from __future__ import annotations

import urllib.request
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class PackagePopularityInfo:
    name: str
    monthly_downloads: Optional[int]
    is_low_popularity: bool
    threshold: int


def _fetch_pypistats(package_name: str) -> Optional[dict]:
    """Fetch monthly download stats from pypistats.org."""
    url = f"https://pypistats.org/api/packages/{package_name.lower()}/recent"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_popularity(package_name: str, low_threshold: int = 1000) -> PackagePopularityInfo:
    """Return popularity info for *package_name*.

    A package is considered low-popularity when its monthly downloads are
    below *low_threshold* (default 1 000).
    """
    data = _fetch_pypistats(package_name)
    monthly: Optional[int] = None
    if data and isinstance(data.get("data"), dict):
        monthly = data["data"].get("last_month")

    is_low = (monthly is not None) and (monthly < low_threshold)
    return PackagePopularityInfo(
        name=package_name,
        monthly_downloads=monthly,
        is_low_popularity=is_low,
        threshold=low_threshold,
    )


def scan_popularity(package_names: list[str], low_threshold: int = 1000) -> list[PackagePopularityInfo]:
    """Return popularity info for each package in *package_names*."""
    return [fetch_popularity(name, low_threshold) for name in package_names]
