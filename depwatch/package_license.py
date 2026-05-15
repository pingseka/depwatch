"""Fetch and evaluate license information for packages via PyPI JSON API."""

from __future__ import annotations

import urllib.request
import urllib.error
import json
from dataclasses import dataclass, field
from typing import Optional, List

# Licenses considered permissive / safe for most projects
_PERMISSIVE = {
    "mit", "apache-2.0", "apache 2.0", "bsd", "bsd-2-clause", "bsd-3-clause",
    "isc", "unlicense", "public domain", "cc0",
}

# Licenses that trigger a warning (copyleft)
_COPYLEFT = {
    "gpl", "gpl-2.0", "gpl-3.0", "lgpl", "lgpl-2.1", "lgpl-3.0",
    "agpl", "agpl-3.0", "mpl-2.0", "eupl",
}


@dataclass
class PackageLicenseInfo:
    name: str
    version: str
    license: Optional[str] = None
    is_permissive: bool = False
    is_copyleft: bool = False
    is_unknown: bool = True


def _normalize(lic: str) -> str:
    return lic.lower().strip()


def fetch_license(package: str, version: Optional[str] = None) -> PackageLicenseInfo:
    """Fetch license metadata from PyPI for *package* (optionally pinned to *version*)."""
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        ver = version or "unknown"
        return PackageLicenseInfo(name=package, version=ver, is_unknown=True)

    info = data.get("info", {})
    resolved_version = version or info.get("version", "unknown")
    raw_license: str = info.get("license") or ""
    norm = _normalize(raw_license)

    permissive = any(p in norm for p in _PERMISSIVE)
    copyleft = any(c in norm for c in _COPYLEFT)
    unknown = not raw_license or (not permissive and not copyleft)

    return PackageLicenseInfo(
        name=package,
        version=resolved_version,
        license=raw_license or None,
        is_permissive=permissive,
        is_copyleft=copyleft,
        is_unknown=unknown,
    )


def scan_licenses(packages: List[str]) -> List[PackageLicenseInfo]:
    """Return license info for each package name in *packages*."""
    return [fetch_license(pkg) for pkg in packages]
