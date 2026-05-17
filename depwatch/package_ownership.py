"""Fetch and analyse PyPI package ownership / maintainer-count information."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import List, Optional

import requests

_PYPI_URL = "https://pypi.org/pypi/{package}/json"
_SINGLE_MAINTAINER_THRESHOLD = 1


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


@dataclass
class PackageOwnershipInfo:
    package: str
    maintainers: List[str] = field(default_factory=list)
    maintainer_count: int = 0
    sole_maintainer: bool = False
    error: Optional[str] = None


def _pypi_url(package: str) -> str:
    return _PYPI_URL.format(package=package)


def fetch_ownership(package: str, timeout: int = 10) -> PackageOwnershipInfo:
    """Fetch maintainer list for *package* from PyPI."""
    try:
        resp = requests.get(_pypi_url(package), timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        info = data.get("info", {})
        # PyPI exposes a single 'maintainer' field (comma-separated) and 'author'.
        raw = info.get("maintainer") or info.get("author") or ""
        maintainers = [m.strip() for m in raw.split(",") if m.strip()]
        count = len(maintainers)
        return PackageOwnershipInfo(
            package=package,
            maintainers=maintainers,
            maintainer_count=count,
            sole_maintainer=count <= _SINGLE_MAINTAINER_THRESHOLD,
        )
    except requests.RequestException as exc:
        return PackageOwnershipInfo(package=package, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return PackageOwnershipInfo(package=package, error=f"unexpected: {exc}")


def scan_ownership(packages: List[str]) -> List[PackageOwnershipInfo]:
    """Fetch ownership info for every package in *packages*."""
    return [fetch_ownership(p) for p in packages]
