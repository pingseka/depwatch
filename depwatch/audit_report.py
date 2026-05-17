"""Render audit trail entries as text or JSON."""
from __future__ import annotations

import json
from typing import List

from depwatch.package_audit_trail import AuditEntry


def render_text(entries: List[AuditEntry]) -> str:
    if not entries:
        return "No audit entries found.\n"
    lines = ["Audit Trail", "=" * 60]
    for e in entries:
        alert_flag = " [ALERT]" if e.triggered_alert else ""
        lines.append(
            f"{e.timestamp}  {e.dep_file}{alert_flag}\n"
            f"  packages={e.total_packages}  "
            f"outdated={e.outdated_count}  "
            f"vulnerable={e.vulnerable_count}"
            + (f"  notes={e.notes}" if e.notes else "")
        )
    lines.append("")
    return "\n".join(lines)


def render_json(entries: List[AuditEntry]) -> str:
    from dataclasses import asdict

    return json.dumps([asdict(e) for e in entries], indent=2)


def has_alerts(entries: List[AuditEntry]) -> bool:
    """Return True if any entry recorded a triggered alert."""
    return any(e.triggered_alert for e in entries)


def summary_stats(entries: List[AuditEntry]) -> dict:
    """Return aggregate statistics across all entries."""
    if not entries:
        return {"total_scans": 0, "total_alerts": 0, "avg_outdated": 0.0, "avg_vulnerable": 0.0}
    total_alerts = sum(1 for e in entries if e.triggered_alert)
    avg_outdated = sum(e.outdated_count for e in entries) / len(entries)
    avg_vulnerable = sum(e.vulnerable_count for e in entries) / len(entries)
    return {
        "total_scans": len(entries),
        "total_alerts": total_alerts,
        "avg_outdated": round(avg_outdated, 2),
        "avg_vulnerable": round(avg_vulnerable, 2),
    }
