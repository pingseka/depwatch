"""Render duplicate-package reports as text or JSON."""
from __future__ import annotations

import json
from typing import List

from depwatch.package_duplicates import DuplicateReport


def render_text(report: DuplicateReport) -> str:
    lines: List[str] = []
    lines.append(f"Duplicate/Conflict scan: {report.path}")
    lines.append(
        f"  Found {len(report.duplicates)} issue(s) "
        f"({report.conflict_count} conflict(s), {report.duplicate_count} exact duplicate(s))"
    )
    if not report.has_issues:
        lines.append("  No duplicate packages detected.")
        return "\n".join(lines)

    lines.append("")
    for entry in report.duplicates:
        lines.append(f"  {entry.description}")

    return "\n".join(lines)


def render_json(report: DuplicateReport) -> str:
    data = {
        "path": report.path,
        "has_issues": report.has_issues,
        "conflict_count": report.conflict_count,
        "duplicate_count": report.duplicate_count,
        "duplicates": [
            {
                "name": e.name,
                "is_conflicting": e.is_conflicting,
                "versions": e.versions,
                "lines": e.lines,
            }
            for e in report.duplicates
        ],
    }
    return json.dumps(data, indent=2)


def has_duplicate_violations(report: DuplicateReport) -> bool:
    """Return True if any conflicting (non-identical duplicate) entries exist."""
    return report.conflict_count > 0
