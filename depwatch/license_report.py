"""Render license scan results as text or JSON."""

from __future__ import annotations

import json
from typing import List

from depwatch.package_license import PackageLicenseInfo


def render_text(results: List[PackageLicenseInfo]) -> str:
    lines: List[str] = ["License Report", "=" * 40]
    for r in results:
        tag = "permissive" if r.is_permissive else ("copyleft" if r.is_copyleft else "unknown")
        lic_str = r.license or "(none)"
        lines.append(f"  {r.name}=={r.version}  [{tag}]  {lic_str}")

    total = len(results)
    copyleft = sum(1 for r in results if r.is_copyleft)
    unknown = sum(1 for r in results if r.is_unknown)
    lines.append("=" * 40)
    lines.append(f"Total: {total}  Copyleft: {copyleft}  Unknown: {unknown}")
    return "\n".join(lines)


def render_json(results: List[PackageLicenseInfo]) -> str:
    payload = [
        {
            "name": r.name,
            "version": r.version,
            "license": r.license,
            "is_permissive": r.is_permissive,
            "is_copyleft": r.is_copyleft,
            "is_unknown": r.is_unknown,
        }
        for r in results
    ]
    return json.dumps(payload, indent=2)


def has_policy_violations(
    results: List[PackageLicenseInfo],
    allow_copyleft: bool = False,
    allow_unknown: bool = True,
) -> bool:
    """Return True if any result violates the given policy."""
    for r in results:
        if r.is_copyleft and not allow_copyleft:
            return True
        if r.is_unknown and not allow_unknown:
            return True
    return False
