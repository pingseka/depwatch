"""Fetch and evaluate package maintainer/ownership health from PyPI."""
from __future__ import annotations

import urllib.request
import urllib.error
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PackageMaintainerInfo:
    name: str
    version: str
    maintainers: List[str] = field(default_factory=list)
    author: Optional[str] = None
    author_email: Optional[str] = None
    is_abandoned: bool = False   # heuristic: zero maintainers listed
    warning: Optional[str] = None


def _pypi_url(package: str, version: Optional[str] = None) -> str:
    if version:
        return f"https://pypi.org/pypi/{package}/{version}/json"
    return f"https://pypi.org/pypi/{package}/json"


def fetch_maintainer(package: str, version: Optional[str] = None) -> PackageMaintainerInfo:
    """Fetch maintainer metadata for *package* from PyPI."""
    url = _pypi_url(package, version)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        return PackageMaintainerInfo(
            name=package,
            version=version or "unknown",
            warning=f"network error: {exc}",
        )
    except Exception as exc:  # noqa: BLE001
        return PackageMaintainerInfo(
            name=package,
            version=version or "unknown",
            warning=f"unexpected error: {exc}",
        )

    info = data.get("info", {})
    resolved_version = info.get("version", version or "unknown")
    maintainers = [
        m.get("username", "") for m in data.get("urls", [])
        if isinstance(m, dict) and m.get("username")
    ]
    # PyPI JSON does not expose maintainer list directly; use author field
    author = info.get("author") or None
    author_email = info.get("author_email") or None
    is_abandoned = not author and not maintainers

    return PackageMaintainerInfo(
        name=package,
        version=resolved_version,
        maintainers=maintainers,
        author=author,
        author_email=author_email,
        is_abandoned=is_abandoned,
    )


def scan_maintainers(packages: List[str]) -> List[PackageMaintainerInfo]:
    """Fetch maintainer info for a list of package names."""
    return [fetch_maintainer(pkg) for pkg in packages]
