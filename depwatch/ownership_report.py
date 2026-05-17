"""Render ownership scan results as text or JSON."""
from __future__ import annotations

import json
from typing import List

from depwatch.package_ownership import PackageOwnershipInfo


def render_text(results: List[PackageOwnershipInfo]) -> str:
    lines: List[str] = ["Package Ownership Report", "=" * 40]
    for r in results:
        if r.error:
            lines.append(f"  {r.package}: ERROR – {r.error}")
            continue
        tag = "[SOLE MAINTAINER]" if r.sole_maintainer else "[OK]"
        names = ", ".join(r.maintainers) if r.maintainers else "unknown"
        lines.append(f"  {r.package}: {tag} maintainers={r.maintainer_count} ({names})")
    sole = sum(1 for r in results if r.sole_maintainer and not r.error)
    lines.append("=" * 40)
    lines.append(f"Total: {len(results)} packages, {sole} with sole maintainer")
    return "\n".join(lines)


def _serialise(r: PackageOwnershipInfo) -> dict:
    return {
        "package": r.package,
        "maintainers": r.maintainers,
        "maintainer_count": r.maintainer_count,
        "sole_maintainer": r.sole_maintainer,
        "error": r.error,
    }


def render_json(results: List[PackageOwnershipInfo]) -> str:
    return json.dumps([_serialise(r) for r in results], indent=2)


def has_ownership_violations(results: List[PackageOwnershipInfo]) -> bool:
    """Return True if any package has a sole maintainer (risk signal)."""
    return any(r.sole_maintainer and not r.error for r in results)
