"""Trend analysis: compare history entries to detect worsening or improving dependency health."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from depwatch.history import load_history


@dataclass
class TrendPoint:
    timestamp: str
    outdated_count: int
    vulnerable_count: int


@dataclass
class TrendReport:
    points: List[TrendPoint]
    outdated_delta: Optional[int]   # latest - previous, None if < 2 points
    vulnerable_delta: Optional[int]

    @property
    def is_worsening(self) -> bool:
        """True if either outdated or vulnerable count increased."""
        if self.outdated_delta is None or self.vulnerable_delta is None:
            return False
        return self.outdated_delta > 0 or self.vulnerable_delta > 0

    @property
    def is_improving(self) -> bool:
        """True if both counts decreased or stayed the same, with at least one decrease."""
        if self.outdated_delta is None or self.vulnerable_delta is None:
            return False
        return (
            self.outdated_delta <= 0
            and self.vulnerable_delta <= 0
            and (self.outdated_delta < 0 or self.vulnerable_delta < 0)
        )


def build_trend(dep_file: str, history_dir: str = ".depwatch", limit: int = 10) -> TrendReport:
    """Load recent history for *dep_file* and build a TrendReport."""
    entries = load_history(dep_file, history_dir=history_dir)
    recent = entries[-limit:] if len(entries) > limit else entries

    points: List[TrendPoint] = [
        TrendPoint(
            timestamp=e["timestamp"],
            outdated_count=e.get("outdated_count", 0),
            vulnerable_count=e.get("vulnerable_count", 0),
        )
        for e in recent
    ]

    if len(points) >= 2:
        prev, latest = points[-2], points[-1]
        outdated_delta = latest.outdated_count - prev.outdated_count
        vulnerable_delta = latest.vulnerable_count - prev.vulnerable_count
    else:
        outdated_delta = None
        vulnerable_delta = None

    return TrendReport(
        points=points,
        outdated_delta=outdated_delta,
        vulnerable_delta=vulnerable_delta,
    )


def render_trend_text(report: TrendReport) -> str:
    """Return a human-readable summary of the trend report."""
    lines = ["=== Dependency Trend ==="]
    if not report.points:
        lines.append("No history available.")
        return "\n".join(lines)

    for pt in report.points:
        lines.append(f"  {pt.timestamp}  outdated={pt.outdated_count}  vulnerable={pt.vulnerable_count}")

    if report.outdated_delta is not None:
        direction = "worsening" if report.is_worsening else ("improving" if report.is_improving else "stable")
        lines.append(
            f"\nTrend: {direction}  "
            f"(outdated Δ{report.outdated_delta:+d}, vulnerable Δ{report.vulnerable_delta:+d})"
        )
    else:
        lines.append("\nNot enough data to compute trend.")

    return "\n".join(lines)
