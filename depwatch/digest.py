"""Digest module: generate and compare scan digests for change detection."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

from depwatch.scanner import ScanResult


def _package_fingerprint(pkg_dict: Dict[str, Any]) -> str:
    """Return a stable string fingerprint for a single package dict."""
    key = f"{pkg_dict['name']}:{pkg_dict['current']}:{pkg_dict['latest']}:{','.join(sorted(pkg_dict.get('vuln_ids', [])))}"
    return key


def compute_digest(result: ScanResult) -> str:
    """Compute a SHA-256 digest that uniquely represents the scan result.

    The digest is deterministic: same packages in any order produce the
    same digest, so it can be used to detect meaningful changes between
    successive scans.
    """
    entries = []
    for pkg in result.packages:
        entries.append(
            _package_fingerprint(
                {
                    "name": pkg.name,
                    "current": pkg.current_version,
                    "latest": pkg.latest_version,
                    "vuln_ids": pkg.vuln_ids,
                }
            )
        )
    # Sort so order does not matter
    entries.sort()
    payload = "\n".join(entries)
    return hashlib.sha256(payload.encode()).hexdigest()


def digests_differ(digest_a: Optional[str], digest_b: Optional[str]) -> bool:
    """Return True when the two digests represent different scan states."""
    if digest_a is None or digest_b is None:
        return True
    return digest_a != digest_b


def digest_summary(result: ScanResult, digest: str) -> Dict[str, Any]:
    """Return a small dict suitable for logging or storing alongside a result."""
    return {
        "digest": digest,
        "total": len(result.packages),
        "outdated": len(result.outdated),
        "vulnerable": len(result.vulnerable),
    }
