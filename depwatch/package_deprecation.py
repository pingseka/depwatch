"""Fetch and report deprecation status for PyPI packages."""
from __future__ import annotations

import requests
from dataclasses import dataclass, field
from typing import List, Optional

PYPI_URL = "https://pypi.org/pypi/{name}/json"
_TIMEOUT = 10


@dataclass
class PackageDeprecationInfo:
    name: str
    version: str
    is_deprecated: bool
    deprecation_message: Optional[str] = None
    successor: Optional[str] = None


def _pypi_url(name: str) -> str:
    return PYPI_URL.format(name=name)


def _extract_deprecation(info: dict) -> tuple[bool, Optional[str], Optional[str]]:
    """Return (is_deprecated, message, successor) from PyPI info dict."""
    classifiers: List[str] = info.get("info", {}).get("classifiers", [])
    for clf in classifiers:
        if "Development Status" in clf and "Inactive" in clf:
            return True, "Marked as Inactive via trove classifier", None

    description: str = info.get("info", {}).get("description", "") or ""
    summary: str = info.get("info", {}).get("summary", "") or ""
    combined = (summary + " " + description[:500]).lower()

    successor: Optional[str] = None
    deprecated = False
    message: Optional[str] = None

    if "deprecated" in combined or "no longer maintained" in combined:
        deprecated = True
        message = summary if summary else "Package description mentions deprecation"
        # Naive successor extraction: look for "use <pkg>" or "replaced by <pkg>"
        import re
        m = re.search(r"(?:use|replaced by|successor[:\s]+)\s+([\w\-]+)", combined)
        if m:
            successor = m.group(1)

    return deprecated, message, successor


def fetch_deprecation(name: str, version: Optional[str] = None) -> PackageDeprecationInfo:
    """Fetch deprecation info for a single package from PyPI."""
    try:
        resp = requests.get(_pypi_url(name), timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return PackageDeprecationInfo(
            name=name,
            version=version or "unknown",
            is_deprecated=False,
            deprecation_message=None,
        )

    resolved_version = version or data.get("info", {}).get("version", "unknown")
    deprecated, message, successor = _extract_deprecation(data)
    return PackageDeprecationInfo(
        name=name,
        version=resolved_version,
        is_deprecated=deprecated,
        deprecation_message=message,
        successor=successor,
    )


def scan_deprecations(packages: List[str], versions: Optional[dict] = None) -> List[PackageDeprecationInfo]:
    """Fetch deprecation info for a list of package names."""
    versions = versions or {}
    return [fetch_deprecation(pkg, versions.get(pkg)) for pkg in packages]
