"""Render popularity scan results as text or JSON."""
from __future__ import annotations

import json
from typing import List

from depwatch.package_popularity import PackagePopularityInfo


def render_text(infos: List[PackagePopularityInfo]) -> str:
    lines: list[str] = ["Package Popularity Report", "=" * 30]
    low = [i for i in infos if i.is_low_popularity]
    ok = [i for i in infos if not i.is_low_popularity]

    if low:
        lines.append(f"\nLow popularity ({len(low)} package(s)):")
        for info in low:
            dl = info.monthly_downloads if info.monthly_downloads is not None else "N/A"
            lines.append(f"  - {info.name}: {dl} downloads/month (threshold: {info.threshold})")
    else:
        lines.append("\nNo low-popularity packages detected.")

    if ok:
        lines.append(f"\nHealthy popularity ({len(ok)} package(s)):")
        for info in ok:
            dl = info.monthly_downloads if info.monthly_downloads is not None else "N/A"
            lines.append(f"  - {info.name}: {dl} downloads/month")

    lines.append("")
    return "\n".join(lines)


def render_json(infos: List[PackagePopularityInfo]) -> str:
    records = [
        {
            "name": i.name,
            "monthly_downloads": i.monthly_downloads,
            "is_low_popularity": i.is_low_popularity,
            "threshold": i.threshold,
        }
        for i in infos
    ]
    return json.dumps({"popularity": records}, indent=2)


def has_low_popularity(infos: List[PackagePopularityInfo]) -> bool:
    """Return True if any package is flagged as low popularity."""
    return any(i.is_low_popularity for i in infos)
