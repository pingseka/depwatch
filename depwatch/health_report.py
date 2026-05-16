"""Render package health reports as text or JSON."""
from __future__ import annotations

import json
from typing import List

from depwatch.package_health import PackageHealthReport


def render_text(reports: List[PackageHealthReport]) -> str:
    if not reports:
        return "No packages to report.\n"

    lines: List[str] = []
    healthy = sum(1 for r in reports if r.is_healthy)
    lines.append(f"Package Health Report — {len(reports)} packages, {healthy} healthy\n")
    lines.append("-" * 60)

    for r in reports:
        lines.append(r.summary)
        if r.warnings:
            for w in r.warnings:
                lines.append(f"  ! {w}")
        if r.age and r.age.release_date:
            lines.append(f"  age: {r.age.age_days} days since {r.age.release_date.date()}")
        if r.popularity:
            lines.append(f"  downloads: {r.popularity.monthly_downloads}/month")
        lines.append("")

    return "\n".join(lines)


def render_json(reports: List[PackageHealthReport]) -> str:
    def _serialise(r: PackageHealthReport) -> dict:
        return {
            "name": r.name,
            "version": r.version,
            "grade": r.score.grade,
            "score": r.score.total,
            "is_healthy": r.is_healthy,
            "warnings": r.warnings,
            "age_days": r.age.age_days if r.age else None,
            "is_stale": r.age.is_stale if r.age else None,
            "monthly_downloads": r.popularity.monthly_downloads if r.popularity else None,
            "is_deprecated": r.deprecation.is_deprecated if r.deprecation else None,
            "successor": r.deprecation.successor if r.deprecation else None,
        }

    return json.dumps([_serialise(r) for r in reports], indent=2)


def has_health_violations(reports: List[PackageHealthReport]) -> bool:
    return any(not r.is_healthy for r in reports)
