"""Fetch and report the distribution size of PyPI packages."""
from __future__ import annotations

import urllib.request
import urllib.error
import json
from dataclasses import dataclass, field
from typing import List, Optional

# Default threshold in bytes (10 MB)
DEFAULT_SIZE_THRESHOLD = 10 * 1024 * 1024


@dataclass
class PackageSizeInfo:
    name: str
    version: str
    size_bytes: Optional[int]  # None when unavailable
    threshold_bytes: int = DEFAULT_SIZE_THRESHOLD
    error: Optional[str] = None

    @property
    def is_large(self) -> bool:
        """Return True when the package exceeds the size threshold."""
        if self.size_bytes is None:
            return False
        return self.size_bytes > self.threshold_bytes

    @property
    def size_kb(self) -> Optional[float]:
        if self.size_bytes is None:
            return None
        return round(self.size_bytes / 1024, 1)


def _pypi_url(name: str, version: Optional[str] = None) -> str:
    if version:
        return f"https://pypi.org/pypi/{name}/{version}/json"
    return f"https://pypi.org/pypi/{name}/json"


def _total_size(urls: list) -> Optional[int]:
    """Sum the sizes of all distribution files for a release."""
    total = 0
    for entry in urls:
        size = entry.get("size")
        if size is None:
            return None
        total += size
    return total


def fetch_size(
    name: str,
    version: Optional[str] = None,
    threshold_bytes: int = DEFAULT_SIZE_THRESHOLD,
) -> PackageSizeInfo:
    url = _pypi_url(name, version)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        resolved_version = data["info"]["version"]
        urls = data.get("urls") or []
        size = _total_size(urls)
        return PackageSizeInfo(
            name=name,
            version=resolved_version,
            size_bytes=size,
            threshold_bytes=threshold_bytes,
        )
    except urllib.error.URLError as exc:
        return PackageSizeInfo(
            name=name,
            version=version or "unknown",
            size_bytes=None,
            threshold_bytes=threshold_bytes,
            error=str(exc),
        )
    except Exception as exc:  # noqa: BLE001
        return PackageSizeInfo(
            name=name,
            version=version or "unknown",
            size_bytes=None,
            threshold_bytes=threshold_bytes,
            error=f"unexpected error: {exc}",
        )


def scan_sizes(
    packages: List[str],
    threshold_bytes: int = DEFAULT_SIZE_THRESHOLD,
) -> List[PackageSizeInfo]:
    return [fetch_size(pkg, threshold_bytes=threshold_bytes) for pkg in packages]
