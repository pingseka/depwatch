"""Baseline management for depwatch.

Allows saving and comparing scan results against a known-good baseline,
so alerts are only raised for newly introduced issues.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

from depwatch.scanner import ScanResult, PackageInfo


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_baseline_path(dep_file: str) -> str:
    base = os.path.splitext(os.path.basename(dep_file))[0]
    return os.path.join(".depwatch", f"{base}.baseline.json")


def save_baseline(result: ScanResult, dep_file: str, path: Optional[str] = None) -> str:
    """Persist a ScanResult as the new baseline. Returns the path written."""
    path = path or _default_baseline_path(dep_file)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    packages = [
        {
            "name": p.name,
            "current_version": p.current_version,
            "latest_version": p.latest_version,
            "vulnerabilities": p.vulnerabilities,
        }
        for p in result.packages
    ]

    data = {
        "saved_at": _utcnow(),
        "dep_file": dep_file,
        "packages": packages,
    }

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    return path


def load_baseline(dep_file: str, path: Optional[str] = None) -> Optional[ScanResult]:
    """Load a previously saved baseline. Returns None if no baseline exists."""
    path = path or _default_baseline_path(dep_file)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    packages = [
        PackageInfo(
            name=p["name"],
            current_version=p["current_version"],
            latest_version=p["latest_version"],
            vulnerabilities=p.get("vulnerabilities", []),
        )
        for p in data.get("packages", [])
    ]
    return ScanResult(packages=packages)


def diff_against_baseline(current: ScanResult, baseline: ScanResult) -> ScanResult:
    """Return a ScanResult containing only packages new or worsened since baseline."""
    baseline_map = {p.name: p for p in baseline.packages}
    new_issues: list[PackageInfo] = []

    for pkg in current.packages:
        base_pkg = baseline_map.get(pkg.name)
        if base_pkg is None:
            new_issues.append(pkg)
            continue
        new_vulns = set(pkg.vulnerabilities) - set(base_pkg.vulnerabilities)
        became_outdated = pkg.is_outdated and not base_pkg.is_outdated
        if new_vulns or became_outdated:
            new_issues.append(PackageInfo(
                name=pkg.name,
                current_version=pkg.current_version,
                latest_version=pkg.latest_version,
                vulnerabilities=list(new_vulns),
            ))

    return ScanResult(packages=new_issues)
