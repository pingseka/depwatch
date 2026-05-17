"""Render complexity reports as text or JSON."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from depwatch.package_complexity import ComplexityInfo, ComplexityReport


def _serialise(info: ComplexityInfo) -> Dict[str, Any]:
    return {
        "package": info.package,
        "direct_deps": info.direct_deps,
        "transitive_deps": info.transitive_deps,
        "total_deps": info.total_deps,
        "max_depth": info.max_depth,
        "is_complex": info.is_complex,
        "error": info.error,
    }


def render_text(report: ComplexityReport) -> str:
    lines: List[str] = []
    lines.append(f"Complexity Report  ({len(report.packages)} package(s) analysed)")
    lines.append("-" * 56)
    for info in report.packages:
        flag = " [COMPLEX]" if info.is_complex else ""
        err = f"  error={info.error}" if info.error else ""
        lines.append(
            f"  {info.package:<30} direct={info.direct_deps:>3}  "
            f"transitive={info.transitive_deps:>4}  depth={info.max_depth:>2}"
            f"{flag}{err}"
        )
    lines.append("")
    if report.has_complex:
        lines.append(f"WARNING: {len(report.complex_packages)} complex package(s) detected.")
    else:
        lines.append("All packages within acceptable complexity bounds.")
    return "\n".join(lines)


def render_json(report: ComplexityReport) -> str:
    return json.dumps(
        {
            "total": len(report.packages),
            "complex_count": len(report.complex_packages),
            "packages": [_serialise(p) for p in report.packages],
        },
        indent=2,
    )


def has_complexity_violations(report: ComplexityReport) -> bool:
    return report.has_complex
