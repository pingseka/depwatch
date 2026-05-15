"""Render PinningReport objects as text or JSON."""

from __future__ import annotations

import json
from typing import List

from depwatch.package_pinning import PinningReport


def render_text(report: PinningReport) -> str:
    lines: List[str] = []
    lines.append(f"Pinning report for: {report.path}")
    if not report.has_issues:
        lines.append("  All packages are exactly pinned. ✓")
        return "\n".join(lines)
    lines.append(f"  Unpinned : {len(report.unpinned)}")
    lines.append(f"  Loose    : {len(report.loose)}")
    lines.append("")
    for issue in report.issues:
        tag = "[UNPINNED]" if issue.kind == "unpinned" else "[LOOSE]   "
        lines.append(f"  {tag} {issue.description}")
    return "\n".join(lines)


def render_json(report: PinningReport) -> str:
    data = {
        "path": report.path,
        "total_issues": len(report.issues),
        "unpinned": len(report.unpinned),
        "loose": len(report.loose),
        "issues": [
            {"package": i.package, "specifier": i.specifier, "kind": i.kind}
            for i in report.issues
        ],
    }
    return json.dumps(data, indent=2)


def has_pinning_violations(report: PinningReport) -> bool:
    """Return True if there are any unpinned or loosely-pinned packages."""
    return report.has_issues
